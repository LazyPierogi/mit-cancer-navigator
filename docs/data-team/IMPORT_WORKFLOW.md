# Import Workflow

After validation, use the import pipeline to load a dataset into the local application database.

## Production runtime summary

- Production import batches persist in Supabase Postgres.
- `/labs` reads corpus state from those import batches.
- Real repo datasets are bundled into the API deployment and exposed under the logical `datasets/...` path namespace.

## Import the current curated ESMO dataset

```bash
uv run --project apps/api python scripts/import_data_drop.py --dataset esmo
```

## Import the current curated PubMed dataset

```bash
uv run --project apps/api python scripts/import_data_drop.py --dataset pubmed
```

## Import a specific file

```bash
uv run --project apps/api python scripts/import_data_drop.py --dataset esmo --path /path/to/file.json
```

## Output

The importer runs:

1. validation
2. normalization
3. ingest into the local database
4. import batch metadata persistence

Each run creates an import batch record with:

- batch ID
- dataset kind
- source path
- validation summary
- status
- record counts

## Current limitation

Canonical files can be imported directly.

Additional runtime support now exists for:

- ESMO `external_v2` JSON drops such as `datasets/esmo/v.5`
- PubMed `raw_v2` CSV drops such as `datasets/pubmed/v.2/*.csv` and `datasets/pubmed/v.5/*.csv`

Still not a general promise:

- arbitrary new raw formats without contract alignment
- legacy local preview assets as a long-term production ingest strategy

For new external raw drops, the expected path is:

- Data Team sends canonical ESMO / PubMed files
- validator checks them
- importer ingests them

## Production API examples

Import ESMO `v.5` folder batch:

```bash
curl -X POST https://mit-cancer-navigator-api-boringsoft.vercel.app/api/v1/import/esmo \
  -H 'content-type: application/json' \
  --data '{"path":"datasets/esmo/v.5"}'
```

Import PubMed CSV:

```bash
curl -X POST https://mit-cancer-navigator-api-boringsoft.vercel.app/api/v1/import/pubmed \
  -H 'content-type: application/json' \
  --data '{"path":"datasets/pubmed/v.5/pubmed-NSCLCANDlo-set_100entries_extracted_v5.csv"}'
```
