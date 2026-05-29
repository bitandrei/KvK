from pathlib import Path
import pandas as pd

# Canonical option lists used by the app
ALLIANCE_OPTS = ["TFR", "TNS", "EVA", "RAW", "DEU"]
TG_OPTS = ["TG1", "TG2", "TG3", "TG4", "TG5", "TG6", "TG7", "TG8"]
STATUS_OPTS = ["Active", "Inactive", "Part-Time"]
AVAILABILITY_OPTS = ["Yes", "No"]
POSITION_OPTS = ["Leader", "Joiner"]
OBJECT_OPTS = ["Castle", "Nord", "West", "East", "South", "CA TEAM"]

# Color map (normalized keys are matched against lower-cased cell text)
COLOR_MAP = {
    "active": "#28a745",
    "yes": "#28a745",
    "castle": "#28a745",
    "leader": "#28a745",
    "inactive": "#dc3545",
    "no": "#dc3545",
    "joiner": "#d4af37",
    "nord": "#007bff",
    "west": "#fd7e14",
    "south": "#6f42c1",
    "east": "#50C878",
    "ca team": "#ff6b6b",
}


def get_column_options(df: pd.DataFrame, column: str) -> list:
    """Return sorted unique string options for a dataframe column."""
    if df is None or column not in df.columns:
        return []
    vals = df[column].dropna().unique().tolist()
    return sorted([str(v) for v in vals])


def get_color_for_value(value) -> str | None:
    """Return a hex color for a value based on COLOR_MAP, or None if no match.

    Matching is case-insensitive and checks whether any key is a substring
    of the lower-cased cell text.
    """
    if value is None:
        return None
    s = str(value).strip().lower()
    if not s:
        return None
    for key, color in COLOR_MAP.items():
        if key in s:
            return color
    return None


def roster_exists(path: str | Path) -> bool:
    return Path(path).exists()


def list_sheets(path: str | Path) -> list:
    p = Path(path)
    if not p.exists():
        return []
    xls = pd.ExcelFile(p)
    return xls.sheet_names


def read_roster(path: str | Path, sheet_name: str) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        return pd.DataFrame()
    return pd.read_excel(p, sheet_name=sheet_name)


def save_roster(path: str | Path, df: pd.DataFrame, sheet_name: str) -> None:
    p = Path(path)
    # This is a thin wrapper - app.py uses its own save helper to preserve sheets
    df.to_excel(p, sheet_name=sheet_name, index=False)
