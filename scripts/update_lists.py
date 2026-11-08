"""Refresh the third-party filter lists bundled in subscriptions/.

Downloads EasyList, EasyPrivacy, uBlock filters and uBlock Quick fixes, expands
uBlock's `!#include` lines in place (FeatherShield does not fetch includes),
adds the FeatherFilters header lines, sanity-checks every list and only then
writes them. If any download or check fails, nothing is written.

Usage:
    python scripts/update_lists.py
    python scripts/update_lists.py --check
"""

from datetime import datetime, timezone
from pathlib import Path
import argparse
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
SUBSCRIPTIONS = ROOT / "subscriptions"

UBO_BASE = "https://ublockorigin.github.io/uAssets/filters/"
UBO_LICENSE = (
    "! uBlock Origin filter lists (https://github.com/uBlockOrigin/uAssets), "
    "licensed GPL-3.0. Do not edit by hand."
)
SKIPPED_INCLUDES = {"filters-mobile.txt"}
LISTS = [
    ("easylist.txt", "https://easylist.to/easylist/easylist.txt", False),
    ("easyprivacy.txt", "https://easylist.to/easylist/easyprivacy.txt", False),
    ("ublock-filters.txt", UBO_BASE + "filters.txt", True),
    ("ublock-quick-fixes.txt", UBO_BASE + "quick-fixes.txt", True),
]
MIN_RULE_RATIO = 0.5
MIN_RULES = 50

INCLUDE_RE = re.compile(r"^!#include\s+(\S+)\s*$")
TITLE_RE = re.compile(r"^! Title:", re.M)
USER_AGENT = "FeatherFilters-updater (+https://github.com/FeatherBrowser/FeatherFilters)"


class UpdateError(Exception):
    pass


def fetch(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            if response.status != 200:
                raise UpdateError(f"{url}: HTTP {response.status}")
            data = response.read()
            expected = response.headers.get("Content-Length")
            if expected and not response.headers.get("Content-Encoding") and len(data) != int(expected):
                raise UpdateError(f"{url}: got {len(data)} bytes, expected {expected}")
    except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
        raise UpdateError(f"{url}: {error}") from error
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise UpdateError(f"{url}: not valid UTF-8 ({error})") from error
    if not text.strip():
        raise UpdateError(f"{url}: empty response")
    return text.replace("\r\n", "\n").replace("\r", "\n")


def expand_includes(text: str, base_url: str, seen: set[str]) -> str:
    out = []
    for line in text.split("\n"):
        match = INCLUDE_RE.match(line.strip())
        if not match:
            out.append(line)
            continue
        name = match.group(1)
        if name in SKIPPED_INCLUDES:
            out.append(f"! ({name} is mobile-only and not bundled)")
            continue
        url = urllib.parse.urljoin(base_url, name)
        if not url.startswith(UBO_BASE):
            raise UpdateError(f"{base_url}: include {name!r} resolves outside {UBO_BASE}")
        if url in seen:
            raise UpdateError(f"{base_url}: include cycle through {name!r}")
        print(f"  including {name}")
        included = fetch(url)
        if rule_count(included) == 0:
            raise UpdateError(f"{url}: included list has no rules")
        out.append(f"! >>> begin {name}")
        out.append(expand_includes(included, url, seen | {url}).rstrip("\n"))
        out.append(f"! <<< end {name}")
    return "\n".join(out)


def rule_count(text: str) -> int:
    return sum(1 for line in text.split("\n") if line.strip() and not line.lstrip().startswith(("!", "#", "[")))


def build(name: str, url: str, is_ubo: bool, today: str) -> str:
    print(f"{name}: downloading {url}")
    text = fetch(url)
    if is_ubo:
        text = expand_includes(text, url, {url})
        source = url + (" (with its !#include files expanded in place)" if name == "ublock-filters.txt" else "")
        text = f"! Bundled by FeatherFilters on {today} from {source}\n{UBO_LICENSE}\n{text}"
    return text.rstrip("\n") + "\n"


def check(name: str, text: str) -> list[str]:
    problems = []
    rules = rule_count(text)
    if rules < MIN_RULES:
        problems.append(f"{name}: only {rules} rules")
    if not TITLE_RE.search(text):
        problems.append(f"{name}: no '! Title:' line")
    for number, line in enumerate(text.split("\n"), 1):
        if line.strip().startswith("!#include"):
            problems.append(f"{name}:{number}: leftover {line.strip()!r}")
    directives = [line.split()[0] for line in text.split("\n") if line.startswith("!#")]
    if directives.count("!#if") != directives.count("!#endif"):
        problems.append(f"{name}: unbalanced !#if/!#endif")
    current = SUBSCRIPTIONS / name
    if current.exists():
        old_rules = rule_count(current.read_text(encoding="utf-8"))
        if old_rules and rules < old_rules * MIN_RULE_RATIO:
            problems.append(f"{name}: {rules} rules, down from {old_rules}; looks truncated")
    print(f"{name}: {rules} rules")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="download and check, but do not write")
    args = parser.parse_args()

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    results = {}
    problems = []
    try:
        for name, url, is_ubo in LISTS:
            results[name] = build(name, url, is_ubo, today)
            problems += check(name, results[name])
    except UpdateError as error:
        problems.append(str(error))

    if problems:
        print("Update failed; no files were written:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1

    if args.check:
        print("All lists downloaded and passed checks (--check: nothing written).")
        return 0

    for name, text in results.items():
        (SUBSCRIPTIONS / name).write_text(text, encoding="utf-8", newline="\n")
    print(f"Wrote {len(results)} lists to {SUBSCRIPTIONS}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
