"""Phase 1: download daily NASA POWER data for Batac City.
See docs/project_plan.md §4.7.

Run from the project root:  python3 -m src.fetch_nasa_power [start_year end_year]
Writes data/raw/nasa_power_daily_<site>.csv
"""
import csv
import json
import sys
import urllib.request
from pathlib import Path

SITES = {
    "batac": (18.055, 120.566),
}
PARAMS = ["ALLSKY_KT", "ALLSKY_SFC_SW_DWN", "TOA_SW_DWN", "T2M", "T2M_MAX", "T2M_MIN"]
URL = ("https://power.larc.nasa.gov/api/temporal/daily/point"
       "?parameters={p}&community=RE&latitude={lat}&longitude={lon}"
       "&start={start}0101&end={end}1231&format=JSON&time-standard=LST")
RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
FILL = -999.0


def fetch(site, start, end):
    lat, lon = SITES[site]
    url = URL.format(p=",".join(PARAMS), lat=lat, lon=lon, start=start, end=end)
    with urllib.request.urlopen(url, timeout=180) as r:
        series = json.load(r)["properties"]["parameter"]
    RAW.mkdir(parents=True, exist_ok=True)
    out = RAW / f"nasa_power_daily_{site}.csv"
    dates = sorted(series[PARAMS[0]])
    with out.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date"] + PARAMS)
        for d in dates:
            vals = [series[p].get(d, FILL) for p in PARAMS]
            w.writerow([f"{d[:4]}-{d[4:6]}-{d[6:]}"] + ["" if v == FILL else v for v in vals])
    missing = sum(series["ALLSKY_KT"].get(d, FILL) == FILL for d in dates)
    print(f"{site}: {len(dates)} days ({dates[0]}–{dates[-1]}), "
          f"{missing} missing kt → {out}")


if __name__ == "__main__":
    start, end = (sys.argv[1], sys.argv[2]) if len(sys.argv) > 2 else ("2001", "2024")
    for s in SITES:
        fetch(s, start, end)
