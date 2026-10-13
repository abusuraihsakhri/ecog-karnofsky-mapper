"""Smoke tests for both public Python entry points."""
import csv
import pytest
from ecog_karnofsky import calculate_metrics, process_batch


def test_mapping_by_ecog_and_kps():
    assert calculate_metrics(ecog=0)["kps_values"] == [90, 100]
    assert calculate_metrics(kps=30)["ecog"] == 3
    assert calculate_metrics(ecog=5)["kps_values"] == [0]


def test_batch_output(tmp_path):
    csv_in = tmp_path / "in.csv"
    csv_out = tmp_path / "out.csv"
    csv_in.write_text("case,ecog\nP-001,2\nP-002,5\n", encoding="utf-8")
    process_batch(str(csv_in), str(csv_out))
    with csv_out.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["mapped_kps_values"] == "50|60"
    assert rows[1]["mapped_ecog"] == "5"


def test_batch_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        process_batch(tmp_path / "missing.csv", tmp_path / "out.csv")


def test_batch_missing_output_directory(tmp_path):
    source = tmp_path / "in.csv"
    source.write_text("ecog\n3\n", encoding="utf-8")
    with pytest.raises(FileNotFoundError):
        process_batch(source, tmp_path / "absent" / "out.csv")
