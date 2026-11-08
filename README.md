# FeatherFilters

Filter data used by FeatherShield and Feather Browser.

This repository contains the blocking data that was previously embedded directly in Feather Browser's `BlockerEngine` on the `v2.0.0` branch. Keeping filter data separate means rules can be updated independently from browser releases.

## Layout

- `filters/network-domains.txt` — known advertising, analytics and tracking hosts.
- `filters/tracking-tokens.txt` — URL tokens used by strict third-party tracking detection.
- `tracking-parameters.txt` — query parameters removed from top-level navigation URLs.
- `exceptions/network-domains.txt` — compatibility exceptions.
- `metadata.json` — filter format/version metadata.
- `subscriptions/` — full filter lists in Adblock Plus / uBlock Origin syntax, all loaded:
  - `feather.txt` — Feather's own rules, including the anti-adblock stub redirects.
  - `easylist.txt`, `easyprivacy.txt` — [EasyList](https://easylist.to/) ads and tracking lists.
  - `ublock-filters.txt` — [uBlock filters](https://github.com/uBlockOrigin/uAssets), with its
    `!#include` sub-lists expanded in place (the mobile-only sub-list is left out). This is where most
    anti-adblock fixes (`##+js(...)` scriptlets and `$redirect` rules) come from.
  - `ublock-quick-fixes.txt` — uBlock filters – Quick fixes, short-lived fixes for sites that just broke.

Blank lines and lines beginning with `#` or `!` are ignored by the loader, except the
`!#if` / `!#else` / `!#endif` blocks, which are evaluated for a desktop Chromium browser.

## Updating the third-party lists

The EasyList and uBlock lists are snapshots. Refresh them from upstream before a release (Quick fixes
changes every few hours):

```bash
python scripts/update_lists.py          # download, check and write all four lists
python scripts/update_lists.py --check  # download and check only
```

The script expands uBlock's `!#include` lines in place (FeatherShield does not fetch includes),
leaves out the mobile-only `filters-mobile.txt`, and regenerates the two header lines that record
the source and license. It writes nothing if any download fails or any list is empty, has no
`! Title:` line, still contains an `!#include`, or has lost more than half of its rules.

The `Update third-party lists` workflow (`.github/workflows/update-lists.yml`) runs it every Monday
and opens or updates a pull request when the lists change. Don't edit these files by hand.

## Validation

```bash
python scripts/validate.py
```

The validator checks for duplicate domains/parameters and malformed host entries.

## Consuming from FeatherShield

Clone or download this repository, then point FeatherShield's `FilterListLoader` at the repository root:

```csharp
RuleSet rules = FilterListLoader.LoadDirectory(pathToFeatherFilters);
var shield = new ShieldEngine(rules);
```

## License

Feather's own files are MIT. The third-party lists keep their upstream licenses:

| File | Upstream | License |
|---|---|---|
| `subscriptions/easylist.txt`, `subscriptions/easyprivacy.txt` | https://easylist.to/ | GPL-3.0 or CC BY-SA 3.0 (dual) |
| `subscriptions/ublock-filters.txt`, `subscriptions/ublock-quick-fixes.txt` | https://github.com/uBlockOrigin/uAssets | GPL-3.0 |
