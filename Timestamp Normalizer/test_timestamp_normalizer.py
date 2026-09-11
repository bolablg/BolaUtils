from datetime import datetime, timedelta

import pytest

from timestamp_normalizer import (
    normalize_timestamp_column,
    normalize_timestamp_columns,
    normalize_timestamps_to_day,
)


def test_scales_unsorted_values_to_one_day_without_changing_order():
    values = [
        datetime(2024, 1, 10, 8),
        datetime(2024, 1, 1, 8),
        datetime(2024, 1, 3, 20),
    ]

    result = normalize_timestamps_to_day(values, "2026-09-10")

    assert result == [
        datetime(2026, 9, 10, 23, 59, 59, 999999),
        datetime(2026, 9, 10, 0, 0),
        datetime(2026, 9, 10, 6, 40),
    ]


def test_preserves_missing_values_and_accepts_iso_strings():
    result = normalize_timestamp_column(
        ["2024-01-01T00:00:00", None, "2024-01-03T00:00:00"],
        datetime(2026, 9, 10, 14),
    )

    assert result == [
        datetime(2026, 9, 10, 0, 0),
        None,
        datetime(2026, 9, 10, 23, 59, 59, 999999),
    ]


def test_equal_timestamps_map_to_target_midnight():
    values = [datetime(2024, 1, 1, 12), datetime(2024, 1, 1, 12), None]

    result = normalize_timestamps_to_day(values, "2026-09-10")

    assert result == [datetime(2026, 9, 10), datetime(2026, 9, 10), None]


def test_rejects_mixed_timezone_awareness():
    values = [
        datetime(2024, 1, 1),
        datetime(2024, 1, 2, tzinfo=datetime.now().astimezone().tzinfo),
    ]

    with pytest.raises(ValueError, match="timezone-aware"):
        normalize_timestamps_to_day(values, "2026-09-10")


def test_output_span_is_one_microsecond_less_than_one_day():
    result = normalize_timestamps_to_day(
        [datetime(2024, 1, 1), datetime(2024, 1, 2)],
        "2026-09-10",
    )

    assert result[1] - result[0] == timedelta(days=1) - timedelta(microseconds=1)


def test_step_extends_the_target_period_by_additional_calendar_days():
    result = normalize_timestamps_to_day(
        [datetime(2024, 1, 1), datetime(2024, 1, 2)],
        "2026-09-10",
        step=1,
    )

    assert result == [
        datetime(2026, 9, 10, 0, 0),
        datetime(2026, 9, 11, 23, 59, 59, 999999),
    ]


def test_step_must_be_a_non_negative_integer():
    with pytest.raises(ValueError, match="greater than or equal to 0"):
        normalize_timestamps_to_day(
            [datetime(2024, 1, 1), datetime(2024, 1, 2)],
            "2026-09-10",
            step=-1,
        )

    with pytest.raises(TypeError, match="must be an integer"):
        normalize_timestamps_to_day(
            [datetime(2024, 1, 1), datetime(2024, 1, 2)],
            "2026-09-10",
            step=1.5,
        )


def test_normalizes_multiple_columns_independently_when_pandas_is_available():
    pd = pytest.importorskip("pandas")
    dataframe = pd.DataFrame(
        {
            "created_at": pd.to_datetime(["2024-01-01", "2024-01-03"]),
            "updated_at": pd.to_datetime(["2024-01-01 12:00", "2024-01-02 12:00"]),
            "value": [10, 20],
        },
        index=[10, 20],
    )

    result = normalize_timestamp_columns(
        dataframe,
        ["created_at", "updated_at"],
        "2026-09-10",
    )

    assert result.index.tolist() == [10, 20]
    assert result["value"].tolist() == [10, 20]
    assert result["created_at"].iloc[0] == pd.Timestamp("2026-09-10 00:00:00")
    assert result["created_at"].iloc[1] == pd.Timestamp("2026-09-10 23:59:59.999999999")
    assert result["updated_at"].iloc[0] == pd.Timestamp("2026-09-10 00:00:00")
    assert result["updated_at"].iloc[1] == pd.Timestamp("2026-09-10 23:59:59.999999999")
    assert dataframe["created_at"].iloc[0] == pd.Timestamp("2024-01-01")


def test_shared_range_preserves_relationships_between_columns():
    pd = pytest.importorskip("pandas")
    dataframe = pd.DataFrame(
        {
            "start_time": pd.to_datetime(["2024-01-01", "2024-01-03"]),
            "end_time": pd.to_datetime(["2024-01-02", "2024-01-04"]),
        }
    )

    result = normalize_timestamp_columns(
        dataframe,
        ["start_time", "end_time"],
        "2026-09-10",
        shared_range=True,
    )

    assert result["start_time"].iloc[0] == pd.Timestamp("2026-09-10 00:00:00")
    assert result["end_time"].iloc[0] == pd.Timestamp("2026-09-10 07:59:59.999999999")
    assert result["start_time"].iloc[1] == pd.Timestamp("2026-09-10 15:59:59.999999999")
    assert result["end_time"].iloc[1] == pd.Timestamp("2026-09-10 23:59:59.999999999")


def test_multiple_columns_can_use_a_multi_day_target_period():
    pd = pytest.importorskip("pandas")
    dataframe = pd.DataFrame(
        {
            "created_at": pd.to_datetime(["2024-01-01", "2024-01-02"]),
            "updated_at": pd.to_datetime(["2024-01-01", "2024-01-02"]),
        }
    )

    result = normalize_timestamp_columns(
        dataframe,
        ["created_at", "updated_at"],
        "2026-09-10",
        step=1,
    )

    expected_end = pd.Timestamp("2026-09-11 23:59:59.999999999")
    assert result["created_at"].iloc[1] == expected_end
    assert result["updated_at"].iloc[1] == expected_end
