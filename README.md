# KvK Castle Battle Command Center

A comprehensive Streamlit application for planning, coordinating, and managing KvK (Kingdom vs Kingdom) wave launches and guild roster organization. Features wave timing calculations, synchronized arrival planning, and interactive roster management with member distribution by combat objects.

## Features

### 🌊 Waves + Counter Rally Tab
- Calculate Wave 1, 2, and 3 launch times with adjustable march durations
- Wave 2/3 offsets: fixed at +15s and +30s from Wave 1
- Create **staggered arrival** plans (different arrival times for each wave)
- Create **synchronized arrival** plans (all waves arrive at same time)
- Adjustable march times per wave for synchronized calculations
- Auto-generated copy/paste ready command messages (≤512 chars)
- Optional Excel calculator integration for preset values

### 📋 Roster Tab
- Load and manage guild member roster from `KvK 2.xlsx`
- Edit member data inline with per-column dropdowns:
  - **Alliance**: TFR, TNS, EVA, RAW, DEU
  - **TG Level**: TG1-TG8
  - **Status**: Active, Inactive, Part-Time
  - **Availability**: Yes, No
  - **Position**: Leader, Joiner
  - **Object**: Castle, Nord, West, East, South, CA
- Color-coded preview display for quick visual reference
- Multiple sheet support (switch between different rosters)
- Save changes directly to Excel file

### 🎯 Object Distribution Tab
- Automatically groups and displays members by combat Object
- Expandable sections for each Object (Castle, Nord, West, East, South, CA)
- Shows member count per Object
- Displays Name, Position, and Object assignment
- Real-time synchronization with Roster tab changes
- Read-only view (editing done in Roster tab)

## Prerequisites
- Python 3.10 or newer
- Git (optional, for deployment)

## Installation

### Local Setup

```bash
# Clone repository (or extract project)
cd KVK

# Create virtual environment
python -m venv .venv
source .venv/Scripts/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

The app will open at `http://localhost:8501` in your browser.

## Usage

### Waves + Counter Rally
1. Upload optional Excel calculator (`KvK_Battle_Calculators (1).xlsx`) for preset values
2. Adjust Wave 1 launch time and march durations
3. Choose staggered or synchronized arrival mode
4. Copy generated command messages for voice/text coordination

### Roster Management
1. Navigate to the **Roster** tab
2. Select the sheet to edit from dropdown
3. Scroll through colored preview to see current state
4. Edit any cell in the editable table using dropdowns for preset options
5. Click **Save** to persist changes to `KvK 2.xlsx`
6. Click **Discard** to revert changes without saving

### Object Distribution
1. Navigate to the **Object Distribution** tab
2. First open **Roster** tab to load roster data
3. Expand each Object section to view assigned members
4. Changes made in Roster tab are reflected here in real-time
5. Use this view for tactical Object coordination

## Project Structure

```
KVK/
├── app.py                              # Main Streamlit application
├── KvK.py                              # Configuration, constants, helper functions
├── requirements.txt                    # Python dependencies
├── README.md                           # This file
├── KvK 2.xlsx                          # Guild roster workbook (user data)
├── roster_db.xlsx                      # Backup/alternate save location
├── KvK_Battle_Calculators (1).xlsx     # Optional calculator reference
├── ocr_merged.csv                      # OCR data (reference)
└── Images/                             # Battle screenshot references
    ├── Hero Power/
    ├── Hero's Total Power/
    ├── Mystic Trial/
    ├── Personal Power/
    ├── Total Pet Power/
    ├── Town Center Level/
    └── ...
```

## Key Files

- **`app.py`** (1300+ lines)
  - Main Streamlit application with all UI logic
  - Functions: `render_wave_and_timing_tab()`, `render_roster_tab()`, `render_object_distribution_tab()`
  - Includes wave timing calculations, roster management, and styling

- **`KvK.py`**
  - Canonical option lists: `ALLIANCE_OPTS`, `TG_OPTS`, `STATUS_OPTS`, `AVAILABILITY_OPTS`, `POSITION_OPTS`, `OBJECT_OPTS`
  - Color map: `COLOR_MAP` for visual styling (active/inactive, positions, objects)
  - Utility functions: `get_column_options()`, `get_color_for_value()`, roster I/O functions

- **`requirements.txt`**
  - Python dependencies for Streamlit, pandas, openpyxl, and utilities

## Configuration

All configuration is done through the Streamlit UI:
- Roster file: `KvK 2.xlsx` (auto-loaded)
- Save locations: Original file (`KvK 2.xlsx`) or backup (`roster_db.xlsx`)
- Color scheme and styling: Defined in `KvK.COLOR_MAP`
- Option lists: Defined in `KvK.py` (modify to add/remove alliance names, statuses, etc.)

## Deployment to Streamlit Cloud

1. Push your repository to GitHub
2. Go to https://share.streamlit.io and sign in with GitHub
3. Click "New app"
4. Select repository, branch → set main file to `app.py`
5. Click "Deploy"

## Troubleshooting

**"KvK 2.xlsx file not found"**
- Ensure `KvK 2.xlsx` is in the same directory as `app.py`
- Check that the file is not open in another application

**Dropdowns not appearing in Roster tab**
- Verify that column names match: Alliance, TG Level, Status, Availability, Position, Object
- Check that `KvK.py` has correct option lists defined

**Object Distribution shows "No data available"**
- Open Roster tab first to load roster data into session state
- Ensure members have Object assignments

**Excel file locked error**
- Close the Excel file if it's open in another application
- App will auto-save to `roster_backup_<timestamp>.xlsx` if original is locked

## Notes

- The app uses Streamlit's session state to keep roster data in sync across tabs
- Colors are applied based on `COLOR_MAP` in `KvK.py` — customize hex colors there
- Wave calculations assume T+0:00 is the reference point for Wave 1
- March times are customizable per wave in the UI

## License

Internal use for guild coordination.

---

**Last updated**: May 2026  
**Built with**: Python 3.10+, Streamlit 1.24+, pandas, openpyxl
