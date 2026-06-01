from datetime import datetime, timedelta
from pathlib import Path
import re

import json
import pandas as pd
import streamlit as st
import KvK


st.set_page_config(
    page_title="KvK Castle Battle Command Center",
    page_icon="🏰",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_command_center_css() -> None:
    st.markdown(
        """
        <style>
            .stApp {
                background: radial-gradient(circle at top left, #141b2d 0%, #0a0f1f 45%, #06080f 100%);
                color: #dbe2ff;
            }
            h1, h2, h3, h4 {
                color: #f3f6ff !important;
                letter-spacing: 0.02em;
            }
            .stTabs [data-baseweb="tab-list"] {
                gap: 0.5rem;
            }
            .stTabs [data-baseweb="tab"] {
                border-radius: 0.5rem;
                background-color: rgba(18, 28, 53, 0.75);
                border: 1px solid #2f3f65;
            }
            .stTabs [aria-selected="true"] {
                background-color: rgba(43, 68, 124, 0.95) !important;
                border-color: #6f8add !important;
            }
            .cc-card {
                border: 1px solid #2f3f65;
                border-radius: 0.75rem;
                padding: 0.9rem 1rem;
                background: rgba(15, 24, 44, 0.85);
                margin-bottom: 0.8rem;
            }
            .wave-badge {
                display: inline-block;
                padding: 0.22rem 0.55rem;
                border-radius: 999px;
                border: 1px solid #5f7ac7;
                background: rgba(55, 81, 154, 0.35);
                margin-right: 0.35rem;
            }
            
            /* OBJECT INDICATORS */
            .object-indicator {
                border: 1px solid #2f3f65;
                border-radius: 0.5rem;
                padding: 1rem;
                margin-bottom: 1rem;
                background: rgba(15, 24, 44, 0.85);
            }
            .object-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 0.5rem;
                font-weight: 600;
                color: #f3f6ff;
            }
            .progress-bar {
                width: 100%;
                height: 24px;
                background-color: rgba(50, 50, 50, 0.2);
                border-radius: 4px;
                overflow: hidden;
                margin-bottom: 0.5rem;
                border: 1px solid #2f3f65;
            }
            .progress-fill {
                height: 100%;
                background: linear-gradient(90deg, #28a745, #20c997);
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 12px;
                font-weight: 600;
                white-space: nowrap;
                transition: width 0.3s ease;
            }
            .progress-text {
                color: #dbe2ff;
                font-size: 0.85rem;
                text-align: right;
            }
            
            /* MOBILE RESPONSIVE */
            @media (max-width: 768px) {
                .stApp {
                    padding: 0.5rem;
                }
                .object-indicator {
                    padding: 0.75rem;
                    margin-bottom: 0.75rem;
                }
                .object-header {
                    flex-direction: column;
                    align-items: flex-start;
                }
                .progress-bar {
                    margin-top: 0.5rem;
                    height: 20px;
                }
                .progress-fill {
                    font-size: 11px;
                }
                .stTabs [data-baseweb="tab-list"] {
                    gap: 0.2rem;
                }
            }
            
            @media (max-width: 480px) {
                h1 {
                    font-size: 1.5rem !important;
                }
                h2 {
                    font-size: 1.2rem !important;
                }
                .stMetric {
                    padding: 0.5rem;
                }
            }
            
            /* CASTLE MAP */
            .castle-map-container {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                gap: 2rem;
                margin: 2rem 0;
                padding: 2rem;
                background: rgba(15, 24, 44, 0.5);
                border-radius: 1rem;
                border: 1px solid #2f3f65;
            }
            
            .map-layout {
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 1.5rem;
                width: 100%;
            }
            
            .turrets-grid {
                display: grid;
                grid-template-columns: 1fr 1fr 1fr;
                grid-template-rows: 1fr 1fr 1fr;
                gap: 1rem;
                width: 100%;
                max-width: 600px;
                aspect-ratio: 1;
                padding: 1rem;
            }
            
            .turret-north {
                grid-column: 2;
                grid-row: 1;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .turret-west {
                grid-column: 1;
                grid-row: 2;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .castle-center {
                grid-column: 2;
                grid-row: 2;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .turret-east {
                grid-column: 3;
                grid-row: 2;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .turret-south {
                grid-column: 2;
                grid-row: 3;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .turret {
                width: 80px;
                height: 80px;
                border: 2px solid;
                border-radius: 8px;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                transition: all 0.3s ease;
                background: rgba(15, 24, 44, 0.8);
                transform: rotate(45deg);
                position: relative;
                box-shadow: inset 0 0 10px rgba(0, 0, 0, 0.3);
            }
            
            .turret:hover {
                transform: rotate(45deg) scale(1.1);
                box-shadow: 0 0 20px rgba(111, 138, 221, 0.5), inset 0 0 10px rgba(0, 0, 0, 0.3);
                border-width: 2.5px;
            }
            
            .turret.selected {
                box-shadow: 0 0 30px currentColor, inset 0 0 15px rgba(111, 138, 221, 0.3);
                border-width: 3px;
                transform: rotate(45deg) scale(1.15);
            }
            
            .turret-inner {
                transform: rotate(-45deg);
                text-align: center;
                width: 100%;
                height: 100%;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                font-size: 11px;
                font-weight: 600;
                color: #f3f6ff;
                gap: 2px;
            }
            
            .turret-name {
                font-size: 12px;
                font-weight: 700;
            }
            
            .turret-count {
                font-size: 10px;
                opacity: 0.9;
            }
            
            .castle {
                width: 100px;
                height: 100px;
                border: 2px solid #28a745;
                border-radius: 12px;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                transition: all 0.3s ease;
                background: rgba(40, 167, 69, 0.15);
                box-shadow: inset 0 0 15px rgba(40, 167, 69, 0.1), 0 0 15px rgba(40, 167, 69, 0.2);
            }
            
            .castle:hover {
                transform: scale(1.08);
                box-shadow: 0 0 25px rgba(40, 167, 69, 0.6), inset 0 0 15px rgba(40, 167, 69, 0.2);
                border-width: 2.5px;
            }
            
            .castle.selected {
                box-shadow: 0 0 40px rgba(40, 167, 69, 0.9), inset 0 0 20px rgba(40, 167, 69, 0.3);
                border-width: 3px;
                transform: scale(1.12);
            }
            
            .castle-inner {
                text-align: center;
                font-size: 12px;
                font-weight: 700;
                color: #28a745;
                display: flex;
                flex-direction: column;
                gap: 3px;
            }
            
            .castle-emoji {
                font-size: 32px;
            }
            
            .castle-count {
                font-size: 11px;
            }
            
            .ca-team-section {
                width: 100%;
                padding: 1.5rem;
                background: rgba(15, 24, 44, 0.8);
                border: 2px solid #ff6b6b;
                border-radius: 0.75rem;
                cursor: pointer;
                transition: all 0.3s ease;
            }
            
            .ca-team-section:hover {
                transform: scale(1.02);
                box-shadow: 0 0 20px rgba(255, 107, 107, 0.3);
            }
            
            .ca-team-section.selected {
                box-shadow: 0 0 30px rgba(255, 107, 107, 0.6);
                border-width: 3px;
            }
            
            .ca-team-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                color: #ff6b6b;
                font-weight: 700;
                font-size: 14px;
            }
            
            .member-list-container {
                margin-top: 2rem;
                padding: 1.5rem;
                background: rgba(15, 24, 44, 0.9);
                border: 1px solid #2f3f65;
                border-radius: 0.75rem;
                width: 100%;
                max-width: 800px;
            }
            
            .member-list-header {
                font-size: 16px;
                font-weight: 700;
                color: #f3f6ff;
                margin-bottom: 1rem;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }
            
            .member-list-content {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
                gap: 0.75rem;
            }
            
            .member-item {
                padding: 0.75rem;
                background: rgba(43, 68, 124, 0.3);
                border: 1px solid #2f3f65;
                border-radius: 0.5rem;
                font-size: 13px;
                color: #dbe2ff;
            }
            
            .member-name {
                font-weight: 600;
                color: #f3f6ff;
                margin-bottom: 0.3rem;
            }
            
            .member-info {
                font-size: 12px;
                opacity: 0.85;
            }
            
            .no-members-message {
                text-align: center;
                padding: 2rem;
                color: #999;
                font-style: italic;
            }
            
            .capacity-badge {
                display: inline-block;
                padding: 0.25rem 0.6rem;
                border-radius: 999px;
                font-size: 12px;
                font-weight: 600;
                margin-left: 0.5rem;
            }
            
            .capacity-ok {
                background: rgba(40, 167, 69, 0.3);
                color: #28a745;
            }
            
            .capacity-warning {
                background: rgba(255, 193, 7, 0.3);
                color: #ffc107;
            }
            
            .capacity-critical {
                background: rgba(220, 53, 69, 0.3);
                color: #dc3545;
            }
            
            /* RESPONSIVE CASTLE MAP */
            @media (max-width: 768px) {
                .castle-map-container {
                    padding: 1rem;
                    gap: 1.5rem;
                }
                
                .turrets-grid {
                    max-width: 400px;
                    gap: 0.75rem;
                    padding: 0.75rem;
                }
                
                .turret {
                    width: 60px;
                    height: 60px;
                    border-width: 1.5px;
                }
                
                .turret-inner {
                    font-size: 9px;
                    gap: 1px;
                }
                
                .turret-name {
                    font-size: 10px;
                }
                
                .turret-count {
                    font-size: 9px;
                }
                
                .castle {
                    width: 75px;
                    height: 75px;
                    border-width: 1.5px;
                }
                
                .castle-inner {
                    font-size: 11px;
                    gap: 2px;
                }
                
                .castle-emoji {
                    font-size: 24px;
                }
                
                .castle-count {
                    font-size: 10px;
                }
                
                .ca-team-section {
                    padding: 1rem;
                    border-width: 1.5px;
                }
                
                .member-list-container {
                    max-width: 100%;
                    padding: 1rem;
                }
                
                .member-list-content {
                    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
                }
            }
            
            @media (max-width: 480px) {
                .castle-map-container {
                    padding: 0.75rem;
                    gap: 1rem;
                    margin: 1rem 0;
                }
                
                .turrets-grid {
                    max-width: 100%;
                    gap: 0.5rem;
                    padding: 0.5rem;
                }
                
                .turret {
                    width: 50px;
                    height: 50px;
                    border-width: 1px;
                }
                
                .turret-inner {
                    font-size: 8px;
                    gap: 1px;
                }
                
                .turret-name {
                    font-size: 9px;
                }
                
                .castle {
                    width: 60px;
                    height: 60px;
                    border-width: 1px;
                }
                
                .castle-inner {
                    font-size: 10px;
                }
                
                .castle-emoji {
                    font-size: 18px;
                }
                
                .member-list-container {
                    padding: 0.75rem;
                }
                
                .member-list-content {
                    grid-template-columns: 1fr;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner=False)
def load_excel_data(uploaded_file=None):
    if uploaded_file is not None:
        xls = pd.ExcelFile(uploaded_file)
    else:
        default_path = Path("KvK_Battle_Calculators (1).xlsx")
        if not default_path.exists():
            return {}
        xls = pd.ExcelFile(default_path)

    data = {}
    for sheet_name in xls.sheet_names:
        data[sheet_name] = pd.read_excel(xls, sheet_name=sheet_name, header=None)
    return data


def seconds_to_mmss(seconds: float) -> str:
    seconds = int(round(seconds))
    sign = "-" if seconds < 0 else ""
    seconds = abs(seconds)
    return f"{sign}{seconds // 60:02d}:{seconds % 60:02d}"


def parse_mmss_to_seconds(value: str) -> int:
    parts = value.split(":")
    if len(parts) != 2:
        raise ValueError("Expected mm:ss format.")
    mins, secs = int(parts[0]), int(parts[1])
    return mins * 60 + secs


def infer_position_bucket(position: int) -> str:
    if 1 <= position <= 2:
        return "1-2 tiles (T+0:00)"
    if 4 <= position <= 6:
        return "4-6 tiles (T+0:15)"
    if 7 <= position <= 10:
        return "7-10 tiles (T+0:30)"
    return "Outside funnel range"


def build_wave_table(launch_times: dict, march_times: dict) -> pd.DataFrame:
    rows = []
    for wave, launch_dt in launch_times.items():
        march_sec = march_times[wave]
        arrival_dt = launch_dt + timedelta(seconds=march_sec)
        rows.append(
            {
                "Wave": wave,
                "Launch Time": launch_dt.strftime("%H:%M:%S"),
                "March Time (sec)": march_sec,
                "Predicted Arrival": arrival_dt.strftime("%H:%M:%S"),
            }
        )
    return pd.DataFrame(rows)


def render_wave_visual(df: pd.DataFrame) -> None:
    chart_df = df.copy()
    st.bar_chart(chart_df.set_index("Wave")["March Time (sec)"], height=250)
    st.caption("Bar shows measured march time per wave (used to estimate arrival spread).")


def _safe_str(value) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip().replace("\n", " ")


def get_sheet(excel_data: dict, contains: str):
    for name, df in excel_data.items():
        if contains.lower() in name.lower():
            return df
    return None


def get_label_value(sheet: pd.DataFrame, label: str, value_col: int = 1):
    if sheet is None:
        return None
    col0 = sheet.iloc[:, 0].apply(_safe_str)
    matches = col0[col0.str.contains(label, case=False, regex=False)]
    if matches.empty:
        return None
    row = matches.index[0]
    if value_col >= sheet.shape[1]:
        return None
    return sheet.iat[row, value_col]


def parse_hms(value: str):
    try:
        return datetime.strptime(value, "%H:%M:%S").time()
    except Exception:
        return None


def extract_default_targets(sheet1: pd.DataFrame) -> dict:
    targets = {
        "Wave 1 (1-2 tiles / T+0:00)": "12:00:30",
        "Wave 2 (4-6 tiles / T+0:15)": "12:00:33",
        "Wave 3 (7-10 tiles / T+0:30)": "12:00:36",
    }
    if sheet1 is None:
        return targets
    for key, label in [
        ("Wave 1 (1-2 tiles / T+0:00)", "Wave 1 target arrival time"),
        ("Wave 2 (4-6 tiles / T+0:15)", "Wave 2 target arrival time"),
        ("Wave 3 (7-10 tiles / T+0:30)", "Wave 3 target arrival time"),
    ]:
        val = get_label_value(sheet1, label, 1)
        if val is not None and _safe_str(val):
            targets[key] = _safe_str(val)
    return targets


def extract_fill_tracker(sheet4: pd.DataFrame) -> pd.DataFrame:
    rows = []
    if sheet4 is None:
        return pd.DataFrame()
    for i in range(len(sheet4)):
        leader = _safe_str(sheet4.iat[i, 0] if sheet4.shape[1] > 0 else "")
        if not leader:
            continue
        if ("Wave" in leader or "Turret" in leader) and ("  �  " in leader):
            min_fill = sheet4.iat[i, 1] if sheet4.shape[1] > 1 else 6
            max_cap = sheet4.iat[i, 2] if sheet4.shape[1] > 2 else 9
            current = sheet4.iat[i, 3] if sheet4.shape[1] > 3 else 0
            notes = _safe_str(sheet4.iat[i, 5] if sheet4.shape[1] > 5 else "")
            rows.append(
                {
                    "Rally / Leader": leader.replace("  �  ", " - "),
                    "Min Fillers": int(min_fill) if pd.notna(min_fill) else 6,
                    "Max Capacity": int(max_cap) if pd.notna(max_cap) else 9,
                    "Current Fill": int(current) if pd.notna(current) else 0,
                    "Notes": notes,
                }
            )
    return pd.DataFrame(rows)


def _normalize_player_name(name: str) -> str:
    raw = str(name).strip()
    lower = raw.lower()
    alias_rules = [
        (r"yensid", "[TFR]Yensid08"),
        (r"noox", "[TFR]NoOX"),
        (r"brumm", "[TFR]BRUMMBÄR"),
        (r"marc[o0]{1,2}127", "[EVA]MARCO0127"),
        (r"admiral", "[TFR]AdmiralKayne"),
        (r"\bpentode\b", "[TFR]pentode"),
        (r"noble\s*minion", "[TFR]Noble Minion"),
        (r"lord\s*minion", "[TFR]Lord Minion"),
        (r"bronson", "[TNS]BRONSON__"),
        (r"allyoucanbeam", "[TNS]Allyoucanbeam"),
        (r"kralice", "[DEU]Kralice"),
        (r"wif", "[EVA]WIFI"),
        (r"onlyhuman", "[TFR]OnlyHuman"),
        (r"pappaguru", "[TNS]Pappaguru"),
        (r"dejw", "[TFR]Dejw"),
        (r"mietek", "[TFR]Mietek"),
        (r"desillusion", "[TFR]Desillusionierer"),
        (r"daiki", "[TFR]Daiki"),
        (r"fsm\s*han", "[TFR]FSM HAN"),
    ]
    for pattern, canonical in alias_rules:
        if re.search(pattern, lower):
            return canonical
    return raw


def _is_name_usable(name: str) -> bool:
    text = str(name).strip()
    if len(text) < 3:
        return False
    if re.search(r"[A-Za-z\u4e00-\u9fff\uac00-\ud7a3]", text) is None:
        return False
    if text.count(" ") > 6:
        return False
    if text.startswith(".") or text in {"?OO", "L6", "0品[]"}:
        return False
    return True


def load_ocr_default_map_table() -> pd.DataFrame:
    csv_path = Path("ocr_merged.csv")
    if not csv_path.exists():
        return pd.DataFrame()

    df = pd.read_csv(csv_path)
    expected = ["Name", "Power", "TC Level", "Hero Power", "Heroes Total Power", "Pet Power", "Mystic Trial"]
    missing_cols = [col for col in expected if col not in df.columns]
    if missing_cols:
        return pd.DataFrame()

    merged = {}
    for _, row in df.iterrows():
        name = str(row["Name"]).strip()
        if not _is_name_usable(name):
            continue
        name = _normalize_player_name(name)
        key = re.sub(r"[^a-z0-9\u4e00-\u9fff\uac00-\ud7a3]+", "", name.lower())
        if not key:
            continue
        if key not in merged:
            merged[key] = {c: 0 for c in expected}
            merged[key]["Name"] = name
        for field in expected[1:]:
            value = int(row[field]) if pd.notna(row[field]) else 0
            merged[key][field] = max(int(merged[key][field]), value)

    if not merged:
        return pd.DataFrame()
    out = pd.DataFrame(list(merged.values()))
    out = out.sort_values("Name").reset_index(drop=True)
    return out[expected]


def get_default_map_table() -> pd.DataFrame:
    ocr_defaults = load_ocr_default_map_table()
    if not ocr_defaults.empty:
        return ocr_defaults
    return pd.DataFrame(
        [
            {
                "Name": "[TFR]Yensid08",
                "Power": 472324654,
                "TC Level": 0,
                "Hero Power": 18803568,
                "Heroes Total Power": 85331736,
                "Pet Power": 33852960,
                "Mystic Trial": 2767,
            },
            {
                "Name": "[TFR]NickM",
                "Power": 418026435,
                "TC Level": 0,
                "Hero Power": 16632814,
                "Heroes Total Power": 91623668,
                "Pet Power": 31884600,
                "Mystic Trial": 2691,
            },
            {
                "Name": "[TFR]BRUMMBÄR",
                "Power": 473008161,
                "TC Level": 5,
                "Hero Power": 18155770,
                "Heroes Total Power": 85075998,
                "Pet Power": 24294720,
                "Mystic Trial": 2581,
            },
            {
                "Name": "[TNS]Pikachu",
                "Power": 356446924,
                "TC Level": 5,
                "Hero Power": 16132269,
                "Heroes Total Power": 66454341,
                "Pet Power": 22009440,
                "Mystic Trial": 2380,
            },
            {
                "Name": "[TFR]pentode",
                "Power": 420760032,
                "TC Level": 5,
                "Hero Power": 11240450,
                "Heroes Total Power": 63848011,
                "Pet Power": 25731600,
                "Mystic Trial": 2352,
            },
            {
                "Name": "[EVA]MARCO0127",
                "Power": 342333118,
                "TC Level": 5,
                "Hero Power": 13193322,
                "Heroes Total Power": 63765723,
                "Pet Power": 19971240,
                "Mystic Trial": 2233,
            },
            {
                "Name": "[TFR]AdmiralKayne",
                "Power": 0,
                "TC Level": 0,
                "Hero Power": 11666423,
                "Heroes Total Power": 59730132,
                "Pet Power": 17735400,
                "Mystic Trial": 2117,
            },
            {
                "Name": "[EVA]WIFI",
                "Power": 357540532,
                "TC Level": 5,
                "Hero Power": 10150264,
                "Heroes Total Power": 58645303,
                "Pet Power": 18274680,
                "Mystic Trial": 2110,
            },
            {
                "Name": "[TFR]Noble Minion",
                "Power": 0,
                "TC Level": 0,
                "Hero Power": 0,
                "Heroes Total Power": 52977180,
                "Pet Power": 0,
                "Mystic Trial": 0,
            },
            {
                "Name": "[TFR]Lord Minion",
                "Power": 0,
                "TC Level": 5,
                "Hero Power": 0,
                "Heroes Total Power": 0,
                "Pet Power": 0,
                "Mystic Trial": 0,
            },
            {
                "Name": "[TFR]NoOX",
                "Power": 240325140,
                "TC Level": 5,
                "Hero Power": 4954285,
                "Heroes Total Power": 30584648,
                "Pet Power": 14788560,
                "Mystic Trial": 1497,
            },
            {
                "Name": "[TNS]Fritz",
                "Power": 366116462,
                "TC Level": 0,
                "Hero Power": 0,
                "Heroes Total Power": 0,
                "Pet Power": 0,
                "Mystic Trial": 0,
            },
            {
                "Name": "[TNS]Daenerys",
                "Power": 0,
                "TC Level": 0,
                "Hero Power": 0,
                "Heroes Total Power": 0,
                "Pet Power": 0,
                "Mystic Trial": 1958,
            },
            {
                "Name": "[TNS]Allyoucanbeam",
                "Power": 0,
                "TC Level": 0,
                "Hero Power": 0,
                "Heroes Total Power": 0,
                "Pet Power": 17575560,
                "Mystic Trial": 0,
            },
            {
                "Name": "[TNS]BRONSON__",
                "Power": 0,
                "TC Level": 5,
                "Hero Power": 0,
                "Heroes Total Power": 0,
                "Pet Power": 14527560,
                "Mystic Trial": 0,
            },
            {
                "Name": "[EVA]依依ɞyiyi",
                "Power": 0,
                "TC Level": 5,
                "Hero Power": 0,
                "Heroes Total Power": 0,
                "Pet Power": 0,
                "Mystic Trial": 0,
            },
            {
                "Name": "[EVA]刷刷刷刷刷刷",
                "Power": 0,
                "TC Level": 5,
                "Hero Power": 9708102,
                "Heroes Total Power": 0,
                "Pet Power": 0,
                "Mystic Trial": 0,
            },
            {
                "Name": "[TFR]TOP63 KOR",
                "Power": 369527836,
                "TC Level": 0,
                "Hero Power": 0,
                "Heroes Total Power": 0,
                "Pet Power": 0,
                "Mystic Trial": 0,
            },
            {
                "Name": "[TNS]한국인101",
                "Power": 208999143,
                "TC Level": 5,
                "Hero Power": 0,
                "Heroes Total Power": 0,
                "Pet Power": 0,
                "Mystic Trial": 0,
            },
            {
                "Name": "[TFR]Lord Knight 357",
                "Power": 208288403,
                "TC Level": 0,
                "Hero Power": 0,
                "Heroes Total Power": 0,
                "Pet Power": 0,
                "Mystic Trial": 0,
            },
            {
                "Name": "[RAW]Spenalson",
                "Power": 207915101,
                "TC Level": 0,
                "Hero Power": 0,
                "Heroes Total Power": 0,
                "Pet Power": 0,
                "Mystic Trial": 0,
            },
            {
                "Name": "[DEU]Kralice",
                "Power": 207715721,
                "TC Level": 0,
                "Hero Power": 0,
                "Heroes Total Power": 29514635,
                "Pet Power": 0,
                "Mystic Trial": 0,
            },
            {
                "Name": "[D8F]Mamie Tsunade",
                "Power": 207526461,
                "TC Level": 0,
                "Hero Power": 0,
                "Heroes Total Power": 0,
                "Pet Power": 0,
                "Mystic Trial": 0,
            },
            {
                "Name": "[TNS]Kings'landing",
                "Power": 207146222,
                "TC Level": 0,
                "Hero Power": 0,
                "Heroes Total Power": 0,
                "Pet Power": 0,
                "Mystic Trial": 0,
            },
            {
                "Name": "[TFR]Lord of the Seas",
                "Power": 206885210,
                "TC Level": 0,
                "Hero Power": 0,
                "Heroes Total Power": 0,
                "Pet Power": 0,
                "Mystic Trial": 0,
            },
            {
                "Name": "[TFR]FSM HAN",
                "Power": 206095334,
                "TC Level": 0,
                "Hero Power": 0,
                "Heroes Total Power": 0,
                "Pet Power": 0,
                "Mystic Trial": 1275,
            },
            {
                "Name": "[TFR]LLuna",
                "Power": 204532168,
                "TC Level": 0,
                "Hero Power": 4063041,
                "Heroes Total Power": 0,
                "Pet Power": 0,
                "Mystic Trial": 0,
            },
            {
                "Name": "[TFR]STEEL",
                "Power": 0,
                "TC Level": 0,
                "Hero Power": 3762955,
                "Heroes Total Power": 0,
                "Pet Power": 14446080,
                "Mystic Trial": 0,
            },
            {
                "Name": "[TNS]Белая ворона",
                "Power": 0,
                "TC Level": 5,
                "Hero Power": 3741745,
                "Heroes Total Power": 0,
                "Pet Power": 0,
                "Mystic Trial": 0,
            },
            {
                "Name": "[TNS]Landogost",
                "Power": 0,
                "TC Level": 0,
                "Hero Power": 3737142,
                "Heroes Total Power": 0,
                "Pet Power": 0,
                "Mystic Trial": 0,
            },
            {
                "Name": "[TFR]Veri",
                "Power": 0,
                "TC Level": 0,
                "Hero Power": 3736241,
                "Heroes Total Power": 0,
                "Pet Power": 0,
                "Mystic Trial": 0,
            },
            {
                "Name": "[TNS]Loading000",
                "Power": 0,
                "TC Level": 0,
                "Hero Power": 3729545,
                "Heroes Total Power": 0,
                "Pet Power": 0,
                "Mystic Trial": 0,
            },
            {
                "Name": "[EVA]雞蛋仔",
                "Power": 0,
                "TC Level": 0,
                "Hero Power": 3718852,
                "Heroes Total Power": 0,
                "Pet Power": 0,
                "Mystic Trial": 1277,
            },
            {
                "Name": "박현민",
                "Power": 0,
                "TC Level": 0,
                "Hero Power": 3682220,
                "Heroes Total Power": 0,
                "Pet Power": 0,
                "Mystic Trial": 0,
            },
            {
                "Name": "[TFR]Radinho",
                "Power": 0,
                "TC Level": 0,
                "Hero Power": 3655870,
                "Heroes Total Power": 0,
                "Pet Power": 0,
                "Mystic Trial": 0,
            },
            {
                "Name": "[TFR]BK 201",
                "Power": 0,
                "TC Level": 0,
                "Hero Power": 4075143,
                "Heroes Total Power": 0,
                "Pet Power": 0,
                "Mystic Trial": 0,
            },
            {
                "Name": "[TFR]JimVaria",
                "Power": 0,
                "TC Level": 0,
                "Hero Power": 4073180,
                "Heroes Total Power": 0,
                "Pet Power": 0,
                "Mystic Trial": 0,
            },
            {
                "Name": "[EVA]柳如烟",
                "Power": 0,
                "TC Level": 0,
                "Hero Power": 4069550,
                "Heroes Total Power": 0,
                "Pet Power": 0,
                "Mystic Trial": 0,
            },
            {
                "Name": "[EVA]大僧_MONK",
                "Power": 0,
                "TC Level": 5,
                "Hero Power": 3966822,
                "Heroes Total Power": 0,
                "Pet Power": 0,
                "Mystic Trial": 0,
            },
            {
                "Name": "[TNS]Akagami",
                "Power": 0,
                "TC Level": 0,
                "Hero Power": 3922490,
                "Heroes Total Power": 0,
                "Pet Power": 0,
                "Mystic Trial": 0,
            },
            {
                "Name": "[DEU]Lajiikmiii",
                "Power": 0,
                "TC Level": 0,
                "Hero Power": 3896985,
                "Heroes Total Power": 0,
                "Pet Power": 0,
                "Mystic Trial": 0,
            },
            {
                "Name": "sosopi",
                "Power": 0,
                "TC Level": 0,
                "Hero Power": 3867035,
                "Heroes Total Power": 0,
                "Pet Power": 0,
                "Mystic Trial": 0,
            },
            {
                "Name": "[TFR]Desillusionierer",
                "Power": 0,
                "TC Level": 0,
                "Hero Power": 0,
                "Heroes Total Power": 29852536,
                "Pet Power": 0,
                "Mystic Trial": 0,
            },
            {
                "Name": "[EVA]慢半拍",
                "Power": 0,
                "TC Level": 0,
                "Hero Power": 0,
                "Heroes Total Power": 29851968,
                "Pet Power": 0,
                "Mystic Trial": 0,
            },
            {
                "Name": "[TNS]Pappaguru",
                "Power": 0,
                "TC Level": 0,
                "Hero Power": 0,
                "Heroes Total Power": 29846054,
                "Pet Power": 14485440,
                "Mystic Trial": 0,
            },
            {
                "Name": "[TFR]Dejw",
                "Power": 0,
                "TC Level": 5,
                "Hero Power": 0,
                "Heroes Total Power": 29832524,
                "Pet Power": 0,
                "Mystic Trial": 0,
            },
            {
                "Name": "[TFR]OnlyHuman",
                "Power": 0,
                "TC Level": 0,
                "Hero Power": 0,
                "Heroes Total Power": 29742765,
                "Pet Power": 0,
                "Mystic Trial": 1266,
            },
            {
                "Name": "[TFR]Mietek",
                "Power": 0,
                "TC Level": 0,
                "Hero Power": 0,
                "Heroes Total Power": 29638187,
                "Pet Power": 0,
                "Mystic Trial": 0,
            },
            {
                "Name": "레오니다스",
                "Power": 0,
                "TC Level": 0,
                "Hero Power": 0,
                "Heroes Total Power": 29618298,
                "Pet Power": 0,
                "Mystic Trial": 0,
            },
            {
                "Name": "[TNS]나나땡이",
                "Power": 0,
                "TC Level": 0,
                "Hero Power": 0,
                "Heroes Total Power": 29543193,
                "Pet Power": 0,
                "Mystic Trial": 1266,
            },
            {
                "Name": "[TNS]eeedowrah",
                "Power": 0,
                "TC Level": 0,
                "Hero Power": 0,
                "Heroes Total Power": 29532945,
                "Pet Power": 0,
                "Mystic Trial": 0,
            },
            {
                "Name": "[TFR]MehmetOnur",
                "Power": 0,
                "TC Level": 0,
                "Hero Power": 0,
                "Heroes Total Power": 0,
                "Pet Power": 14515560,
                "Mystic Trial": 0,
            },
            {
                "Name": "[EVA]瑪莎maya",
                "Power": 0,
                "TC Level": 0,
                "Hero Power": 0,
                "Heroes Total Power": 0,
                "Pet Power": 14511120,
                "Mystic Trial": 0,
            },
            {
                "Name": "[EVA]KingOfTheERGUL",
                "Power": 0,
                "TC Level": 0,
                "Hero Power": 0,
                "Heroes Total Power": 0,
                "Pet Power": 14479440,
                "Mystic Trial": 0,
            },
            {
                "Name": "[TFR]Marrowgar",
                "Power": 0,
                "TC Level": 0,
                "Hero Power": 0,
                "Heroes Total Power": 0,
                "Pet Power": 14477040,
                "Mystic Trial": 0,
            },
            {
                "Name": "[TFR]Daiki",
                "Power": 0,
                "TC Level": 0,
                "Hero Power": 0,
                "Heroes Total Power": 0,
                "Pet Power": 14465280,
                "Mystic Trial": 1251,
            },
            {
                "Name": "[TNS]Wistful",
                "Power": 0,
                "TC Level": 0,
                "Hero Power": 0,
                "Heroes Total Power": 0,
                "Pet Power": 14456280,
                "Mystic Trial": 0,
            },
            {
                "Name": "[TNS]baby Pikachu",
                "Power": 0,
                "TC Level": 0,
                "Hero Power": 0,
                "Heroes Total Power": 0,
                "Pet Power": 0,
                "Mystic Trial": 1275,
            },
            {
                "Name": "[RAW]tA1lum27",
                "Power": 0,
                "TC Level": 0,
                "Hero Power": 0,
                "Heroes Total Power": 0,
                "Pet Power": 0,
                "Mystic Trial": 1273,
            },
            {
                "Name": "[EVA]JeabdE",
                "Power": 0,
                "TC Level": 0,
                "Hero Power": 0,
                "Heroes Total Power": 0,
                "Pet Power": 0,
                "Mystic Trial": 1265,
            },
            {
                "Name": "[TNS]HE MAN",
                "Power": 0,
                "TC Level": 0,
                "Hero Power": 0,
                "Heroes Total Power": 0,
                "Pet Power": 0,
                "Mystic Trial": 1261,
            },
        ]
    )


# "Our Map" UI removed per request. Kept helper functions for map data intact.


# Sidebar removed per user request (side panel and voice cheat sheet)


def render_wave_and_timing_tab(excel_data: dict) -> None:
    st.subheader("Wave Launch Planner")
    sheet1 = get_sheet(excel_data, "Wave Timing")
    sheet2 = get_sheet(excel_data, "Counter Delay")
    defaults = extract_default_targets(sheet1)

    left, right = st.columns([1.05, 1], gap="large")

    with left:
        st.markdown('<div class="cc-card">Launch-first Wave Control</div>', unsafe_allow_html=True)
        wave1_default = parse_hms(defaults["Wave 1 (1-2 tiles / T+0:00)"]) or datetime.now().time()
        t1_text = st.text_input("Wave 1 Launch Time (HH:MM:SS)", value=wave1_default.strftime("%H:%M:%S"))
        t1 = parse_hms(t1_text)
        if t1 is None:
            st.error("Invalid Wave 1 launch time. Use HH:MM:SS (example: 12:00:30).")
            return
        reference_date = datetime(2000, 1, 1)  # Use fixed reference date, not local time
        base_dt = datetime.combine(reference_date, t1)
        t2_dt = base_dt + timedelta(seconds=15)
        t3_dt = base_dt + timedelta(seconds=30)
        st.write(f"Wave 2 Launch (fixed): `{t2_dt.strftime('%H:%M:%S')}`")
        st.write(f"Wave 3 Launch (fixed): `{t3_dt.strftime('%H:%M:%S')}`")

        # Default march durations updated per request: Wave1=36s, Wave2=38s, Wave3=43s
        wave1_march_default = int(get_label_value(sheet1, "Wave 1  �  Pentode", 1) or 36)
        wave2_march_default = int(get_label_value(sheet1, "Wave 2  �  Nick", 1) or 38)
        wave3_march_default = int(get_label_value(sheet1, "Wave 3  �  Brumbar", 1) or 43)
        m1 = st.number_input("Wave 1 March Time (sec)", min_value=1, value=wave1_march_default)
        m2 = st.number_input("Wave 2 March Time (sec)", min_value=1, value=wave2_march_default)
        m3 = st.number_input("Wave 3 March Time (sec)", min_value=1, value=wave3_march_default)

        launch_times = {
            "Wave 1 (1-2 tiles)": base_dt,
            "Wave 2 (4-6 tiles)": t2_dt,
            "Wave 3 (7-10 tiles)": t3_dt,
        }
        march_times = {
            "Wave 1 (1-2 tiles)": int(m1),
            "Wave 2 (4-6 tiles)": int(m2),
            "Wave 3 (7-10 tiles)": int(m3),
        }
        # Wave table, chart, and estimated spread removed as requested

        # Different-time (staggered) arrival message (e.g., +15s, +30s)
        stagger_lines = ["(Wave strategy: staggered arrival)"]
        stagger_lines.append(f"Wave 1: launch {base_dt.strftime('%H:%M:%S')}")
        stagger_lines.append(f"Wave 2: launch {t2_dt.strftime('%H:%M:%S')}")
        stagger_lines.append(f"Wave 3: launch {t3_dt.strftime('%H:%M:%S')}")
        stagger_msg = "\n".join(stagger_lines)
        if len(stagger_msg) > 512:
            stagger_msg = stagger_msg[:509] + "..."
        st.text_area("Copy message - Different arrival (plain text, <=512 chars)", value=stagger_msg, height=120)

        # (Synchronized arrival controls moved to the right column)

    with right:
        st.markdown('<div class="cc-card">Synchronized Arrival</div>', unsafe_allow_html=True)
        # Synchronized arrival controls (moved to right column)

        # Allow overriding march times specifically for synchronized arrival
        sync_m1 = st.number_input("Synchronized Wave 1 March Time (sec)", min_value=1, value=int(m1), key="sync_m1")
        sync_m2 = st.number_input("Synchronized Wave 2 March Time (sec)", min_value=1, value=int(m2), key="sync_m2")
        sync_m3 = st.number_input("Synchronized Wave 3 March Time (sec)", min_value=1, value=int(m3), key="sync_m3")

        march_times_list = [int(sync_m1), int(sync_m2), int(sync_m3)]

        if "sync_arrival_input" not in st.session_state:
            st.session_state.sync_arrival_input = "12:00:00"

        desired_time_text = st.text_input(
            "Synchronized Arrival Time (HH:MM:SS)",
            value=st.session_state.sync_arrival_input,
            key="sync_arrival_time_input_right",
        )
        st.session_state.sync_arrival_input = desired_time_text
        desired_time = parse_hms(desired_time_text)
        if desired_time is None:
            st.error("Invalid synchronized arrival time. Use HH:MM:SS (example: 10:08:09).")
        else:
            desired_dt = datetime.combine(reference_date, desired_time)
            chosen_lines = ["(Synchronized Arrival - chosen)"]
            for i in range(1, 4):
                lt = desired_dt - timedelta(seconds=march_times_list[i - 1])
                mt = march_times_list[i - 1]
                chosen_lines.append(f"Wave {i}: launch {lt.strftime('%H:%M:%S')} (march {mt}s)")
            chosen_msg = "\n".join(chosen_lines)
            if len(chosen_msg) > 512:
                chosen_msg = chosen_msg[:509] + "..."
            st.text_area(
                "Copy message - Synchronized arrival (plain text, <=512 chars)", value=chosen_msg, height=160
            )


def apply_column_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    """
    Apply multiple column filters to roster dataframe.
    
    Args:
        df: Original dataframe
        filters: Dict with column names as keys and list of selected values as values
                Example: {"Alliance": ["TFR", "TNS"], "Status": ["Active"]}
    
    Returns:
        Filtered dataframe
    """
    filtered_df = df.copy()
    
    for column, selected_values in filters.items():
        if not selected_values:  # Skip if no values selected
            continue
        if column not in filtered_df.columns:
            continue
        
        # Case-insensitive matching for string columns
        mask = filtered_df[column].astype(str).str.lower().isin([v.lower() for v in selected_values])
        filtered_df = filtered_df[mask]
    
    return filtered_df


def save_roster_to_excel(df: pd.DataFrame, file_path: str, sheet_name: str, save_to_original: bool = False) -> tuple[bool, str]:
    """
    Save roster dataframe back to Excel file.
    Default target is roster_db.xlsx; if save_to_original=True, writes to original file.
    
    Args:
        df: Dataframe to save
        file_path: Path to original Excel file
        sheet_name: Name of sheet to write to
        save_to_original: if True, save to original file; else save to roster_db.xlsx
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        from openpyxl import load_workbook
        import time
        
        # Choose target: roster_db.xlsx by default, or original if requested
        target_path = Path(file_path) if save_to_original else Path(file_path).parent / "roster_db.xlsx"
        
        if target_path.exists():
            # Load workbook and update specific sheet
            with pd.ExcelWriter(target_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        else:
            # Create new file
            df.to_excel(target_path, sheet_name=sheet_name, index=False)
        
        return True, f"✓ Changes saved to {target_path.name}"
    except PermissionError:
        # File is locked — try to save backup with timestamp
        try:
            ts = int(time.time())
            backup_path = Path(file_path).parent / f"roster_backup_{ts}.xlsx"
            df.to_excel(backup_path, sheet_name=sheet_name, index=False)
            return True, f"✓ Original file locked; saved backup to {backup_path.name}"
        except Exception as e2:
            return False, f"✗ Error: File locked and backup also failed: {str(e2)}"
    except Exception as e:
        return False, f"✗ Error saving file: {str(e)}"


def split_dataframe_by_status(df: pd.DataFrame, status_column: str = "Status") -> dict:
    """
    Split dataframe into separate dataframes by status value.
    
    Args:
        df: Dataframe to split
        status_column: Name of status column
    
    Returns:
        Dict of {status: dataframe} for each unique status value
    """
    status_dfs = {}
    if status_column not in df.columns:
        return status_dfs
    
    for status in df[status_column].unique():
        if pd.notna(status):
            status_dfs[str(status)] = df[df[status_column] == status].reset_index(drop=True)
    
    return status_dfs


def _tag_color_map(key: str) -> dict:
    """Return color map for specific tag categories."""
    if key == "TG Level":
        return {
            "TG5": "#e34242",
            "TG4": "#f0c419",
            "TG3": "#2b7bd3",
            "TG2": "#2f9f6e",
            "TG1": "#7b4ca6",
        }
    if key == "Alliance":
        return {"TFR": "#ff9999", "TNS": "#c2f0c2", "EVA": "#cfe7ff", "RAW": "#ffd9b3", "DEU": "#e6ccff"}
    # default
    return {}


def render_selected_badges(values: list, category: str) -> None:
    """Render selected values as colored badges for visual aid."""
    if not values:
        return
    cmap = _tag_color_map(category)
    badges = []
    for v in values:
        color = cmap.get(v, "#dddddd")
        badges.append(f"<span style='display:inline-block;padding:4px 8px;margin:2px;border-radius:12px;background:{color};color:#000;font-weight:600;font-size:12px;'>{v}</span>")
    st.markdown("" + "".join(badges), unsafe_allow_html=True)


def render_status_table(status: str, df: pd.DataFrame, color: str, roster_file: str, sheet_name: str) -> None:
    """
    Render a color-coded status table with edit capability.
    
    Args:
        status: Status name (Active, Inactive, Part-Time)
        df: Dataframe for this status
        color: Hex color code (#00FF00 for green, #FF0000 for red, #FFFF00 for yellow)
        roster_file: Path to roster Excel file
        sheet_name: Name of sheet being edited
    """
    # Color-coded header
    color_emoji = {"Active": "🟢", "Inactive": "🔴", "Part-Time": "🟡"}
    emoji = color_emoji.get(status, "⚪")
    
    st.markdown(
        f"""
        <div style="background-color: {color}; padding: 10px; border-radius: 5px; margin: 10px 0;">
            <h4 style="color: black; margin: 0;">{emoji} {status} ({len(df)} members)</h4>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Editable table for this status
    edited_status_df = st.data_editor(
        df,
        use_container_width=True,
        num_rows="dynamic",
        key=f"roster_editor_{status}",
        hide_index=True
    )
    
    # Save button for this specific status table
    if st.button(f"💾 Save {status} Changes", key=f"save_{status}_btn"):
        success, message = save_roster_to_excel(edited_status_df, roster_file, sheet_name)
        if success:
            st.success(message)
        else:
            st.error(message)


def search_roster_by_name(df: pd.DataFrame, search_text: str) -> pd.DataFrame:
    """
    Filter roster by member name using substring matching (case-insensitive).
    
    Args:
        df: Roster dataframe
        search_text: Search string
    
    Returns:
        Filtered dataframe
    """
    if not search_text or not df["Name"]:
        return df
    
    search_lower = search_text.lower().strip()
    mask = df["Name"].astype(str).str.lower().str.contains(search_lower, regex=False, na=False)
    return df[mask].reset_index(drop=True)


def render_roster_tab() -> None:
    """Render the Roster tab with guild member data from KvK 2.xlsx"""
    st.subheader("Guild Roster")
    
    # Try to load KvK 2.xlsx
    roster_file = Path("KvK 2.xlsx")
    if not roster_file.exists():
        st.warning("KvK 2.xlsx file not found in the workspace.")
        return
    
    try:
        # Load all sheets from KvK 2.xlsx
        xls = pd.ExcelFile(roster_file)
        sheet_names = xls.sheet_names
        
        if not sheet_names:
            st.warning("KvK 2.xlsx has no sheets.")
            return
        
        # Let user select which sheet to view
        selected_sheet = st.selectbox("Select sheet to view:", sheet_names, index=0)
        
        # Read the selected sheet
        roster_df = pd.read_excel(roster_file, sheet_name=selected_sheet)
        roster_df = roster_df.fillna("")

        st.markdown(f"**Sheet:** {selected_sheet} | **Rows:** {len(roster_df)}")

        # Keep editable copy in session state
        if "edited_roster" not in st.session_state or st.session_state.get("edited_roster_sheet") != selected_sheet:
            st.session_state["edited_roster"] = roster_df.copy()
            st.session_state["edited_roster_sheet"] = selected_sheet
        
        # ===== SEARCH & FILTER CONTROLS =====
        # Initialize filter state
        if "roster_filters" not in st.session_state:
            st.session_state["roster_filters"] = {
                "name_search": "",
                "alliance_filter": [],
                "tg_filter": [],
                "status_filter": [],
                "object_filter": [],
                "edit_mode": True,  # True = edit, False = view-only
            }
        
        # Mode toggle and search bar in top row
        mode_col, search_col = st.columns([1, 3])
        
        with mode_col:
            edit_mode = st.checkbox("✏️ Edit Mode", value=st.session_state["roster_filters"]["edit_mode"], help="Disable to lock editing")
            st.session_state["roster_filters"]["edit_mode"] = edit_mode
        
        with search_col:
            search_text = st.text_input("🔍 Search by name:", value=st.session_state["roster_filters"]["name_search"], placeholder="Type member name...")
            st.session_state["roster_filters"]["name_search"] = search_text
        
        # Multi-select filters in expandable section
        with st.expander("🔧 Advanced Filters", expanded=False):
            filter_col1, filter_col2 = st.columns(2)
            
            with filter_col1:
                alliance_opts = sorted(set(st.session_state["edited_roster"]["Alliance"].astype(str).unique()) - {""})
                alliance_selected = st.multiselect(
                    "Alliance",
                    options=alliance_opts,
                    default=st.session_state["roster_filters"]["alliance_filter"],
                    key="alliance_multi"
                )
                st.session_state["roster_filters"]["alliance_filter"] = alliance_selected
                
                tg_opts = sorted(set(st.session_state["edited_roster"]["TG Level"].astype(str).unique()) - {""})
                tg_selected = st.multiselect(
                    "TG Level",
                    options=tg_opts,
                    default=st.session_state["roster_filters"]["tg_filter"],
                    key="tg_multi"
                )
                st.session_state["roster_filters"]["tg_filter"] = tg_selected
            
            with filter_col2:
                status_opts = sorted(set(st.session_state["edited_roster"]["Status"].astype(str).unique()) - {""})
                status_selected = st.multiselect(
                    "Status",
                    options=status_opts,
                    default=st.session_state["roster_filters"]["status_filter"],
                    key="status_multi"
                )
                st.session_state["roster_filters"]["status_filter"] = status_selected
                
                object_opts = getattr(KvK, "OBJECT_OPTS", ["Castle", "North", "West", "East", "South", "CA TEAM"])
                object_selected = st.multiselect(
                    "Object",
                    options=object_opts,
                    default=st.session_state["roster_filters"]["object_filter"],
                    key="object_multi"
                )
                st.session_state["roster_filters"]["object_filter"] = object_selected
            
            # Clear filters button
            if st.button("🔄 Clear All Filters"):
                st.session_state["roster_filters"] = {
                    "name_search": "",
                    "alliance_filter": [],
                    "tg_filter": [],
                    "status_filter": [],
                    "object_filter": [],
                    "edit_mode": True,
                }
                st.rerun()
        
        # Apply filters to roster data
        filtered_df = search_roster_by_name(st.session_state["edited_roster"], search_text)
        
        filter_dict = {}
        if st.session_state["roster_filters"]["alliance_filter"]:
            filter_dict["Alliance"] = st.session_state["roster_filters"]["alliance_filter"]
        if st.session_state["roster_filters"]["tg_filter"]:
            filter_dict["TG Level"] = st.session_state["roster_filters"]["tg_filter"]
        if st.session_state["roster_filters"]["status_filter"]:
            filter_dict["Status"] = st.session_state["roster_filters"]["status_filter"]
        if st.session_state["roster_filters"]["object_filter"]:
            filter_dict["Object"] = st.session_state["roster_filters"]["object_filter"]
        
        filtered_df = apply_column_filters(filtered_df, filter_dict)
        
        st.markdown(f"**Displayed:** {len(filtered_df)} of {len(st.session_state['edited_roster'])} members")
        
        # ===== STYLED PREVIEW WITH COLORS =====
        color_map = getattr(KvK, "COLOR_MAP", {})
        
        def style_cell(val):
            """Apply COLOR_MAP styling to cell value using substring matching (longer keys first)"""
            if pd.isna(val) or val == "":
                return ""
            val_str = str(val).lower().strip()
            # Sort keys by length (longest first) to avoid conflicts (e.g., "ca team" before checking substrings)
            sorted_keys = sorted(color_map.items(), key=lambda x: len(x[0]), reverse=True)
            for key, col_hex in sorted_keys:
                if key in val_str:
                    try:
                        c = col_hex.lstrip('#')
                        r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
                        yiq = ((r*299)+(g*587)+(b*114))/1000
                        txt_col = '#fff' if yiq < 128 else '#000'
                    except:
                        txt_col = '#000'
                    return f"background-color: {col_hex}; color: {txt_col}; font-weight: bold;"
            return ""
        
        styled_df = filtered_df.style.map(style_cell)
        st.dataframe(styled_df, use_container_width=True, height=300)
        
        # ===== EDITABLE DATA TABLE =====
        
        # Show message if filters are active
        if search_text or any([
            st.session_state["roster_filters"]["alliance_filter"],
            st.session_state["roster_filters"]["tg_filter"],
            st.session_state["roster_filters"]["status_filter"],
            st.session_state["roster_filters"]["object_filter"],
        ]):
            st.info("ℹ️ Showing filtered results. Edit only the displayed members.")
            display_df = filtered_df
        else:
            display_df = st.session_state["edited_roster"]
        
        # Build column config with SelectboxColumn for known fields
        column_config = {}
        mapping = {
            "Alliance": getattr(KvK, "ALLIANCE_OPTS", KvK.get_column_options(roster_df, "Alliance")),
            "TG Level": getattr(KvK, "TG_OPTS", KvK.get_column_options(roster_df, "TG Level")),
            "Status": getattr(KvK, "STATUS_OPTS", KvK.get_column_options(roster_df, "Status")),
            "Availability": getattr(KvK, "AVAILABILITY_OPTS", KvK.get_column_options(roster_df, "Availability")),
            "Position": getattr(KvK, "POSITION_OPTS", KvK.get_column_options(roster_df, "Position")),
            "Object": getattr(KvK, "OBJECT_OPTS", KvK.get_column_options(roster_df, "Object")),
        }
        
        # Add SelectboxColumn for columns that have options
        for col_name, opts in mapping.items():
            if col_name in roster_df.columns and opts and len(opts) > 0:
                opts_clean = [str(o) for o in opts]
                column_config[col_name] = st.column_config.SelectboxColumn(label=col_name, options=opts_clean)
        
        # Display editable table
        edited_df = st.data_editor(
            display_df,
            use_container_width=True,
            num_rows="dynamic",
            key="roster_data_editor",
            hide_index=True,
            disabled=not st.session_state["roster_filters"]["edit_mode"],
            column_config=column_config if column_config else None,
        )
        
        # Update session state with edited data
        if st.session_state["roster_filters"]["edit_mode"]:
            # If showing filtered data, update only those rows in the full roster
            if display_df is not st.session_state["edited_roster"]:
                # Find and update matching rows
                for idx, filtered_row in edited_df.iterrows():
                    for full_idx, full_row in st.session_state["edited_roster"].iterrows():
                        if full_row["Name"] == filtered_row["Name"]:  # Match by name
                            st.session_state["edited_roster"].iloc[full_idx] = filtered_row
                            break
            else:
                # If showing all data, update directly
                st.session_state["edited_roster"] = edited_df.copy()
        
        # ===== SAVE CONTROLS =====
        st.markdown("---")
        col_save_orig, col_discard = st.columns([1.5, 1])
        
        with col_save_orig:
            if not st.session_state["roster_filters"]["edit_mode"]:
                st.button("💾 Save", disabled=True, key="save_original_btn", help="Enable Edit Mode to save")
            elif st.button("💾 Save", key="save_original_btn", help="Save back to KvK 2.xlsx"):
                success, message = save_roster_to_excel(
                    st.session_state["edited_roster"],
                    str(roster_file),
                    selected_sheet,
                    save_to_original=True
                )
                if success:
                    st.success(message)
                else:
                    st.error(message)
        
        with col_discard:
            if not st.session_state["roster_filters"]["edit_mode"]:
                st.button("↩️ Discard", disabled=True, key="discard_roster_btn", help="Enable Edit Mode to discard")
            elif st.button("↩️ Discard", key="discard_roster_btn"):
                st.session_state["edited_roster"] = roster_df.copy()
                st.info("Changes discarded.")
                st.rerun()
        
    except Exception as e:
        st.error(f"Error loading roster data: {str(e)}")


def render_object_indicators(roster_df: pd.DataFrame) -> None:
    """Render visual progress indicators for each combat Object.
    
    Displays progress bars with member counts and percentages for each Object.
    Shows: Castle 10/15, North 15/15, South 15/15, East 15/15, West 15/15, CA TEAM 30/30
    """
    st.markdown("### 🎯 Object Capacity Overview")
    
    # Define max capacity per object
    max_capacity = {
        "Castle": 15,
        "North": 15,
        "South": 15,
        "East": 15,
        "West": 15,
        "CA TEAM": 30
    }
    
    object_opts = getattr(KvK, "OBJECT_OPTS", list(max_capacity.keys()))
    
    # Create responsive columns based on screen size
    # On mobile: 1 column, on desktop: 2-3 columns
    cols_per_row = 1
    try:
        # This is a heuristic for mobile detection
        if st.session_state.get("screen_width", 1200) < 768:
            cols_per_row = 1
        elif st.session_state.get("screen_width", 1200) < 1200:
            cols_per_row = 2
        else:
            cols_per_row = 3
    except:
        cols_per_row = 2
    
    # Render indicators
    col_idx = 0
    cols = []
    
    for obj in object_opts:
        if col_idx % cols_per_row == 0:
            cols = st.columns(cols_per_row)
        
        with cols[col_idx % cols_per_row]:
            # Count members in this object
            obj_count = len(roster_df[
                (roster_df["Object"].astype(str).str.strip() == obj) & 
                (roster_df["Object"].astype(str).str.strip() != "")
            ])
            
            max_cap = max_capacity.get(obj, 15)
            pct = (obj_count / max_cap * 100) if max_cap > 0 else 0
            pct = min(pct, 100)  # Cap at 100%
            
            # Determine color based on capacity
            if pct >= 100:
                bar_color = "#28a745"  # Green
                status = "✅ FULL"
            elif pct >= 75:
                bar_color = "#20c997"  # Light green
                status = "⚠️ 75%+"
            elif pct >= 50:
                bar_color = "#ffc107"  # Yellow
                status = "📊 50%+"
            else:
                bar_color = "#ff6b6b"  # Red
                status = "📭 <50%"
            
            # Emoji for each object
            obj_emoji = {
                "Castle": "🏰",
                "North": "🗻",
                "South": "🌋",
                "East": "🏔️",
                "West": "⚔️",
                "CA TEAM": "👥"
            }
            emoji = obj_emoji.get(obj, "📍")
            
            # HTML for progress indicator
            html_content = f"""
            <div class="object-indicator">
                <div class="object-header">
                    <span>{emoji} {obj}</span>
                    <span style="color: #aaaaaa; font-size: 0.9em;">{status}</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {pct}%; background: linear-gradient(90deg, {bar_color}, {'#' + format(int(int(bar_color[1:], 16) * 1.1) % 0xFFFFFF, '06x')}); color: white;">
                        {int(pct)}%
                    </div>
                </div>
                <div class="progress-text">
                    {obj_count}/{max_cap} members
                </div>
            </div>
            """
            
            st.markdown(html_content, unsafe_allow_html=True)
        
        col_idx += 1


def render_object_distribution_tab() -> None:
    """Render Object Distribution tab with members grouped by Object"""
    st.subheader("Object Distribution")
    
    # Check if roster data is available in session state
    if "edited_roster" not in st.session_state:
        st.info("📋 Please open the Roster tab first to load roster data.")
        return
    
    roster_df = st.session_state.get("edited_roster", pd.DataFrame())
    if roster_df.empty:
        st.warning("No roster data available.")
        return
    
    # Show visual indicators first
    render_object_indicators(roster_df)
    
    st.markdown("---")
    st.markdown("### 📋 Detailed Member List")
    
    # Check if required columns exist
    required_cols = ["Name", "Position", "Object"]
    missing_cols = [col for col in required_cols if col not in roster_df.columns]
    if missing_cols:
        st.error(f"Missing columns in roster: {', '.join(missing_cols)}")
        return
    
    # Get Object options from KvK module
    object_opts = getattr(KvK, "OBJECT_OPTS", ["Castle", "North", "West", "East", "South", "CA TEAM"])
    
    # Group data by Object and display in expanders
    found_any = False
    for obj in object_opts:
        # Filter rows for this Object
        obj_df = roster_df[
            (roster_df["Object"].astype(str).str.strip() == obj) & 
            (roster_df["Object"].astype(str).str.strip() != "")
        ][["Name", "Position", "Object"]].reset_index(drop=True)
        
        if len(obj_df) > 0:
            found_any = True
            
            # Create expander with Object name and member count
            with st.expander(
                f"{obj} ({len(obj_df)} member{'s' if len(obj_df) != 1 else ''})",
                expanded=False
            ):
                # Display table
                st.dataframe(obj_df, use_container_width=True, hide_index=True)
    
    if not found_any:
        st.info("No data available yet. Members will appear here once assigned to Objects in the Roster tab.")


def render_member_details_for_turret(turret_name: str, roster_df: pd.DataFrame) -> pd.DataFrame:
    """
    Get members assigned to a specific turret/object.
    
    Args:
        turret_name: Object name (e.g., "North", "Castle")
        roster_df: Roster dataframe
    
    Returns:
        Filtered and formatted dataframe with Name, Position, Alliance columns, sorted by Position and Name
    """
    if roster_df.empty:
        return pd.DataFrame()
    
    # Filter by Object
    filtered = roster_df[
        (roster_df["Object"].astype(str).str.strip() == turret_name) & 
        (roster_df["Object"].astype(str).str.strip() != "")
    ].copy()
    
    # Select columns
    cols_to_keep = []
    if "Name" in filtered.columns:
        cols_to_keep.append("Name")
    if "Position" in filtered.columns:
        cols_to_keep.append("Position")
    if "Alliance" in filtered.columns:
        cols_to_keep.append("Alliance")
    
    if not cols_to_keep:
        return filtered[["Object"]].head(0)
    
    filtered = filtered[cols_to_keep].reset_index(drop=True)
    
    # Sort: Leader first, then alphabetically by name
    if "Position" in filtered.columns and "Name" in filtered.columns:
        filtered["_sort_position"] = filtered["Position"].apply(lambda x: 0 if str(x).strip() == "Leader" else 1)
        filtered = filtered.sort_values(["_sort_position", "Name"], na_position="last").drop("_sort_position", axis=1)
    elif "Name" in filtered.columns:
        filtered = filtered.sort_values("Name")
    
    return filtered.reset_index(drop=True)


def render_castle_map_tab() -> None:
    """Render interactive castle map with clickable turrets showing member assignments"""
    st.subheader("🗺️ Interactive Castle Map")
    
    # Check if roster data is available
    if "edited_roster" not in st.session_state:
        st.info("📋 Please open the Roster tab first to load roster data.")
        return
    
    roster_df = st.session_state.get("edited_roster", pd.DataFrame())
    if roster_df.empty:
        st.warning("No roster data available.")
        return
    
    # Initialize session state for selected turret
    if "selected_turret" not in st.session_state:
        st.session_state["selected_turret"] = "Castle"
    
    # Get object options and max capacities
    object_opts = getattr(KvK, "OBJECT_OPTS", ["Castle", "North", "West", "East", "South", "CA TEAM"])
    max_capacity = {
        "Castle": 15,
        "North": 15,
        "South": 15,
        "East": 15,
        "West": 15,
        "CA TEAM": 30
    }
    
    # Get color map
    color_map = getattr(KvK, "COLOR_MAP", {})
    
    def get_turret_color(turret_name: str) -> str:
        """Get hex color for turret from COLOR_MAP"""
        key = turret_name.lower()
        sorted_keys = sorted(color_map.items(), key=lambda x: len(x[0]), reverse=True)
        for k, v in sorted_keys:
            if k in key:
                return v
        return "#2f3f65"
    
    # Create main container
    st.markdown('<div class="castle-map-container">', unsafe_allow_html=True)
    
    # Render the map grid
    st.markdown('<div class="map-layout">', unsafe_allow_html=True)
    st.markdown('<div class="turrets-grid">', unsafe_allow_html=True)
    
    # Create columns for turret buttons (using raw HTML for better layout control)
    turret_data = [
        ("North", "🗻", "turret-north"),
        ("West", "🗻", "turret-west"),
        ("Castle", "🏰", "castle"),
        ("East", "🗻", "turret-east"),
        ("South", "🗻", "turret-south"),
    ]
    
    # Render turret buttons
    for turret_name, emoji, grid_class in turret_data:
        count = len(render_member_details_for_turret(turret_name, roster_df))
        capacity = max_capacity.get(turret_name, 15)
        color = get_turret_color(turret_name)
        is_selected = st.session_state["selected_turret"] == turret_name
        
        if turret_name == "Castle":
            # Special styling for castle
            if st.button(
                f"{emoji} {turret_name}\n{count}/{capacity}",
                key=f"btn_{turret_name}",
                use_container_width=False,
                help=f"Click to view {turret_name} members"
            ):
                st.session_state["selected_turret"] = turret_name
                st.rerun()
        else:
            # Turret buttons
            if st.button(
                f"{emoji}\n{turret_name}\n{count}/{capacity}",
                key=f"btn_{turret_name}",
                use_container_width=False,
                help=f"Click to view {turret_name} members"
            ):
                st.session_state["selected_turret"] = turret_name
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)  # close turrets-grid
    
    # Render CA TEAM section
    ca_count = len(render_member_details_for_turret("CA TEAM", roster_df))
    ca_capacity = max_capacity["CA TEAM"]
    
    if st.button(
        f"🎯 CA TEAM: {ca_count}/{ca_capacity}",
        key="btn_CA_TEAM",
        use_container_width=True,
        help="Click to view CA TEAM members"
    ):
        st.session_state["selected_turret"] = "CA TEAM"
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)  # close map-layout
    
    # Display selected turret's members
    st.markdown("---")
    selected = st.session_state["selected_turret"]
    selected_df = render_member_details_for_turret(selected, roster_df)
    selected_count = len(selected_df)
    selected_capacity = max_capacity.get(selected, 15)
    
    # Capacity badge color
    if selected_count >= selected_capacity:
        capacity_class = "capacity-critical"
        fill_percent = 100
        fill_color = "#dc3545"
    elif selected_count >= selected_capacity * 0.75:
        capacity_class = "capacity-warning"
        fill_percent = int((selected_count / selected_capacity) * 100)
        fill_color = "#ffc107"
    elif selected_count >= selected_capacity * 0.5:
        capacity_class = "capacity-ok"
        fill_percent = int((selected_count / selected_capacity) * 100)
        fill_color = "#ffc107"
    else:
        capacity_class = "capacity-ok"
        fill_percent = int((selected_count / selected_capacity) * 100)
        fill_color = "#28a745"
    
    emoji_map = {
        "Castle": "🏰",
        "North": "🗻",
        "South": "🗻",
        "East": "🗻",
        "West": "🗻",
        "CA TEAM": "🎯"
    }
    
    emoji = emoji_map.get(selected, "📍")
    
    # Create progress bar HTML
    progress_html = f'''
    <div class="member-list-container">
        <div class="member-list-header">
            {emoji} {selected} Members
            <span class="capacity-badge {capacity_class}">{selected_count}/{selected_capacity}</span>
        </div>
        <div class="progress-bar">
            <div class="progress-fill" style="width: {fill_percent}%; background: linear-gradient(90deg, {fill_color}, #20c997);">
                {fill_percent}%
            </div>
        </div>
    '''
    
    st.markdown(progress_html, unsafe_allow_html=True)
    
    if selected_df.empty:
        st.markdown('<div class="no-members-message">No members assigned to this location yet.</div>', unsafe_allow_html=True)
    else:
        # Display members in grid
        st.markdown('<div class="member-list-content">', unsafe_allow_html=True)
        for _, row in selected_df.iterrows():
            name = str(row.get("Name", "?")).strip()
            position = str(row.get("Position", "")).strip() if "Position" in row.index else ""
            alliance = str(row.get("Alliance", "")).strip() if "Alliance" in row.index else ""
            
            member_html = f'<div class="member-item"><div class="member-name">{name}</div>'
            if position or alliance:
                member_html += f'<div class="member-info">'
                if position:
                    member_html += f'{position}'
                if position and alliance:
                    member_html += ' • '
                if alliance:
                    member_html += f'{alliance}'
                member_html += f'</div>'
            member_html += f'</div>'
            st.markdown(member_html, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)  # close member-list-content
    
    st.markdown('</div>', unsafe_allow_html=True)  # close member-list-container
    st.markdown('</div>', unsafe_allow_html=True)  # close castle-map-container


def main() -> None:
    # Initialize session state
    if "roster_filters" not in st.session_state:
        st.session_state["roster_filters"] = {
            "name_search": "",
            "alliance_filter": [],
            "tg_filter": [],
            "status_filter": [],
            "object_filter": [],
            "edit_mode": False
        }
    if "edited_roster" not in st.session_state:
        st.session_state["edited_roster"] = pd.DataFrame()
    if "edited_roster_sheet" not in st.session_state:
        st.session_state["edited_roster_sheet"] = ""
    
    # Apply CSS
    inject_command_center_css()
    
    st.title("🏰 KvK Castle Battle Command Center")
    st.caption("Strategy-assisted battle orchestration based on wave funnel and command cadence.")

    uploaded = st.file_uploader("Optional: Upload KvK_Battle_Calculators (1).xlsx", type=["xlsx"])
    excel_data = load_excel_data(uploaded)
    if excel_data:
        st.success(f"Loaded {len(excel_data)} sheet(s): {', '.join(excel_data.keys())}")
    else:
        st.warning("Excel workbook not detected. Calculators still work with manual inputs.")

    tab1, tab2, tab3, tab4 = st.tabs(["🌊 Waves + Counter Rally", "📋 Roster", "🎯 Object Distribution", "🗺️ Castle Map"])

    with tab1:
        render_wave_and_timing_tab(excel_data)
    
    with tab2:
        render_roster_tab()
    
    with tab3:
        render_object_distribution_tab()
    
    with tab4:
        render_castle_map_tab()


if __name__ == "__main__":
    main()
