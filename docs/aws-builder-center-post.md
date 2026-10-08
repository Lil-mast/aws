# We Built a Financial Health App with Kiro — Here's What Happened 🚀

At the AWS AI/ML User Group Nairobi event, our team sat down with one goal: build something real, something useful, something *African*.

We built **Mula** — a personal finance app designed for the Kenyan market. Think M-Pesa syncing, a credit score engine that actually makes sense for how people here save and spend, and an AI coach powered by **AWS Bedrock (Nova Lite + Nova Micro)** that explains your financial health in plain language.

---

## Enter Kiro

We used **Kiro**, the AI-powered dev environment built on VS Code, to move fast without breaking everything.

Kiro helped us:
- Scaffold the FastAPI backend with async SQLAlchemy, JWT auth, and modular apps (users, transactions, AI assistant, credit score)
- Design the **Mula Score engine** — a deterministic 300–850 scoring system with five weighted factors: payment consistency, savings behavior, spending discipline, debt management, and financial stability
- Wire up AWS Bedrock as the AI layer with rate limiting, retries, and a local fallback
- Keep the React + TypeScript frontend clean with TailwindCSS and Framer Motion animations for the score gauge

The best part? Kiro understood the *context* of what we were building. It wasn't just autocomplete — it was a collaborator that helped us think through architecture decisions in real time.

---

## The Stack

`FastAPI` · `React` · `AWS Bedrock` · `PostgreSQL` · `Redis` · `Celery` · `M-Pesa` · `Paystack` · `Cloudflare Workers`

---

## Big Thanks 🙏

Huge shoutout to **Kevin Tuei** for organizing and to the entire **AWS AI/ML User Group Kenya** for creating a space where builders can actually build. The energy in that room was something else.

This is just the beginning for Mula. Score API, lender integrations, and the what-if simulator are up next.

If you're building in the fintech or AI space in East Africa — let's connect. 🌍

---

*Built with AWS Bedrock · Powered by Kiro · Inspired by Nairobi*
