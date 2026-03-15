# Validation Workflow

Use the validator before importing any new Data Team drop.

## Production API behavior

Production `/labs` and API validation now support:

- ESMO JSON
- PubMed JSON
- PubMed CSV
- PubMed TXT

Important nuance:

- local validation prefers `scripts/validate_data_drop.py`
- production uses the serverless fallback validator when local scripts are unavailable
- these two paths should behave the same for supported dataset shapes

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

You can also validate legacy text exports:

```bash
python3 scripts/validate_data_drop.py --dataset pubmed --path /path/to/pubmed.txt
```

## Validate through the production API

ESMO folder batch:

```bash
curl -X POST https://mit-cancer-navigator-api-boringsoft.vercel.app/api/v1/validate/esmo \
  -H 'content-type: application/json' \
  --data '{"path":"datasets/esmo/v.5"}'
```

PubMed CSV:

```bash
curl -X POST https://mit-cancer-navigator-api-boringsoft.vercel.app/api/v1/validate/pubmed \
  -H 'content-type: application/json' \
  --data '{"path":"datasets/pubmed/v.5/pubmed-NSCLCANDlo-set_100entries_extracted_v5.csv"}'
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
