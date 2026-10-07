# AI usage log

## How I worked
I read the brief, email thread, ops policy and README myself, ran every script, checked each output, and made the final decisions. I used AI as a reviewer and a code writer, not as the decision-maker.

## Claude (chat) — second reviewer
- **Used for:** Cross-checking my reading of the brief against the email and policy; flagged that team_label is the bot's guess, not the true team; checked my cost arithmetic; reviewed scripts for bugs.
- **Helped:** Caught the team-rename mapping bug and a hardcoded path before submission.
- **Wasted time:** Setup commands written for PowerShell while my terminal was cmd (~10 min).
- **Cost:** Rs 0 extra (existing subscription).

## Gemini (chat) — code writing
- **Used for:** Writing src/01_audit.py and requirements.txt from my specifications.
- **Wasted time:** Hardcoded a D:\ path, mis-read the team rename (9 teams instead of 7), counted duplicates wrongly.
- **Discarded:** First version of the audit script; I kept the corrected, reviewed version.
- **Cost:** Rs 0 (free tier).