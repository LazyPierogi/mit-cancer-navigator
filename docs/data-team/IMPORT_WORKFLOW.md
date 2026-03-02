# Import Workflow

After validation, use the import pipeline to load a dataset into the local application database.

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

Raw files are only auto-normalized for the current preview source files already stored in this repo.

For new external raw drops, the expected path is:

- Data Team sends canonical ESMO / PubMed files
- validator checks them
- importer ingests them
