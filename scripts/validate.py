from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
DOMAIN_RE = re.compile(r"^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$", re.I)


def values(path: Path):
    for raw in path.read_text(encoding="utf-8").splitlines():
        value = raw.strip()
        if not value or value.startswith(("#", "!")):
            continue
        yield value


def unique(path: Path):
    seen = set()
    duplicates = []
    for value in values(path):
        key = value.casefold()
        if key in seen:
            duplicates.append(value)
        seen.add(key)
    return duplicates


def main():
    failures = []
    domain_files = [
        ROOT / "filters/network-domains.txt",
        ROOT / "exceptions/network-domains.txt",
    ]

    for path in domain_files:
        dupes = unique(path)
        if dupes:
            failures.append(f"{path.name}: duplicate values: {', '.join(dupes)}")
        for value in values(path):
            if not DOMAIN_RE.fullmatch(value):
                failures.append(f"{path.name}: invalid hostname: {value}")

    for path in [ROOT / "filters/tracking-tokens.txt", ROOT / "tracking-parameters.txt"]:
        dupes = unique(path)
        if dupes:
            failures.append(f"{path.name}: duplicate values: {', '.join(dupes)}")

    if failures:
        print("FeatherFilters validation failed:")
        for failure in failures:
            print(f" - {failure}")
        return 1

    print("FeatherFilters validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
