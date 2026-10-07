# Decisions

## 1. Train on final_team, not team_label
- **Why:** team_label is the old bot's guess. Copying it would rebuild the bot.
- **Evidence:** Email (Tanmay) and Ops policy §3. Bot matches final_team only 77.2% of the time.

## 2. Use the 7 current team names
- **Why:** Test data (Jul–Sep 2026) is after the 15 Jan 2026 rename. Old names mapped: Installations → Installs & Demo, Consumables → Filters & Consumables.
- **Evidence:** Ops policy §5, teams.csv.

## 3. Do not use team_label as a model input
- **Why:** It is not in the test file.

## 4. Fix Zoho resolution times (+330 min)
- **Why:** Stored in UTC, never converted to IST.
- **Evidence:** Ops policy §9. 26.4% of Zoho rows resolved before creation; 0% after fix.

## 5. Repair garbled text in Zoho rows
- **Why:** 11.1% of Zoho rows affected; test has none.
- **Evidence:** Email (Tanmay), audit.

## 6. Keep 126 inconsistent rows, flagged
- **Why:** 0 transfers but first team ≠ final team. Final team is still valid; dropping them isn't justified.

## 7. Validate on the latest 3 months (Apr–Jun 2026)
- **Why:** Test is the most recent 3 months. A random split would overstate the score.

## 8. Volume = 722 requests/month
- **Why:** Measured from data (10,822 ÷ 15 months), not the brief's "about 700".

## 9. One misroute costs Rs 742
- **Why:** Based on real transfer counts. Assumed the same for model misroutes.
- **Math:** (3,902 transfers × Rs 305 + 2,471 misroutes × Rs 260) ÷ 2,471 = Rs 742.

## 10. Unclear requests still get a team
- **Why:** Every row needs one of the 7 teams. The service flags these as low confidence, needing a call-back.

## 11. No client data in the public repo
- **Why:** Ops policy §10 and Task 1 feedback. The model file is not committed; the README rebuilds it from the data pack.
## 12. Model: logistic regression on words + product/warranty/channel (M2)
- **Why:** Highest validation accuracy, Rs 0 per request, and it gives reasons a person can read.
- **Evidence:** VALID (Apr–Jun 2026): model 84.1% vs bot 76.7%; Water Purifier 85.9% vs 66.4%.

## 13. Dropped character n-grams (M3)
- **Why:** No gain (83.8% vs 84.1%) and slower to train.

## 14. 90% on every request is not realistic
- **Why:** Both model and bot get 12.9% of requests wrong; these lack routing information. Requests below 0.4 confidence are right only ~24% of the time.
- **Evidence:** At confidence ≥ 0.4 the model routes 85.7% of requests at 94.2% accuracy.
## 15. Read the last issue separately (M4 kept)
- **Why:** In two-issue messages, the last issue decides the team.
- **Evidence:** On 283 two-issue VALID rows: last issue only 88.0%, first issue only 47.7%. M4 85.6% vs M2 84.1% on VALID.

## 16. Product named in text not used (M5 dropped)
- **Why:** No gain (85.5% vs 85.6%); the words already carry the product.

## 17. product_family column is unreliable
- **Why:** It contradicts the product named in the text in 16% of rows (train, valid and test alike). Reported as a data issue.

## 18. The 126 flagged rows are label errors
- **Evidence:** On the 29 in VALID, both model and bot score 0%. Kept in training (1.2% of rows), reported in the form.

## 19. No hand-written policy rules
- **Why:** teams.csv shows routing depends on what the issue is, not warranty status; the model learns this from the words.

## 20. Confidence threshold 0.5 for auto-routing
- **Why:** Auto-routes 85% of requests at 97.0%. The rest are right only 21% of the time, so a call-back (Rs 260) is cheaper than a guess (~Rs 586 expected).

## 21. Model selection moved to TUNE data
- **Why:** Keeps the VALID score honest. The earlier M2-vs-M3 choice used VALID; the gap was small (0.3 points) and is disclosed.## 15. Read the last issue separately (M4 kept)
- **Why:** In two-issue messages, the last issue decides the team.
- **Evidence:** On 283 two-issue VALID rows: last issue only 88.0%, first issue only 47.7%. M4 85.6% vs M2 84.1% on VALID.

## 16. Product named in text not used (M5 dropped)
- **Why:** No gain (85.5% vs 85.6%); the words already carry the product.

## 17. product_family column is unreliable
- **Why:** It contradicts the product named in the text in 16% of rows (train, valid and test alike). Reported as a data issue.

## 18. The 126 flagged rows are label errors
- **Evidence:** On the 29 in VALID, both model and bot score 0%. Kept in training (1.2% of rows), reported in the form.

## 19. No hand-written policy rules
- **Why:** teams.csv shows routing depends on what the issue is, not warranty status; the model learns this from the words.

## 20. Confidence threshold 0.5 for auto-routing
- **Why:** Auto-routes 85% of requests at 97.0%. The rest are right only 21% of the time, so a call-back (Rs 260) is cheaper than a guess (~Rs 586 expected).

## 21. Model selection moved to TUNE data
- **Why:** Keeps the VALID score honest. The earlier M2-vs-M3 choice used VALID; the gap was small (0.3 points) and is disclosed.## 15. Read the last issue separately (M4 kept)
- **Why:** In two-issue messages, the last issue decides the team.
- **Evidence:** On 283 two-issue VALID rows: last issue only 88.0%, first issue only 47.7%. M4 85.6% vs M2 84.1% on VALID.

## 16. Product named in text not used (M5 dropped)
- **Why:** No gain (85.5% vs 85.6%); the words already carry the product.

## 17. product_family column is unreliable
- **Why:** It contradicts the product named in the text in 16% of rows (train, valid and test alike). Reported as a data issue.

## 18. The 126 flagged rows are label errors
- **Evidence:** On the 29 in VALID, both model and bot score 0%. Kept in training (1.2% of rows), reported in the form.

## 19. No hand-written policy rules
- **Why:** teams.csv shows routing depends on what the issue is, not warranty status; the model learns this from the words.

## 20. Confidence threshold 0.5 for auto-routing
- **Why:** Auto-routes 85% of requests at 97.0%. The rest are right only 21% of the time, so a call-back (Rs 260) is cheaper than a guess (~Rs 586 expected).

## 21. Model selection moved to TUNE data
- **Why:** Keeps the VALID score honest. The earlier M2-vs-M3 choice used VALID; the gap was small (0.3 points) and is disclosed.## 15. Read the last issue separately (M4 kept)
- **Why:** In two-issue messages, the last issue decides the team.
- **Evidence:** On 283 two-issue VALID rows: last issue only 88.0%, first issue only 47.7%. M4 85.6% vs M2 84.1% on VALID.

## 16. Product named in text not used (M5 dropped)
- **Why:** No gain (85.5% vs 85.6%); the words already carry the product.

## 17. product_family column is unreliable
- **Why:** It contradicts the product named in the text in 16% of rows (train, valid and test alike). Reported as a data issue.

## 18. The 126 flagged rows are label errors
- **Evidence:** On the 29 in VALID, both model and bot score 0%. Kept in training (1.2% of rows), reported in the form.

## 19. No hand-written policy rules
- **Why:** teams.csv shows routing depends on what the issue is, not warranty status; the model learns this from the words.

## 20. Confidence threshold 0.5 for auto-routing
- **Why:** Auto-routes 85% of requests at 97.0%. The rest are right only 21% of the time, so a call-back (Rs 260) is cheaper than a guess (~Rs 586 expected).

## 21. Model selection moved to TUNE data
- **Why:** Keeps the VALID score honest. The earlier M2-vs-M3 choice used VALID; the gap was small (0.3 points) and is disclosed.
## 22. predictions.csv is committed to the repo
- **Why:** It is a required deliverable and holds only request IDs and team names, no customer text.

## 23. Repairs is slightly over-predicted on test (27.2% vs 23.4% in training)
- **Why:** Vague, low-confidence messages default to Repairs. The service flags these for a call-back instead of auto-routing.
- **Evidence:** Low-confidence share on test 15.2%, same as validation (15.0%).
## 24. Low-confidence requests show "Call the customer back first", not a team
- **Why:** An agent reads the headline. Showing a team name for a weak guess invites the same misroute we are trying to remove. The team appears only as a labelled weak guess.
- **Evidence:** VALID: requests below 0.5 confidence are right only 21% of the time.

## 25. Call-back reason depends on why confidence is low
- **Why:** A two-issue message is clear but ambiguous about which problem comes first; a vague message has no clear problem. The agent needs a different question for each.
- **Evidence:** Same two-issue fan message: 55% in warranty (auto-route), 49% out of warranty (call-back).

## 26. Known weakness: wording the model has not seen
- **What:** "package is broken" (a damaged delivery) was not recognised; the model fell to a call-back (40% Product Advice, 36% Installs).
- **Why:** Training messages are templated ("arrived damaged", "box was open"); the model learned those phrasings.
- **Effect:** Hidden test score unaffected (same templates). Real traffic will have more new wording, so the call-back rate may be higher than 15%.
- **Action:** Run alongside the bot for 2–4 weeks before switching it off; measure the call-back rate on real requests.

## 27. No LLM call in the product
- **Why:** (1) Ops policy §10 limits customer data to approved vendors; an outside AI provider would need Kestrel's approval. (2) Finance wants no per-request AI bill; the local model costs Rs 0. (3) Unclear requests already go to a safe call-back.
- **Would reconsider:** If the parallel run shows the call-back rate is much higher than 15% and Kestrel approves a provider.