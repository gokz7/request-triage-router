# Experiments
| date | approach | features | validation split | metric | score | kept/dropped | reason |
|---|---|---|---|---|---|---|---|
| 2026-10-07 | M0 bot baseline | team_label (bot queue) | fit<2026-01, tune=Jan-Mar 2026, valid=Apr-Jun 2026 | accuracy / macro-F1 | 0.767 / 0.780 | Baseline | Number to beat |
| 2026-10-07 | M1 majority class | none | fit<2026-01, tune=Jan-Mar 2026, valid=Apr-Jun 2026 | accuracy / macro-F1 | 0.233 / 0.054 | Baseline | Floor |
| 2026-10-07 | M2 logistic regression C=0.5 | TF-IDF words 1-2 + one-hot channel/product/warranty/combo | fit<2026-01, tune=Jan-Mar 2026, valid=Apr-Jun 2026 | accuracy / macro-F1 | 0.841 / 0.847 | Kept | Highest VALID accuracy |
| 2026-10-07 | M3 logistic regression C=0.5 | M2 + TF-IDF chars 3-5 | fit<2026-01, tune=Jan-Mar 2026, valid=Apr-Jun 2026 | accuracy / macro-F1 | 0.838 / 0.842 | Dropped | Lower VALID accuracy than M2 logistic regression (0.838 vs 0.841) |
| 2026-10-07 | M4 C=0.5 | M2 + separate TF-IDF on first issue and last issue + issue count | fit<2026-01, tune=Jan-Mar 2026 (selection), valid=Apr-Jun 2026 (report) | tune acc / valid acc / valid macro-F1 | 0.863 / 0.856 / 0.857 | Kept | Highest TUNE accuracy |
| 2026-10-07 | M5 C=0.5 | M4 but product taken from the text when it names one | fit<2026-01, tune=Jan-Mar 2026 (selection), valid=Apr-Jun 2026 (report) | tune acc / valid acc / valid macro-F1 | 0.862 / 0.855 / 0.855 | Dropped | Lower TUNE accuracy than M4 (0.862 vs 0.863) |
| 2026-10-07 | M2 C=0.5 | TF-IDF words + one-hot channel/product/warranty/combo (previous best) | fit<2026-01, tune=Jan-Mar 2026 (selection), valid=Apr-Jun 2026 (report) | tune acc / valid acc / valid macro-F1 | 0.846 / 0.841 / 0.847 | Dropped | Lower TUNE accuracy than M4 (0.846 vs 0.863) |
