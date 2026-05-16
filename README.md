KvK Castle Battle Command Center

Run locally:

```bash
pip install -r requirements.txt
streamlit run app.py
```

Deploy to Streamlit Cloud:

- Push this repository to GitHub.
- Connect the repo in https://share.streamlit.io and set the entrypoint to `app.py`.

Notes:

- The app works without the optional Excel workbook; upload `KvK_Battle_Calculators (1).xlsx` in the UI to use sheet defaults.
- Default march durations updated: Wave1=36s, Wave2=38s, Wave3=43s.
- "Our Map" tab removed and the counter-rally timer was removed from the Waves tab per requirements.
