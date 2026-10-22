# GitHub repository

Repository: https://github.com/ADI238IND/zentromart-voiceops-2026

The repository is public and contains the implementation and deliverables. Review each later change before pushing. Never publish credentials, the supplied dataset or personal recordings.

## Work on the repository in PowerShell

Install Git, then clone the repository with your GitHub account authenticated:

```powershell
git clone https://github.com/ADI238IND/zentromart-voiceops-2026.git
cd zentromart-voiceops-2026
```

Use the README setup instructions. Import the supplied dataset locally; do not commit it. Add credentials only to `.env`.

To push changes from that clone, stage only reviewed files, commit, then push:

```powershell
git add src tests docs README.md SUBMIT.md run.py app.py evaluate.py make_report.py package_submission.py report.pdf sample_outputs
git diff --cached --name-only
git commit -m "Update VoiceOps implementation and measured results"
git push
```

If you are working from the downloaded project ZIP instead of a clone, `publish_github.ps1` creates a fresh `publish-checkout/` clone, copies an explicit allowlist and pushes it. It never changes visibility. It stops if that checkout already exists, so later work can be reviewed there. Configure Git user.name/user.email if Git requests them; authenticate through Git Credential Manager or the official GitHub CLI. Never publish `.env`, dataset/, recordings/, generated tickets or a virtual environment.
