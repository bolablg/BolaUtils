# Timestamp Normalizer

Timestamp Normalizer rescales timestamp data onto a chosen calendar period.
It is useful when historical data spans many dates but a learning exercise,
demo, or simulation needs the same relative activity compressed into one or
more specific dates.

The transformation uses the minimum and maximum non-missing timestamps in the
input. It does not require the input to be sorted and does not reorder rows.

## Quick start

From this folder:

```bash
python3 -m pip install -e ".[pandas]"
```

Then normalize one DataFrame column:

```python
from timestamp_normalizer import normalize_timestamp_column

df["simulated_time"] = normalize_timestamp_column(
    df["event_time"],
    target_date="2026-09-10",
)
```

The original `event_time` column is not changed.

## Target periods

`step` is the number of additional calendar days in the target period. It is
`0` by default:

| `step` | Target period |
| ---: | --- |
| `0` | `target_date 00:00:00` through `target_date 23:59:59.999...` |
| `1` | `target_date 00:00:00` through `target_date + 1 day 23:59:59.999...` |
| `2` | `target_date 00:00:00` through `target_date + 2 days 23:59:59.999...` |

For example:

```python
df["simulated_time"] = normalize_timestamp_column(
    df["event_time"],
    target_date="2026-09-10",
    step=1,
)
```

This maps the complete historical range into September 10 and September 11,
2026. In the pandas path, the final timestamp can reach
`23:59:59.999999999`; the standard-library path uses Python datetime precision
and reaches `23:59:59.999999`.

## Several timestamp columns

Use `normalize_timestamp_columns` to process multiple columns in one call:

```python
from timestamp_normalizer import normalize_timestamp_columns

normalized_df = normalize_timestamp_columns(
    df,
    ["created_at", "updated_at", "last_seen_at"],
    target_date="2026-09-10",
    step=1,
)
```

By default, each column uses its own minimum and maximum. This is useful when
the columns represent separate timestamp fields with different ranges.

When columns are related points on the same timeline, use `shared_range=True`:

```python
normalized_df = normalize_timestamp_columns(
    df,
    ["start_time", "end_time"],
    target_date="2026-09-10",
    step=1,
    shared_range=True,
)
```

The shared mode uses one global minimum and maximum across the selected
columns, so the relationship between `start_time` and `end_time` is retained.

## API

### `normalize_timestamps_to_day(values, target_date, *, step=0)`

The dependency-free core function. It accepts an iterable of Python
`datetime` values, `date` values, ISO-8601 strings, or missing values, and
returns a list in the original order.

### `normalize_timestamp_column(column, target_date, *, step=0)`

Normalizes one column. A pandas Series is returned as a pandas Series with its
original index and name; other iterables return a list.

### `normalize_timestamp_columns(dataframe, columns, target_date, *, shared_range=False, inplace=False, step=0)`

Normalizes several columns in a pandas DataFrame. The default returns a copy.
Set `inplace=True` only when modifying the original DataFrame is intentional.

## Behavior and edge cases

- Input rows are never sorted or reordered.
- Missing values remain missing.
- The target date's time component is ignored.
- Equal input timestamps map to midnight because there is no range to scale.
- Mixed timezone-aware and timezone-naive input timestamps are rejected.
- `step` must be a non-negative integer.
- Invalid timestamp values raise an error instead of being silently guessed.

## Development

Install the test and pandas extras, then run the test suite:

```bash
python3 -m pip install -e ".[test,pandas]"
python3 -m pytest -q
```

The tests cover unsorted input, missing values, ISO-8601 parsing, equal
timestamps, timezone validation, multi-column normalization, shared ranges, and
multi-day target periods.
