"""
app/ai_assistant/services/bedrock_client.py
────────────────────────────────────────────
AWS Bedrock Nova integration with:
  - Per-model token-bucket rate limiting (50 RPM each)
  - Exponential backoff with jitter (max 5 retries)
  - 30-second request timeout
  - Automatic task → model routing
  - Local keyword-based fallback when AI_PROVIDER != "bedrock"
"""

import json
import logging
import random
import os
import time
import threading
from dataclasses import dataclass, field
from typing import Any, Optional

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# ── Task routing ──────────────────────────────────────────────────────────────
# Nova Lite: reasoning-heavy tasks
# Nova Micro: fast / cheap tasks
_NOVA_LITE_TASKS = {
    "chat",
    "budget_planning",
    "financial_advice",
    "transaction_analysis",
    "mpesa_assistance",
    "payment_recommendations",
    "insight",
    "score_coaching",
}
_NOVA_MICRO_TASKS = {"spending_category"}


# ── Token-bucket rate limiter ─────────────────────────────────────────────────

class _TokenBucket:
    """Thread-safe token-bucket rate limiter (capacity = RPM)."""

    def __init__(self, rate: int = 50) -> None:
        self._rate = rate           # tokens added per 60 s
        self._capacity = rate
        self._tokens = float(rate)
        self._last_refill = time.monotonic()
        self._lock = threading.Lock()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        added = elapsed * (self._rate / 60.0)
        self._tokens = min(self._capacity, self._tokens + added)
        self._last_refill = now

    def acquire(self) -> bool:
        """Attempt to consume one token. Returns True if successful."""
        with self._lock:
            self._refill()
            if self._tokens >= 1:
                self._tokens -= 1
                return True
            return False

    def wait_and_acquire(self, timeout: float = 30.0) -> bool:
        """Block until a token is available or timeout is reached."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.acquire():
                return True
            time.sleep(0.1)
        return False


_lite_bucket = _TokenBucket(rate=50)
_micro_bucket = _TokenBucket(rate=50)


# ── Response dataclass ────────────────────────────────────────────────────────

@dataclass
class BedrockResponse:
    content: str
    model_used: str
    input_tokens: int = 0
    output_tokens: int = 0
    is_fallback: bool = False


# ── System prompt ─────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """You are Mula, an intelligent AI financial coach built for East African users.
You help with budgeting, financial planning, savings goals, and understanding Mula Scores.

Key rules:
- Always be warm, practical, and encouraging.
- Use KES (Kenyan Shilling) by default unless the user specifies another currency.
- For score_coaching tasks: ONLY narrate and explain score changes. NEVER calculate or invent scores.
- For budget_planning tasks: Follow the 5-step flow (Income → Fixed → Variable → Savings → Plan).
- Keep advice actionable and grounded in the user's actual data.
- Cite specific numbers when they are provided; don't fabricate figures."""


# ── Local fallback responses ───────────────────────────────────────────────────

_FALLBACK_RESPONSES: dict[str, str] = {
    "budget_planning": (
        "Let's build your budget together! Start by telling me your monthly take-home income "
        "and I'll calculate your 50/30/20 targets."
    ),
    "financial_advice": (
        "Great question! Building an emergency fund covering 3–6 months of expenses is a solid "
        "first step. Would you like to start there?"
    ),
    "score_coaching": (
        "Your Mula Score reflects your payment consistency, savings behaviour, and spending "
        "discipline. Keep making consistent payments and hitting your savings targets to improve it."
    ),
    "spending_category": "miscellaneous",
    "transaction_analysis": (
        "I've reviewed your recent transactions. Your biggest spending category appears to be "
        "food and utilities — consider setting a budget cap to improve your score."
    ),
    "insight": (
        "Tip: Paying bills a few days early can add 4–8 points to your Mula Score each time."
    ),
    "chat": (
        "Hello! I'm Mula, your AI financial coach. How can I help you today? "
        "You can ask me about budgeting, savings, or your Mula Score."
    ),
}


def _fallback_response(task_type: str, user_message: str) -> BedrockResponse:
    content = _FALLBACK_RESPONSES.get(task_type, _FALLBACK_RESPONSES["chat"])
    return BedrockResponse(content=content, model_used="local_fallback", is_fallback=True)


# ── Bedrock client ────────────────────────────────────────────────────────────

class BedrockClient:
    """
    Wraps AWS Bedrock Converse API for Nova Lite and Nova Micro.

    Instantiated once and reused (thread-safe after __init__).
    """

    _MAX_RETRIES = 5
    _BASE_BACKOFF = 1.0   # seconds

    def __init__(self) -> None:
        self._enabled = settings.ai_provider.lower() == "bedrock"
        if self._enabled:
            client_options = {
                "region_name": settings.bedrock_region,
                "config": Config(read_timeout=30, connect_timeout=10),
            }
            if settings.aws_bearer_token_bedrock:
                # Boto3 reads Bedrock bearer credentials from this environment
                # variable; Settings also loads it from backend/.env.
                os.environ["AWS_BEARER_TOKEN_BEDROCK"] = settings.aws_bearer_token_bedrock
            else:
                client_options["aws_access_key_id"] = settings.aws_access_key_id or None
                client_options["aws_secret_access_key"] = settings.aws_secret_access_key or None
            self._client = boto3.client("bedrock-runtime", **client_options)

    def _model_id(self, task_type: str) -> str:
        if task_type in _NOVA_MICRO_TASKS:
            return settings.bedrock_nova_micro_model_id
        return settings.bedrock_nova_lite_model_id

    def _model_name(self, task_type: str) -> str:
        return "nova_micro" if task_type in _NOVA_MICRO_TASKS else "nova_lite"

    def _bucket(self, task_type: str) -> _TokenBucket:
        return _micro_bucket if task_type in _NOVA_MICRO_TASKS else _lite_bucket

    def _call_bedrock(
        self,
        model_id: str,
        messages: list[dict],
        system_prompt: str,
    ) -> dict[str, Any]:
        """Raw Bedrock Converse API call."""
        return self._client.converse(
            modelId=model_id,
            system=[{"text": system_prompt}],
            messages=messages,
            inferenceConfig={"maxTokens": 1024, "temperature": 0.7},
        )

    def chat(
        self,
        task_type: str,
        user_message: str,
        conversation_history: Optional[list[dict]] = None,
    ) -> BedrockResponse:
        """
        Send a message to the appropriate Nova model.

        Args:
            task_type: One of the recognised task type strings.
            user_message: The latest message from the user.
            conversation_history: List of {"role": "user"|"assistant", "content": str}
                                  for multi-turn context.
        Returns:
            BedrockResponse with content and token usage.
        """
        if not self._enabled:
            return _fallback_response(task_type, user_message)

        model_id = self._model_id(task_type)
        model_name = self._model_name(task_type)
        bucket = self._bucket(task_type)

        # Build message list in Bedrock Converse format
        history = conversation_history or []
        messages = [
            {"role": m["role"], "content": [{"text": m["content"]}]}
            for m in history
            if m["role"] in ("user", "assistant")
        ]
        messages.append({"role": "user", "content": [{"text": user_message}]})

        # Rate-limit check
        if not bucket.wait_and_acquire(timeout=10.0):
            logger.warning("Rate limit exceeded for %s, using fallback.", model_name)
            return _fallback_response(task_type, user_message)

        # Retry loop with exponential backoff + jitter
        last_error: Optional[Exception] = None
        for attempt in range(self._MAX_RETRIES):
            try:
                response = self._call_bedrock(model_id, messages, _SYSTEM_PROMPT)
                content = response["output"]["message"]["content"][0]["text"]
                usage = response.get("usage", {})
                return BedrockResponse(
                    content=content,
                    model_used=model_name,
                    input_tokens=usage.get("inputTokens", 0),
                    output_tokens=usage.get("outputTokens", 0),
                )
            except ClientError as exc:
                error_code = exc.response["Error"]["Code"]
                if error_code in ("ThrottlingException", "ServiceUnavailableException"):
                    backoff = self._BASE_BACKOFF * (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(
                        "Bedrock throttled (attempt %d/%d), retrying in %.2fs",
                        attempt + 1, self._MAX_RETRIES, backoff,
                    )
                    time.sleep(backoff)
                    last_error = exc
                else:
                    logger.error("Bedrock error: %s", exc)
                    return _fallback_response(task_type, user_message)
            except Exception as exc:
                logger.error("Unexpected Bedrock error: %s", exc)
                return _fallback_response(task_type, user_message)

        logger.error("All Bedrock retries exhausted: %s", last_error)
        return _fallback_response(task_type, user_message)


# ── Singleton ─────────────────────────────────────────────────────────────────
_bedrock_client: Optional[BedrockClient] = None


def get_bedrock_client() -> BedrockClient:
    global _bedrock_client
    if _bedrock_client is None:
        _bedrock_client = BedrockClient()
    return _bedrock_client
