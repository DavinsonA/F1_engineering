import pandas as pd

from src.ingestion.openf1_client import LiveSessionBlocked, OpenF1Client
from src.utils.paths import BRONZE

CATALOG_ENDPOINTS = ["meetings", "drivers", "championship_drivers"]
SESSION_ENDPOINTS = ["laps", "pit", "stints", "weather", "race_control", "session_result", "team_radio"]


def _save(data, path):
    df = pd.DataFrame(data)
    obj_cols = df.select_dtypes(include="object").columns
    df[obj_cols] = df[obj_cols].astype("string")
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


def extract_catalog(client, endpoint):
    data = client.get(endpoint)
    _save(data, BRONZE / endpoint / "data.parquet")
    return data


def extract_session(client, endpoint, session_key, year):
    out = BRONZE / endpoint / f"year={year}" / f"session_key={session_key}" / "data.parquet"
    if out.exists():
        return False
    data = client.get(endpoint, params={"session_key": session_key})
    _save(data, out)
    return True


def run(years=None):
    try:
        with OpenF1Client() as client:
            for endpoint in CATALOG_ENDPOINTS:
                data = extract_catalog(client, endpoint)
                print(f"[catalog] {endpoint}: {len(data)} filas")

            sessions = pd.DataFrame(extract_catalog(client, "sessions"))
            print(f"[catalog] sessions: {len(sessions)} filas")

            if years:
                sessions = sessions[sessions["year"].isin(years)]

            for row in sessions.itertuples():
                print(f"[session {row.session_key}] year={row.year}")
                for endpoint in SESSION_ENDPOINTS:
                    extract_session(client, endpoint, row.session_key, row.year)
    except LiveSessionBlocked as exc:
        print(f"API bloqueada por sesión en vivo: {exc}")
        print("Vuelve a ejecutar cuando termine la sesión.")
