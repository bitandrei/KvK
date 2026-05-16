# KvK Castle Battle Command Center

Utility web app to plan and coordinate KvK wave launches. Built with Streamlit — provides staggered and synchronized arrival planning, adjustable march times per wave, and copy/paste ready command messages.

## Features
- Set Wave 1 launch and view Wave 2/3 offsets (fixed +15s / +30s)
- Adjustable march durations (Wave 1/2/3)
- Create staggered (different arrival) and synchronized arrival launch plans
- Override march times specifically for synchronized calculations
- Plain-text copy messages (<=512 chars) for quick voice/text commands

## Prerequisites
- Python 3.10 or newer
- Git (for deployment)

## Install (local)

```bash
python -m venv .venv
source .venv/Scripts/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Open http://localhost:8501 in a browser.

## Deploy to Streamlit Cloud
1. Push your repository to GitHub.
2. Go to https://share.streamlit.io and sign in with your GitHub account.
3. Click "New app", select your repository and branch, set the main file to `app.py`, and click Deploy.

## Files of interest
- `app.py` — main Streamlit application
- `requirements.txt` — Python dependencies
- `KvK_Battle_Calculators (1).xlsx` (optional) — Excel calculator used for defaults when uploaded via UI

## Notes
- The app works without the optional Excel workbook; upload the workbook in the UI to use sheet defaults.
- Default march durations are configurable in the UI.

If you want, I can add a `.streamlit/config.toml` for environment-specific settings or create a Dockerfile for custom hosting.
