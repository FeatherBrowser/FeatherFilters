# FeatherFilters

Filter data used by FeatherShield and Feather Browser.

This repository contains the blocking data that was previously embedded directly in Feather Browser's `BlockerEngine` on the `v2.0.0` branch. Keeping filter data separate means rules can be updated independently from browser releases.

## Layout

- `filters/network-domains.txt` — known advertising, analytics and tracking hosts.
- `filters/tracking-tokens.txt` — URL tokens used by strict third-party tracking detection.
- `tracking-parameters.txt` — query parameters removed from top-level navigation URLs.
- `exceptions/network-domains.txt` — compatibility exceptions.
- `metadata.json` — filter format/version metadata.

Blank lines and lines beginning with `#` or `!` are ignored by the loader.

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

MIT.
