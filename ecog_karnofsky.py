#!/usr/bin/env python3
"""ECOG–Karnofsky performance-status crosswalk.

Uses the illustrative comparison published by ECOG-ACRIN:
https://ecog-acrin.org/resources/ecog-performance-status/

A crosswalk is not a validated patient-level conversion or a clinical
eligibility determination. Assess the patient's actual functional status.
"""
import argparse
import csv
import json
import math
import os
import re
import tempfile
from pathlib import Path

ECOG_TO_KPS = {
    0: (90, 100),
    1: (70, 80),
    2: (50, 60),
    3: (30, 40),
    4: (10, 20),
    5: (0,),
}
ECOG_DESCRIPTIONS = {
    0: "Fully active; no restriction on pre-disease performance",
    1: "Ambulatory; restricted in strenuous activity; light work possible",
    2: "Self-care possible; unable to work; active >50% of waking hours",
    3: "Limited self-care; in bed or chair >50% of waking hours",
    4: "Completely disabled; totally confined to bed or chair",
    5: "Dead",
}
MAPPING_NOTE = (
    "Illustrative ECOG-ACRIN comparison, not an exact or reversible "
    "patient-level conversion. Do not use alone to determine trial eligibility."
)
REFERENCE_URL = "https://ecog-acrin.org/resources/ecog-performance-status/"


def _whole_number(value, label):
    """Accept integers or integer-valued decimal inputs, never NaN/Inf."""
    if isinstance(value, bool) or value is None:
        raise ValueError(f"{label} must be a whole number")
    if isinstance(value, str):
        if not re.fullmatch(r"[0-9]+(?:\.0+)?", value.strip()):
            raise ValueError(f"{label} must be a whole number")
        value = float(value.strip())
    if not isinstance(value, (int, float)) or not math.isfinite(value) or not float(value).is_integer():
        raise ValueError(f"{label} must be a finite whole number")
    return int(value)


def map_ecog_to_kps(ecog):
    """Return all KPS values grouped with a given ECOG grade."""
    grade = _whole_number(ecog, "ECOG")
    if grade not in ECOG_TO_KPS:
        raise ValueError("ECOG must be between 0 and 5")
    values = ECOG_TO_KPS[grade]
    return {
        "input_scale": "ECOG", "input_score": grade,
        "ecog": grade, "kps_values": list(values),
        "kps_min": min(values), "kps_max": max(values),
        "ecog_description": ECOG_DESCRIPTIONS[grade],
        "mapping_note": MAPPING_NOTE, "reference": REFERENCE_URL,
    }


def map_kps_to_ecog(kps):
    """Return the ECOG comparison grade for a discrete KPS score."""
    score = _whole_number(kps, "KPS")
    if score < 0 or score > 100 or score % 10:
        raise ValueError("KPS must be 0–100 in increments of 10")
    grade = next(key for key, values in ECOG_TO_KPS.items() if score in values)
    result = map_ecog_to_kps(grade)
    result.update(input_scale="KPS", input_score=score)
    return result


def calculate_metrics(*, ecog=None, kps=None):
    """Compatibility entry point for explicit, validated ECOG/KPS mapping."""
    if (ecog is None) == (kps is None):
        raise ValueError("Provide exactly one of ecog or kps")
    return map_ecog_to_kps(ecog) if ecog is not None else map_kps_to_ecog(kps)


def _safe_cell(value):
    """Avoid CSV formula execution in spreadsheets for passthrough fields."""
    if value is None:
        return ""
    text = str(value)
    if text.lstrip().startswith(("=", "+", "-", "@", "\t", "\r", "\n")):
        return "'" + text
    return text


def process_batch(input_csv, output_csv):
    """Convert a CSV with an ecog or kps column; write atomically.

    Rows must provide exactly one scale. Non-scale columns are retained.
    """
    src, dst = Path(input_csv).resolve(), Path(output_csv).resolve()
    if not src.is_file():
        raise FileNotFoundError(f"Input CSV not found: {src}")
    if src == dst:
        raise ValueError("Output must be a different file from input")
    if not dst.parent.is_dir():
        raise FileNotFoundError(f"Output directory does not exist: {dst.parent}")
    with src.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        if not fields:
            raise ValueError("Input CSV has no headers")
        if len(set(fields)) != len(fields):
            raise ValueError("Input CSV has duplicate headers")
        if not any(key in fields for key in ("ecog", "kps")):
            raise ValueError("Input CSV must have an ecog or kps column")
        extra = ["mapped_ecog", "mapped_kps_values", "mapped_kps_min", "mapped_kps_max"]
        if any(key in fields for key in extra):
            raise ValueError("Input CSV contains reserved output column names")
        output_rows = []
        for line, row in enumerate(reader, start=2):
            if None in row:
                raise ValueError(f"Line {line}: more fields than headers")
            ecog, kps = (row.get("ecog") or "").strip(), (row.get("kps") or "").strip()
            try:
                result = calculate_metrics(
                    ecog=ecog if ecog else None, kps=kps if kps else None
                )
            except ValueError as exc:
                raise ValueError(f"Line {line}: {exc}") from exc
            safe_row = {name: _safe_cell(row[name]) for name in fields}
            safe_row.update(
                mapped_ecog=result["ecog"],
                mapped_kps_values="|".join(map(str, result["kps_values"])),
                mapped_kps_min=result["kps_min"],
                mapped_kps_max=result["kps_max"],
            )
            output_rows.append(safe_row)

    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="", dir=dst.parent,
            prefix=".ecog-kps-", suffix=".csv", delete=False
        ) as handle:
            temporary = Path(handle.name)
            writer = csv.DictWriter(handle, fieldnames=fields + extra)
            writer.writeheader()
            writer.writerows(output_rows)
        os.replace(temporary, dst)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
    print(f"Processed {len(output_rows)} records -> {dst}")
    return len(output_rows)


def main(argv=None):
    parser = argparse.ArgumentParser(description="ECOG/Karnofsky comparison tool")
    sub = parser.add_subparsers(dest="command", required=True)
    single = sub.add_parser("single", help="Compare one ECOG or KPS score")
    scale = single.add_mutually_exclusive_group(required=True)
    scale.add_argument("--ecog", help="ECOG grade, 0–5")
    scale.add_argument("--kps", help="Karnofsky score, 0–100 in steps of 10")
    batch = sub.add_parser("batch", help="Compare rows in a CSV")
    batch.add_argument("-i", "--input", required=True)
    batch.add_argument("-o", "--output", default="results.csv")
    args = parser.parse_args(argv)
    try:
        if args.command == "single":
            print(json.dumps(calculate_metrics(ecog=args.ecog, kps=args.kps), indent=2))
        else:
            process_batch(args.input, args.output)
    except (ValueError, FileNotFoundError, OSError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
