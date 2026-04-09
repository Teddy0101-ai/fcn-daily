import json
import math
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_FILE = ROOT / "raw" / "latest.xlsx"
DATA_DIR = ROOT / "data"
DICT_FILE = ROOT / "scripts" / "dictionary.json"

SHEET_MAP = {
    "今日重点": "highlight",
    "USD": "usd",
    "HKD": "hkd",
}

def load_dictionary():
    with open(DICT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def format_date(v):
    if pd.isna(v) or v == "":
        return ""
    try:
        ts = pd.to_datetime(v)
        return ts.strftime("%Y/%m/%d")
    except Exception:
        return str(v)

def file_date_text(path: Path):
    m = re.search(r"(\d{2})(\d{2})(\d{4})", path.name)
    if m:
        dd, mm, yyyy = m.groups()
        return f"{yyyy}/{mm}/{dd}"
    return ""

def format_pct(v):
    if pd.isna(v) or v == "":
        return "-"
    x = float(v)
    if abs(x - round(x)) < 1e-9:
        return f"{int(round(x))}%"
    s = f"{x:.2f}".rstrip("0").rstrip(".")
    return f"{s}%"

def clean_text(v):
    if pd.isna(v):
        return ""
    return str(v).strip()

def split_codes(s):
    return [part.strip() for part in clean_text(s).split("+") if part.strip()]

def build_ticker_map(xls):
    df = pd.read_excel(xls, sheet_name="Tickers")
    cols = list(df.columns)
    mapping = {}
    if len(cols) >= 2:
        # First row is likely stored as headers, so include headers as data
        mapping[clean_text(cols[0])] = clean_text(cols[1])
        for _, row in df.iterrows():
            code = clean_text(row[cols[0]])
            name = clean_text(row[cols[1]])
            if code:
                mapping[code] = name
    return mapping

def map_name_from_codes(code_str, ticker_map, dictionary):
    codes = split_codes(code_str)
    names = []
    for code in codes:
        name = dictionary["codes_to_cn"].get(code) or ticker_map.get(code) or code
        names.append(name)
    return " + ".join(names)

def map_underlying_name(section, row, ticker_map, dictionary):
    if section == "highlight":
        raw = clean_text(row.get("Underlying Name (Translated)", ""))
        if raw:
            return raw
        return map_name_from_codes(row.get("Underlying (BBG) Indicative", ""), ticker_map, dictionary)

    raw = clean_text(row.get("Underlying Name", ""))
    if raw:
        return raw
    return map_name_from_codes(row.get("Underlying (BBG) Indicative", ""), ticker_map, dictionary)

def map_ko_type(v, dictionary):
    raw = clean_text(v)
    return dictionary["ko_type"].get(raw, raw)

def map_ki_type(v, dictionary):
    raw = clean_text(v)
    if not raw:
        return "无"
    return dictionary["ki_type"].get(raw, raw)

def parse_lock_period(v):
    if pd.isna(v) or v == "":
        return ""
    try:
        return f"{int(float(v))}M"
    except Exception:
        return clean_text(v)

def numeric_or_none(v):
    if pd.isna(v) or v == "":
        return None
    try:
        return float(v)
    except Exception:
        return None

def build_underlying_detail_display(name_cn, bbg):
    if not bbg:
        return name_cn
    return f"{name_cn}（{bbg}）"

def quote_time_from_row(row, fallback_date):
    strike_date = format_date(row.get("Strike Date", ""))
    if strike_date:
        return f"{strike_date} 08:51:00"
    if fallback_date:
        return f"{fallback_date} 08:51:00"
    return ""

def normalize_row(section, row, display_rank, ticker_map, dictionary, fallback_date):
    underlying_name_cn = map_underlying_name(section, row, ticker_map, dictionary)
    product = clean_text(row.get("Product", ""))
    ki_pct = numeric_or_none(row.get("KI %"))
    record = {
        "id": clean_text(row.get("Quote ID", "")),
        "section": section,
        "currency": clean_text(row.get("CCY", "")),
        "product_type": product,
        "product_type_en": dictionary["product_type_en"].get(product, product),
        "tenor": clean_text(row.get("Tenor", "")),
        "strike_date": format_date(row.get("Strike Date", "")),
        "issue_date": format_date(row.get("Issue Date", "")),
        "final_valuation_date": format_date(row.get("Final Valuation Date", "")),
        "maturity_date": format_date(row.get("Maturity Date", "")),
        "underlying_reuters": clean_text(row.get("Underlying (Reuters)", "")),
        "underlying_bbg": clean_text(row.get("Underlying (BBG) Indicative", "")),
        "underlying_name_raw": clean_text(row.get("Underlying Name (Translated)", "")) or clean_text(row.get("Underlying Name", "")),
        "underlying_name_cn": underlying_name_cn,
        "underlying_display": underlying_name_cn,
        "underlying_detail_display": build_underlying_detail_display(underlying_name_cn, clean_text(row.get("Underlying (BBG) Indicative", ""))),
        "strike_pct": numeric_or_none(row.get("Strike %")),
        "strike_display": format_pct(row.get("Strike %")),
        "coupon_pa_pct": numeric_or_none(row.get("Coupon % p.a.")),
        "coupon_display": format_pct(row.get("Coupon % p.a.")),
        "coupon_frequency": clean_text(row.get("Coupon Frequency", "")),
        "ko_pct": numeric_or_none(row.get("KO %")),
        "ko_display": format_pct(row.get("KO %")),
        "ko_type_raw": clean_text(row.get("KO Type", "")),
        "ko_type_cn": map_ko_type(row.get("KO Type", ""), dictionary),
        "first_callable_eop_months": numeric_or_none(row.get("First Callable End of Period")),
        "lock_period": parse_lock_period(row.get("First Callable End of Period")),
        "ki_pct": ki_pct,
        "ki_display": "-" if ki_pct is None else format_pct(ki_pct),
        "ki_type_raw": clean_text(row.get("KI Type", "")),
        "ki_type_cn": map_ki_type(row.get("KI Type", ""), dictionary),
        "min_max_notional": clean_text(row.get("Min/Max Notional", "")),
        "issuer": clean_text(row.get("Issuer", "")),
        "interbank_price_pct": numeric_or_none(row.get("Interbank Price %")),
        "quote_time": quote_time_from_row(row, fallback_date),
        "display_rank": display_rank,
    }
    return record

def main():
    if not RAW_FILE.exists():
        raise FileNotFoundError(f"Missing input file: {RAW_FILE}")

    dictionary = load_dictionary()
    xls = pd.ExcelFile(RAW_FILE)
    ticker_map = build_ticker_map(xls)
    fallback_date = file_date_text(RAW_FILE)

    all_details = {}
    meta_dates = []
    meta_quote_times = []
    outputs = {}

    for sheet_name, section in SHEET_MAP.items():
        df = pd.read_excel(RAW_FILE, sheet_name=sheet_name)
        # keep only rows with Quote ID
        df = df[df["Quote ID"].notna()].copy()
        records = []
        for idx, (_, row) in enumerate(df.iterrows(), start=1):
            rec = normalize_row(section, row, idx, ticker_map, dictionary, fallback_date)
            records.append(rec)
            all_details[rec["id"]] = rec
            if rec["strike_date"]:
                meta_dates.append(rec["strike_date"])
            if rec["quote_time"]:
                meta_quote_times.append(rec["quote_time"])
        outputs[section] = records

    update_date = max(meta_dates) if meta_dates else fallback_date
    quote_time = max(meta_quote_times) if meta_quote_times else (f"{fallback_date} 08:51:00" if fallback_date else "")

    meta = {
        "site_title_cn": "热门选品",
        "detail_title_cn": "选品详情",
        "product_type_en_default": "Fixed Coupon Note",
        "advisor_name": "Ryan Yi 易俊融",
        "advisor_avatar_text": "点击此处\n上传个人头像",
        "qr_caption": "长按扫码 咨询申购",
        "disclaimer_cn": f"数据截至{update_date}，本页报价仅供参考，欲知详情可联系相关工作人员。" if update_date else "本页报价仅供参考，欲知详情可联系相关工作人员。",
        "update_date": update_date,
        "quote_time": quote_time,
        "tabs": [
            {"key": "highlight", "label": "今日重点"},
            {"key": "usd", "label": "USD"},
            {"key": "hkd", "label": "HKD"}
        ],
        "columns": [
            {"key": "underlying_display", "label": "挂钩标的"},
            {"key": "ko_display", "label": "敲出价格"},
            {"key": "strike_display", "label": "执行价格"},
            {"key": "tenor", "label": "期限"},
            {"key": "coupon_display", "label": "票息(年化)"}
        ]
    }

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "highlight.json").write_text(json.dumps(outputs["highlight"], ensure_ascii=False, indent=2), encoding="utf-8")
    (DATA_DIR / "usd.json").write_text(json.dumps(outputs["usd"], ensure_ascii=False, indent=2), encoding="utf-8")
    (DATA_DIR / "hkd.json").write_text(json.dumps(outputs["hkd"], ensure_ascii=False, indent=2), encoding="utf-8")
    (DATA_DIR / "details.json").write_text(json.dumps(all_details, ensure_ascii=False, indent=2), encoding="utf-8")
    (DATA_DIR / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

if __name__ == "__main__":
    main()
