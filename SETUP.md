# Setup (Windows, PowerShell)

One-off, from the repo folder:

```powershell
cd C:\Users\nghil\Projects\ProcessAndRequirementsBuilder
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
copy .env.example .env      # then put your Anthropic API key in .env
pytest
```

`pytest` should report **1 passed**.

Each work session after that:

```powershell
cd C:\Users\nghil\Projects\ProcessAndRequirementsBuilder
.\.venv\Scripts\Activate.ps1
```

If `py -3.12` isn't found, install Python 3.12 from python.org (tick "Add to PATH"). If `Activate.ps1` is blocked, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once.
