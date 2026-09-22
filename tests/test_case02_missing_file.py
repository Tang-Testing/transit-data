"""
Case 02 — Source file arrives late / is missing.

Scenario: the day's GPS file hasn't landed yet. The freshness check
must detect this explicitly instead of the pipeline silently doing
nothing (or crashing on a FileNotFoundError deep inside the loader).
"""
from etl.run_pipeline import check_freshness


def test_missing_gps_file_is_detected():
    # 2026-09-22 ("today") deliberately has no GPS file — see
    # scripts/generate_mock_data.py
    assert check_freshness("2026-09-22") is None


def test_existing_gps_file_is_found():
    assert check_freshness("2026-09-21") is not None
