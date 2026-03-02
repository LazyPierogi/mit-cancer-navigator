# Validation Workflow

Use the validator before importing any new Data Team drop.

## Validate the current repo datasets

```bash
python3 scripts/validate_data_drop.py --current
```

## Validate a single incoming file

ESMO:

```bash
python3 scripts/validate_data_drop.py --dataset esmo --path /path/to/esmo.json
```

PubMed:

```bash
python3 scripts/validate_data_drop.py --dataset pubmed --path /path/to/pubmed.csv
```

## JSON output

If you want machine-readable output:

```bash
python3 scripts/validate_data_drop.py --current --format json
```

## Exit codes

- `0`: validation passed
- `1`: validation found errors
- `2`: invalid command usage

Warnings do not fail by default.

If you want warnings to fail too:

```bash
python3 scripts/validate_data_drop.py --current --strict-warnings
```

## What the validator checks

- required fields exist
- duplicate IDs
- non-empty critical values
- canonical enum values
- ambiguous biomarker flags
- free-text fields where structured values are expected
- empty or non-normalized intervention tags
- mixed clinical scenarios in a single row
