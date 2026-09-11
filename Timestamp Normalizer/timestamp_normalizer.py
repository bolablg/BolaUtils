"""Normalize timestamps onto a configurable calendar period.

The transformation keeps each timestamp's relative position between the
minimum and maximum timestamp, while compressing the complete range into a
configurable calendar period.  The input order is never changed.

The module has no required third-party dependency.  If pandas is installed,
``normalize_timestamp_column`` preserves a pandas Series' index and name, and
``normalize_timestamp_columns`` can process several DataFrame columns at once.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date, datetime, time, timedelta
from numbers import Integral
from typing import Any, TypeAlias


DateLike: TypeAlias = date | datetime | str | Any
TimestampValue: TypeAlias = datetime | None

__all__ = [
    "normalize_timestamp_column",
    "normalize_timestamp_columns",
    "normalize_timestamps_to_day",
]


def _validate_step(step: int) -> int:
    """Validate and normalize the number of additional target days."""

    if isinstance(step, bool) or not isinstance(step, Integral):
        raise TypeError("step must be an integer greater than or equal to 0")
    if step < 0:
        raise ValueError("step must be greater than or equal to 0")
    return int(step)


def _target_span(step: int) -> timedelta:
    """Return the inclusive target period length at microsecond precision."""

    return timedelta(days=_validate_step(step) + 1) - timedelta(microseconds=1)


def _is_missing(value: object) -> bool:
    """Return whether a value should be treated as a missing timestamp."""

    if value is None:
        return True

    # These names cover pandas.NaT and pandas.NA without making pandas a
    # required dependency for the core function.
    if value.__class__.__name__ in {"NaTType", "NAType"}:
        return True

    try:
        comparison = value != value
        return bool(comparison)
    except (TypeError, ValueError):
        return False


def _to_datetime(value: DateLike, *, field_name: str) -> TimestampValue:
    """Convert common datetime-like values to a standard-library datetime."""

    if _is_missing(value):
        return None

    if isinstance(value, datetime):
        return value

    if isinstance(value, date):
        return datetime.combine(value, time.min)

    # pandas.Timestamp and several other datetime-like objects expose this
    # method.  It lets the dependency-free core accept them when available.
    to_pydatetime = getattr(value, "to_pydatetime", None)
    if callable(to_pydatetime):
        converted = to_pydatetime()
        if isinstance(converted, datetime):
            return converted

    if isinstance(value, str):
        text = value.strip()
        if not text:
            raise ValueError(f"{field_name} cannot be an empty string")
        if text.endswith("Z"):
            text = f"{text[:-1]}+00:00"
        try:
            return datetime.fromisoformat(text)
        except ValueError as exc:
            raise ValueError(
                f"{field_name} must be an ISO-8601 datetime or date; got {value!r}"
            ) from exc

    raise TypeError(
        f"{field_name} must contain datetime, date, ISO-8601 string, or None values; "
        f"got {type(value).__name__}"
    )


def normalize_timestamps_to_day(
    values: Iterable[DateLike],
    target_date: DateLike,
    *,
    step: int = 0,
) -> list[TimestampValue]:
    """Map timestamps onto a target period while preserving relative position.

    The earliest non-missing input timestamp maps to midnight at the start of
    ``target_date``.  The latest maps to the final representable microsecond
    of the period defined by ``step``.  Values in between are linearly scaled
    between those two endpoints.  The original input order and missing values
    are preserved.

    Parameters
    ----------
    values:
        An iterable containing ``datetime`` values, ISO-8601 strings, dates,
        or missing values represented by ``None``/``pandas.NaT``.
    target_date:
        The first date of the target period.  Any time component is ignored.
    step:
        The number of additional calendar days in the target period.  ``0``
        maps the range onto one day.  ``1`` maps it from the start of
        ``target_date`` through the end of the following day.

    Returns
    -------
    list[datetime | None]
        A list in the same order as ``values``.

    Notes
    -----
    If all non-missing timestamps are equal, every non-missing value maps to
    midnight on the target date because there is no range to scale.
    """

    step = _validate_step(step)
    timestamps = [_to_datetime(value, field_name="timestamp") for value in values]
    valid_timestamps = [value for value in timestamps if value is not None]

    if not valid_timestamps:
        return timestamps

    awareness = {value.tzinfo is None for value in valid_timestamps}
    if len(awareness) > 1:
        raise ValueError(
            "timestamps cannot mix timezone-aware and timezone-naive values"
        )

    target = _to_datetime(target_date, field_name="target_date")
    if target is None:
        raise ValueError("target_date cannot be missing")

    # A naive target date inherits the source timezone when the source is
    # timezone-aware.  A timezone supplied with target_date is preserved.
    source_is_aware = valid_timestamps[0].tzinfo is not None
    if source_is_aware and target.tzinfo is None:
        target = target.replace(tzinfo=valid_timestamps[0].tzinfo)

    target_start = datetime.combine(target.date(), time.min, tzinfo=target.tzinfo)
    minimum = min(valid_timestamps)
    maximum = max(valid_timestamps)
    source_span = maximum - minimum

    if source_span == timedelta(0):
        return [None if timestamp is None else target_start for timestamp in timestamps]

    target_span = _target_span(step)
    normalized: list[TimestampValue] = []
    for timestamp in timestamps:
        if timestamp is None:
            normalized.append(None)
            continue

        relative_position = (timestamp - minimum) / source_span
        normalized.append(target_start + target_span * relative_position)

    return normalized


def normalize_timestamp_column(
    column: Any,
    target_date: DateLike,
    *,
    step: int = 0,
) -> Any:
    """Normalize a timestamp column, preserving a pandas Series when possible.

    For a pandas Series, the returned Series keeps the original index and
    name.  For any other iterable, this function returns a list of
    ``datetime``/``None`` values.  ``step`` controls the inclusive target
    period in the same way as :func:`normalize_timestamps_to_day`.
    """

    try:
        import pandas as pd  # type: ignore[import-not-found]
    except ImportError:
        pd = None

    if pd is not None and isinstance(column, pd.Series):
        return _normalize_pandas_series(column, target_date, step=step)

    return normalize_timestamps_to_day(column, target_date, step=step)


def _normalize_pandas_series(
    column: Any,
    target_date: DateLike,
    *,
    minimum: Any = None,
    maximum: Any = None,
    step: int = 0,
) -> Any:
    """Normalize one pandas Series, optionally using shared bounds."""

    import pandas as pd  # type: ignore[import-not-found]

    step = _validate_step(step)
    timestamps = pd.to_datetime(column, errors="raise")
    valid_timestamps = timestamps.dropna()

    if valid_timestamps.empty:
        return timestamps.copy()

    target = pd.Timestamp(target_date)
    source_timezone = getattr(timestamps.dt, "tz", None)
    if source_timezone is not None and target.tzinfo is None:
        target = target.tz_localize(source_timezone)
    target = target.normalize()

    if minimum is None:
        minimum = valid_timestamps.min()
    if maximum is None:
        maximum = valid_timestamps.max()

    source_span = maximum - minimum

    if source_span == pd.Timedelta(0):
        normalized = pd.Series(
            target,
            index=column.index,
            name=column.name,
        )
        return normalized.where(timestamps.notna())

    target_span = pd.Timedelta(days=step + 1) - pd.Timedelta(nanoseconds=1)
    relative_position = (timestamps - minimum) / source_span
    normalized = target + relative_position * target_span
    return pd.Series(
        normalized,
        index=column.index,
        name=column.name,
    ).where(timestamps.notna())


def normalize_timestamp_columns(
    dataframe: Any,
    columns: Iterable[str],
    target_date: DateLike,
    *,
    shared_range: bool = False,
    inplace: bool = False,
    step: int = 0,
) -> Any:
    """Normalize several timestamp columns in one pandas DataFrame operation.

    Parameters
    ----------
    dataframe:
        A pandas DataFrame.
    columns:
        The timestamp column names to normalize.
    target_date:
        The calendar date onto which the selected columns are mapped.
    step:
        The number of additional calendar days in the target period.  ``0``
        maps the range onto one day.  ``1`` maps it from the start of
        ``target_date`` through the end of the following day.
    shared_range:
        When ``False`` (the default), each column uses its own minimum and
        maximum.  When ``True``, all selected columns use one global minimum
        and maximum, which preserves relationships between columns such as a
        start and end timestamp.
    inplace:
        When ``False`` (the default), return a copy and leave ``dataframe``
        unchanged.  When ``True``, modify and return the original DataFrame.

    Returns
    -------
    pandas.DataFrame
        The normalized DataFrame.

    Examples
    --------
    >>> df = normalize_timestamp_columns(
    ...     df,
    ...     ["created_at", "updated_at"],
    ...     "2026-09-10",
    ... )

    Use ``shared_range=True`` when the columns describe related points on one
    timeline:

    >>> df = normalize_timestamp_columns(
    ...     df,
    ...     ["start_time", "end_time"],
    ...     "2026-09-10",
    ...     shared_range=True,
    ... )
    """

    if isinstance(columns, str):
        raise TypeError("columns must be an iterable of column names, not one string")

    selected_columns = list(columns)
    if not selected_columns:
        raise ValueError("columns cannot be empty")
    if len(set(selected_columns)) != len(selected_columns):
        raise ValueError("columns cannot contain duplicate names")

    step = _validate_step(step)

    try:
        import pandas as pd  # type: ignore[import-not-found]
    except ImportError as exc:
        raise ImportError(
            "normalize_timestamp_columns requires pandas; install pandas first"
        ) from exc

    if not isinstance(dataframe, pd.DataFrame):
        raise TypeError("dataframe must be a pandas DataFrame")

    missing_columns = [
        column_name
        for column_name in selected_columns
        if column_name not in dataframe.columns
    ]
    if missing_columns:
        raise KeyError(f"timestamp columns not found: {missing_columns}")

    result = dataframe if inplace else dataframe.copy()
    parsed_columns = {
        column_name: pd.to_datetime(result[column_name], errors="raise")
        for column_name in selected_columns
    }

    shared_minimum = None
    shared_maximum = None
    if shared_range:
        valid_parts = [
            timestamp_series.dropna() for timestamp_series in parsed_columns.values()
        ]
        valid_parts = [part for part in valid_parts if not part.empty]
        if valid_parts:
            all_valid_timestamps = pd.concat(valid_parts, ignore_index=True)
            shared_minimum = all_valid_timestamps.min()
            shared_maximum = all_valid_timestamps.max()

    for column_name, timestamp_series in parsed_columns.items():
        if shared_range:
            result[column_name] = _normalize_pandas_series(
                timestamp_series,
                target_date,
                minimum=shared_minimum,
                maximum=shared_maximum,
                step=step,
            )
        else:
            result[column_name] = _normalize_pandas_series(
                timestamp_series,
                target_date,
                step=step,
            )

    return result
