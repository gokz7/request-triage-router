# Evidence: does the routing model work, and how often does it fail?

## How it was tested
- **Truth:** the team that closed the request (`final_team`), not the bot's original queue. The bot's queue matches the closing team only 77.2% of the time across all 10,822 training rows.
- **Time-based split**, because the hidden test set is the most recent 3 months:
  - Train: Apr–Dec 2025 (6,519 requests)
  - Tune (choosing between models): Jan–Mar 2026 (2,168)
  - Report: Apr–Jun 2026 (2,135), never used for training or choosing
- Every model tried is listed in `logs/experiments.md`, kept or dropped, with the reason.

## Headline numbers (Apr–Jun 2026, 2,135 requests)

| Approach | Correct team | Status |
|---|---|---|
| Always "Repairs" (lazy baseline) | 23.3% | Floor |
| Current routing bot | 76.7% | Number to beat |
| Logistic regression on words + product/warranty/channel | 84.1% | Dropped |
| Same + character patterns | 83.8% | Dropped: no gain, slower |
| **Same + first and last issue read separately** | **85.6%** | **Kept** |
| Same + product taken from the text | 85.5% | Dropped: no gain |

The kept model beats the bot on every slice tested:

| Slice | Requests | Model | Bot |
|---|---|---|---|
| One issue in the message | 1,852 | 85.3% | 76.1% |
| Two or more issues | 283 | 87.3% | 80.6% |
| Product field contradicts the text | 339 | 81.1% | 74.9% |

## How often it fails, and what happens then

The model gives each request a confidence. At a cut-off of 0.5:

| | Share of requests | Correct |
|---|---|---|
| Confident: auto-routed | 85.0% | 97.0% |
| Unsure: call the customer back first | 15.0% | 20.9% if guessed |

On these 2,135 requests: about **54 wrong auto-routes** (2.5% of all requests) and **320 call-backs**. Guessing on the unsure group would be wrong about 4 times in 5, so the service shows "Call the customer back first" instead of a team.

| Cut-off | Auto-routed | Correct among auto-routed | Correct below cut-off |
|---|---|---|---|
| 0.4 | 86.4% | 95.7% | 21.4% |
| **0.5** | **85.0%** | **97.0%** | **20.9%** |
| 0.6 | 84.1% | 97.4% | 23.0% |
| 0.7 | 82.2% | 97.7% | 29.7% |

## The kinds of request it gets wrong
I read 50 errors of the first model by hand (30 confident errors, 20 low-confidence). This review is what led to the kept model.

**30 confident errors:**
- **15 were two-issue messages where the last issue decided the team** (e.g. a payment problem followed by "cooktop not turning on" was closed by Repairs). The first model weighed all words equally. Reading the first and last issue separately fixed many of these: on two-issue messages, a model using only the last issue scores 88.0%, only the first 47.7%.
- **15 look like labelling errors:** a clear single-issue message closed by an unrelated team ("charged twice" closed by Warranty Claims; "power consumption of ceiling fan" closed by Filters & Consumables). In most of these, the bot's original queue was the sensible one. No model can score these. Separately, the 126 requests with zero transfers but a different closing team score 0% for both model and bot.
- **11 of the 30 had a product field that contradicts the text** (16% of all requests do).

**20 low-confidence requests:** all vague ("complaint about…", "not happy with…", "please call back regarding…"). Their closing teams are spread across all 7 teams, so the message alone cannot decide. The model was right on 5 of 20 and guessed Repairs on 11, which is why Repairs is predicted more often on the test set (27.2%) than it occurs in training (23.4%). The service asks for a call-back on these.

**Wording not seen in training:** messages are templated. "Package is broken" was not recognised as a damaged delivery; the model fell to a call-back rather than guessing.

## Expected score on the hidden test set
About **85.5% correct** (likely 84%–87%), measured against the closing team.
- Tune and report periods both gave 85–86%.
- The test set looks like the report period: 15.2% low-confidence vs 15.0%, the same share of two-issue messages (12.9%), and the same product and channel mix.
- The range is the 95% margin for 2,178 requests (about ±1.5 points).
- Ceiling: below about 92%, because of label noise.

## Money (Ops policy §4 costs)
One bot misroute costs about Rs 742 (real transfers × Rs 305 + one extra contact at Rs 260). Misroute cost per request: bot **Rs 173**, model **Rs 107**. At 722 requests a month, that saves about **Rs 5.7 lakh a year**, plus the **Rs 3.2 lakh** licence. Assumes a model misroute costs the same as a bot misroute.

## Reproduce
`python src/04_features.py` prints every number above into `logs/04_features.txt`. The manual review file (`data/work/errors_review.csv`) is built by `src/03_errors.py` and stays local because it contains customer text.