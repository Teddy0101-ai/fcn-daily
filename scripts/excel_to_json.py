import json
import math
import re
from pathlib import Path
from typing import Dict, Any, List, Optional

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "raw"
DATA_DIR = ROOT / "data"
DICT_FILE = ROOT / "scripts" / "dictionary.json"

# Match: HKD USD Daily Run 10042026.xlsx
RAW_FILE_PATTERN = re.compile(
    r"^HKD USD Daily Run (\d{2})(\d{2})(\d{4})\.xlsx$",
    re.IGNORECASE
)

SHEET_MAP = {
    "今日重点": "highlight",
    "USD": "usd",
    "HKD": "hkd",
}


def get_latest_raw_file() -> Path:
    candidates = []

    for path in RAW_DIR.glob("*.xlsx"):
        m = RAW_FILE_PATTERN.match(path.name)
        if not m:
            continue
        dd, mm, yyyy = m.groups()
        sort_key = f"{yyyy}{mm}{dd}"
        candidates.append((sort_key, path))

    if not candidates:
        raise FileNotFoundError(
            f"No matching Excel file found in {RAW_DIR}. "
            f"Expected format like: HKD USD Daily Run 10042026.xlsx"
        )

    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


def ensure_dirs():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_dictionary() -> Dict[str, Any]:
    if DICT_FILE.exists():
        with open(DICT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def clean_str(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    return str(value).strip()


def is_blank(value: Any) -> bool:
    return clean_str(value) == ""


def normalize_percent(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None

    s = clean_str(value)
    if not s:
        return None

    s = s.replace("%", "").replace(",", "").strip()

    try:
        num = float(s)
    except ValueError:
        return None

    return num


def format_percent(value: Optional[float]) -> str:
    if value is None:
        return "-"
    if abs(value - round(value)) < 1e-9:
        return f"{int(round(value))}%"
    return f"{value:.2f}%".rstrip("0").rstrip(".") + "%"


def normalize_date(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""

    if isinstance(value, pd.Timestamp):
        return value.strftime("%Y/%m/%d")

    s = clean_str(value)
    if not s:
        return ""

    parsed = pd.to_datetime(s, errors="coerce", dayfirst=False)
    if pd.isna(parsed):
        return s
    return parsed.strftime("%Y/%m/%d")


def file_date_text(path: Path) -> str:
    m = RAW_FILE_PATTERN.match(path.name)
    if not m:
        return ""
    dd, mm, yyyy = m.groups()
    return f"{yyyy}/{mm}/{dd}"


def build_ticker_map(xls: pd.ExcelFile) -> Dict[str, str]:
    ticker_map: Dict[str, str] = {}

    if "Tickers" not in xls.sheet_names:
        return ticker_map

    df = pd.read_excel(xls, sheet_name="Tickers")

    if df.empty:
        return ticker_map

    cols = list(df.columns)
    if len(cols) < 2:
        return ticker_map

    code_col = cols[0]
    name_col = cols[1]

    for _, row in df.iterrows():
        code = clean_str(row.get(code_col))
        name = clean_str(row.get(name_col))
        if code and name:
            ticker_map[code] = name

    return ticker_map


def map_ko_type(raw: str) -> str:
    raw = clean_str(raw).lower()

    if raw in {"daily close memory", "daily memory"}:
        return "记忆型每日"
    if raw in {"daily close", "daily"}:
        return "每日"
    return clean_str(raw) or "-"


def map_ki_type(raw: str) -> str:
    raw_clean = clean_str(raw).lower()
    if raw_clean in {"", "n/a", "na", "none"}:
        return "无"
    return clean_str(raw)


def lock_period_from_eop(value: Any) -> str:
    s = clean_str(value)
    if not s:
        return "-"
    try:
        num = int(float(s))
        return f"{num}M"
    except Exception:
        return s


def split_codes(text: str) -> List[str]:
    if not text:
        return []
    return [x.strip() for x in text.split("+") if x.strip()]


def join_cn_names_from_codes(code_text: str, ticker_map: Dict[str, str]) -> str:
    codes = split_codes(code_text)
    if not codes:
        return ""

    names = []
    for code in codes:
        names.append(ticker_map.get(code, code))
    return " + ".join(names)


def resolve_underlying_name(
    section: str,
    row: pd.Series,
    ticker_map: Dict[str, str]
) -> str:
    if section == "highlight":
        translated = clean_str(row.get("Underlying Name (Translated)"))
        if translated:
            return translated

    name_raw = clean_str(row.get("Underlying Name"))
    if name_raw:
        return name_raw

    bbg = clean_str(row.get("Underlying (BBG) Indicative"))
    mapped = join_cn_names_from_codes(bbg, ticker_map)
    if mapped:
        return mapped

    return bbg or "-"


def build_underlying_detail_display(name_cn: str, bbg: str) -> str:
    if not name_cn:
        return bbg or "-"
    if not bbg:
        return name_cn
    return f"{name_cn}（{bbg}）"


def normalize_row(
    section: str,
    row: pd.Series,
    display_rank: int,
    ticker_map: Dict[str, str],
    fallback_date: str,
) -> Dict[str, Any]:
    product_type = clean_str(row.get("Product")) or "FCN"
    currency = clean_str(row.get("CCY"))
    tenor = clean_str(row.get("Tenor"))
    strike_date = normalize_date(row.get("Strike Date")) or fallback_date
    issue_date = normalize_date(row.get("Issue Date"))
    final_valuation_date = normalize_date(row.get("Final Valuation Date"))
    maturity_date = normalize_date(row.get("Maturity Date"))

    underlying_reuters = clean_str(row.get("Underlying (Reuters)"))
    underlying_bbg = clean_str(row.get("Underlying (BBG) Indicative"))
    underlying_display = resolve_underlying_name(section, row, ticker_map)

    strike_pct = normalize_percent(row.get("Strike %"))
    coupon_pa_pct = normalize_percent(row.get("Coupon % p.a."))
    ko_pct = normalize_percent(row.get("KO %"))
    ki_pct = normalize_percent(row.get("KI %"))
    interbank_price_pct = normalize_percent(row.get("Interbank Price %"))

    ko_type_raw = clean_str(row.get("KO Type"))
    ki_type_raw = clean_str(row.get("KI Type"))
    first_callable_eop = row.get("First Callable End of Period")

    quote_time = f"{strike_date} 08:51:00" if strike_date else ""

    rec = {
        "id": clean_str(row.get("Quote ID")),
        "section": section,
        "currency": currency,
        "product_type": product_type,
        "tenor": tenor,
        "strike_date": strike_date,
        "issue_date": issue_date,
        "final_valuation_date": final_valuation_date,
        "maturity_date": maturity_date,
        "underlying_reuters": underlying_reuters,
        "underlying_bbg": underlying_bbg,
        "underlying_name_raw": underlying_display,
        "underlying_name_cn": underlying_display,
        "underlying_display": underlying_display,
        "underlying_detail_display": build_underlying_detail_display(
            underlying_display, underlying_bbg
        ),
        "strike_pct": strike_pct,
        "strike_display": format_percent(strike_pct),
        "coupon_pa_pct": coupon_pa_pct,
        "coupon_display": format_percent(coupon_pa_pct),
        "coupon_frequency": clean_str(row.get("Coupon Frequency")),
        "ko_pct": ko_pct,
        "ko_display": format_percent(ko_pct),
        "ko_type_raw": ko_type_raw,
        "ko_type_cn": map_ko_type(ko_type_raw),
        "first_callable_eop_months": clean_str(first_callable_eop),
        "lock_period": lock_period_from_eop(first_callable_eop),
        "ki_pct": ki_pct,
        "ki_display": format_percent(ki_pct) if ki_pct is not None else "-",
        "ki_type_raw": ki_type_raw,
        "ki_type_cn": map_ki_type(ki_type_raw),
        "min_max_notional": clean_str(row.get("Min/Max Notional")),
        "issuer": clean_str(row.get("Issuer")),
        "interbank_price_pct": interbank_price_pct,
        "quote_time": quote_time,
        "display_rank": display_rank,
    }

    return rec


def write_json(path: Path, data: Any):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    ensure_dirs()

    raw_file = get_latest_raw_file()
    fallback_date = file_date_text(raw_file)

    dictionary = load_dictionary()  # kept for future use
    _ = dictionary

    xls = pd.ExcelFile(raw_file)
    ticker_map = build_ticker_map(xls)

    all_details: Dict[str, Dict[str, Any]] = {}
    outputs: Dict[str, List[Dict[str, Any]]] = {
        "highlight": [],
        "usd": [],
        "hkd": [],
    }

    for sheet_name, section in SHEET_MAP.items():
        if sheet_name not in xls.sheet_names:
            continue

        df = pd.read_excel(raw_file, sheet_name=sheet_name)

        if "Quote ID" not in df.columns:
            continue

        df = df[df["Quote ID"].notna()].copy()

        records = []
        for idx, (_, row) in enumerate(df.iterrows(), start=1):
            rec = normalize_row(section, row, idx, ticker_map, fallback_date)
            if not rec["id"]:
                continue
            records.append(rec)
            all_details[rec["id"]] = rec

        outputs[section] = records

    update_date = fallback_date
    quote_time = f"{fallback_date} 08:51:00" if fallback_date else ""

    meta = {
        "site_title_cn": "热门选品",
        "detail_title_cn": "选品详情",
        "product_type_en": "Fixed Coupon Note",
        "advisor_name": "Ryan Yi 易俊融",
        "disclaimer_cn": f"数据截至{update_date}，本页报价仅供参考，欲知详情可联系相关工作人员。" if update_date else "本页报价仅供参考，欲知详情可联系相关工作人员。",
        "update_date": update_date,
        "quote_time": quote_time,
        "source_file": raw_file.name,
    }

    write_json(DATA_DIR / "highlight.json", outputs["highlight"])
    write_json(DATA_DIR / "usd.json", outputs["usd"])
    write_json(DATA_DIR / "hkd.json", outputs["hkd"])
    write_json(DATA_DIR / "details.json", all_details)
    write_json(DATA_DIR / "meta.json", meta)

    print(f"Using latest raw file: {raw_file.name}")
    print("JSON files generated successfully.")


if __name__ == "__main__":
    main()
