# Mula user story

## Personal finance user

**As a person managing money across income, bills, savings, and day-to-day
spending, I want one place to record and understand my finances, so I can make
clearer decisions and build healthier habits.**

### Main journey

1. I create an account and set my profile, currency, and financial context.
2. I add or import income and transactions, then categorize spending.
3. I create a budget and savings goals that reflect my priorities.
4. I review progress and ask the AI coach for explanations or practical next
   steps based on my financial activity.
5. Once enough history is available and I consent, I review my Mula Score,
   understand the factors behind it, and track decisions that affect it.

### Acceptance criteria

- Account data and financial records are associated with the signed-in user.
- The user can see income, spending, budget allocations, and savings progress
  in their chosen currency.
- Coach responses explain the available financial context and do not invent
  account facts or change calculated score values.
- The score is presented as an educational financial health measure, with its
  factors and recorded events available for explanation.
- Score history is not used unless the user has provided score consent.
- Users can request access to or deletion of their personal data.

## First release scope

The current backend provides foundational models and API modules for accounts,
transactions, financial planning, conversations, and score records. M-Pesa
sync, complete score APIs, and some product experiences are still planned; the
journey above describes the intended user outcome, not a claim that every step
is already available in the current build.
