"""Calendar release versions: YY.MM.DD.N, dated in Europe/Moscow."""

from datetime import date, datetime
import re
from zoneinfo import ZoneInfo


CALVER = re.compile(r"([0-9]{2})\.([0-9]{2})\.([0-9]{2})\.([1-9][0-9]*)")


def parse_version(version: str) -> tuple[date, int]:
    match = CALVER.fullmatch(version)
    if match is None:
        raise ValueError("version must use YY.MM.DD.N with a positive daily release number")
    year, month, day, number = map(int, match.groups())
    return date(2000 + year, month, day), number


def next_version(tags: list[str], day: date | None = None) -> str:
    day = day or datetime.now(ZoneInfo("Europe/Moscow")).date()
    if not 2000 <= day.year <= 2099:
        raise ValueError("two-digit release years cover 2000 through 2099")
    numbers = []
    for tag in tags:
        if not tag.startswith("v"):
            continue
        try:
            released_day, number = parse_version(tag[1:])
        except ValueError:
            continue  # Historical semantic-version tags remain unchanged.
        if released_day > day:
            raise ValueError("a release tag is dated after the proposed release day")
        if released_day == day:
            numbers.append(number)
    return f"{day:%y.%m.%d}.{max(numbers, default=0) + 1}"
