"""Reference-table and safety tests for the clinical score crosswalk."""
import csv
import json
import pytest
from ecog_karnofsky import (
    ECOG_TO_KPS, calculate_metrics, main, map_ecog_to_kps, map_kps_to_ecog,
    process_batch,
)


@pytest.mark.parametrize("grade,expected", list(ECOG_TO_KPS.items()))
def test_all_ecog_grades(grade, expected):
    mapped = map_ecog_to_kps(grade)
    assert mapped["ecog"] == grade
    assert mapped["kps_values"] == list(expected)
    assert mapped["kps_min"] == min(expected)
    assert mapped["kps_max"] == max(expected)


@pytest.mark.parametrize("grade,values", list(ECOG_TO_KPS.items()))
def test_all_kps_deciles(grade, values):
    for kps in values:
        mapped = map_kps_to_ecog(kps)
        assert mapped["ecog"] == grade
        assert mapped["input_score"] == kps


@pytest.mark.parametrize("value", [-1, 6, 2.5, float("nan"), float("inf"), True, "", "abc"])
def test_invalid_ecog(value):
    with pytest.raises(ValueError):
        map_ecog_to_kps(value)


@pytest.mark.parametrize("value", [-10, 101, 55, 2.5, float("nan"), float("inf"), False])
def test_invalid_kps(value):
    with pytest.raises(ValueError):
        map_kps_to_ecog(value)


def test_exactly_one_scale():
    with pytest.raises(ValueError):
        calculate_metrics()
    with pytest.raises(ValueError):
        calculate_metrics(ecog=1, kps=80)


def test_single_cli(capsys):
    assert main(["single", "--ecog", "2"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["kps_values"] == [50, 60]


def test_batch_mixed_scale_and_csv_safety(tmp_path):
    source, output = tmp_path / "in.csv", tmp_path / "out.csv"
    source.write_text("case,ecog,kps\n=SUM(1+1),1,\nPT-2,,40\n", encoding="utf-8")
    assert process_batch(source, output) == 2
    with output.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["case"].startswith("'=")
    assert rows[0]["mapped_kps_values"] == "70|80"
    assert rows[1]["mapped_ecog"] == "3"


def test_batch_rejects_bad_row_without_overwriting(tmp_path):
    source, output = tmp_path / "in.csv", tmp_path / "out.csv"
    source.write_text("ecog,kps\n1,\n2,50\n", encoding="utf-8")
    output.write_text("previous result", encoding="utf-8")
    with pytest.raises(ValueError, match="Line 3"):
        process_batch(source, output)
    assert output.read_text(encoding="utf-8") == "previous result"


def test_batch_invalid_schema(tmp_path):
    source = tmp_path / "in.csv"
    for contents, phrase in [
        ("", "no headers"),
        ("case,v1\nPT-1,3\n", "ecog or kps"),
        ("ecog,ecog\n1,1\n", "duplicate"),
    ]:
        source.write_text(contents, encoding="utf-8")
        with pytest.raises(ValueError, match=phrase):
            process_batch(source, tmp_path / "out.csv")


def test_batch_prevents_self_overwrite(tmp_path):
    source = tmp_path / "in.csv"
    source.write_text("ecog\n1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="different file"):
        process_batch(source, source)
