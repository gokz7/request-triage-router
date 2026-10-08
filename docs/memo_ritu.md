# Memo: Replacing the routing bot

**To:** Ritu Deshpande, Head of D2C Operations
**Cc:** Farhan Sheikh, Meenal Joshi, Tanmay Kulkarni
**Date:** 8 October 2026

## The decision
**Do not renew the bot for another year. Replace it with the new router, after a two-week trial alongside the bot.**

## The number
I tested both on the latest three months of requests (Apr–Jun 2026, 2,135 requests), checking each against the team that **actually closed** it.

- **The bot sent 77 in 100 requests to the right team. The new router sends 86 in 100.**
- For the 85% of requests where the router is sure, it is right **97 times in 100**. That is above your 90% bar.
- For the other 15% (about **108 requests a month**, messages like "please call me about my purifier"), nobody can tell the team from the message. The router says so and asks the agent to **call the customer back first**, instead of guessing. A guess there is wrong 4 times in 5.

**Why I did not aim for "90% match with the labels":** the labels in the export are the queues the bot chose. Matching them would rebuild the bot, mistakes included. The bot's queue was the final team only 77% of the time.

## The rupees
Using the costs in the operations policy (Rs 305 per transfer, Rs 260 per extra customer contact):

| | Per year |
|---|---|
| What wrong routing costs today | about **Rs 14.7 lakh** (4.6 times the licence) |
| Saved by the new router on misroutes | about **Rs 5.7 lakh** |
| Bot licence no longer paid | **Rs 3.2 lakh** |
| **Total saving** | **about Rs 8.9 lakh** |

If one call-back is enough to route the unclear 15% correctly, the saving rises to about **Rs 13.2 lakh**.

**Monthly running cost (for Farhan): Rs 0** in licences or AI fees. No charge per request; it runs on an ordinary office computer or existing server.

## For headcount planning
Planning from the bot's queues would staff the wrong teams. Actual work per team (by closing team) vs what the bot's queues suggest:
- **Busier than they look:** Installs & Demo (+35%), Warranty Claims (+33%), Returns & Replacement (+31%), Product Advice (+18%)
- **Quieter than they look:** Filters & Consumables (−27%), Billing (−20%), Repairs (−19%)

This matches Meenal's experience: Billing receives payment-mentioning requests that belong to Installs or Repairs, and Filters & Consumables receives purifier breakdowns.

## What to do next week
1. **Start a two-week trial.** Run the router alongside the bot on live requests; customers see no change. Each day, compare its choice with the team that closed the request.
2. **Give Meenal's team the call-back list** (about 25 requests a week) and track whether one call settles the right team.
3. **Ask the bot vendor for a one-month extension** instead of a one-year renewal, to cover the trial.
4. **Switch off the bot** after the trial if the router stays at 85%+ and call-backs stay near 15%.
5. **Ask Tanmay to check the product field at intake.** It disagrees with the customer's own message in 16% of requests.

*Supporting detail: docs/evidence.md (how it was tested) and logs/decisions.md (every decision and why).*