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
        
        # ===== STYLED PREVIEW WITH COLORS =====
        color_map = getattr(KvK, "COLOR_MAP", {})
        
        def style_cell(val):
            """Apply COLOR_MAP styling to cell value"""
            if pd.isna(val) or val == "":
                return ""
            val_str = str(val).lower().strip()
            for key, col_hex in color_map.items():
                if key.lower() == val_str:
                    try:
                        c = col_hex.lstrip('#')
                        r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
                        yiq = ((r*299)+(g*587)+(b*114))/1000
                        txt_col = '#fff' if yiq < 128 else '#000'
                    except:
                        txt_col = '#000'
                    return f"background-color: {col_hex}; color: {txt_col}; font-weight: bold;"
            return ""
        
        styled_df = st.session_state["edited_roster"].style.applymap(style_cell)
        st.dataframe(styled_df, use_container_width=True, height=300)
        
        # ===== EDITABLE DATA TABLE =====
        
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
            st.session_state["edited_roster"],
            use_container_width=True,
            num_rows="dynamic",
            key="roster_data_editor",
            hide_index=True,
            column_config=column_config if column_config else None,
        )
        
        # Update session state with edited data
        st.session_state["edited_roster"] = edited_df.copy()
        
        # ===== SAVE CONTROLS =====
        st.markdown("---")
        col_save_orig, col_discard = st.columns([1.5, 1])
        
        with col_save_orig:
            if st.button("💾 Save", key="save_original_btn", help="Save back to KvK 2.xlsx"):
                success, message = save_roster_to_excel(
                    edited_df,
                    str(roster_file),
                    selected_sheet,
                    save_to_original=True
                )
                if success:
                    st.success(message)
                else:
                    st.error(message)
        
        with col_discard:
            if st.button("↩️ Discard", key="discard_roster_btn"):
                st.session_state["edited_roster"] = roster_df.copy()
                st.info("Changes discarded.")
                st.rerun()
        
    except Exception as e:
        st.error(f"Error loading roster data: {str(e)}")


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
    
    # Check if required columns exist
    required_cols = ["Name", "Position", "Object"]
    missing_cols = [col for col in required_cols if col not in roster_df.columns]
    if missing_cols:
        st.error(f"Missing columns in roster: {', '.join(missing_cols)}")
        return
    
    # Get Object options from KvK module
    object_opts = getattr(KvK, "OBJECT_OPTS", ["Castle", "Nord", "West", "East", "South", "CA"])
    
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


def main() -> None:
    inject_command_center_css()
    # Sidebar removed per user request

    st.title("KvK Castle Battle Command Center")
    st.caption("Strategy-assisted battle orchestration based on wave funnel and command cadence.")

    uploaded = st.file_uploader("Optional: Upload KvK_Battle_Calculators (1).xlsx", type=["xlsx"])
    excel_data = load_excel_data(uploaded)
    if excel_data:
        st.success(f"Loaded {len(excel_data)} sheet(s): {', '.join(excel_data.keys())}")
    else:
        st.warning("Excel workbook not detected. Calculators still work with manual inputs.")

    tab1, tab2, tab3 = st.tabs(["Waves + Counter Rally", "Roster", "Object Distribution"])

    with tab1:
        render_wave_and_timing_tab(excel_data)
    
    with tab2:
        render_roster_tab()
    
    with tab3:
        render_object_distribution_tab()


if __name__ == "__main__":
    main()
