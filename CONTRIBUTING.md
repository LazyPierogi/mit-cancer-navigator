# Contributing

Thank you for considering a contribution to `mit-cancer-navigator`.

This repository is a public research and engineering project built around transparent evidence triage for NSCLC case review. We welcome improvements that make the system more understandable, testable, safer, and easier to maintain.

## Before you contribute

Please keep the following project boundaries in mind:

- This repository is **not** a clinical decision system.
- Contributions must preserve a **responsible AI posture**: explicit limitations, inspectable behavior, visible uncertainty, and no misleading automation claims.
- Bundled datasets and fixtures in this repository are currently included for **proof-of-concept use only**. They are **not approved for external reuse or production use**.

## What good contributions look like

We especially welcome contributions that improve:

- deterministic ranking, labeling, and provenance
- evaluation and benchmark reliability
- input validation and schema clarity
- explainability and uncertainty handling
- setup, tests, and contributor documentation
- UI clarity for evidence inspection and runtime transparency

## What to avoid

Please do not submit contributions that:

- turn the product into a free-form diagnosis or treatment recommender
- hide important uncertainty behind polished wording
- weaken provenance, auditability, or deterministic guardrails
- introduce secrets, credentials, or environment-specific values into tracked files
- add patient-identifiable information, confidential documents, or third-party data you do not have rights to share
- present benchmark or retrieval lift as clinical validation

## Local setup

### Prerequisites

- Node.js 24+
- Python 3.11+
- `uv`
- Docker optional for local infrastructure

### Install

```bash
npm install
uv sync --project apps/api
uv sync --project apps/worker
```

### Run locally

```bash
npm run migrate:api
npm run dev:api
npm run dev:web
```

Optional infrastructure:

```bash
docker compose -f infra/compose/docker-compose.yml up -d
```

## Contribution workflow

1. Start from a fresh branch.
2. Keep changes focused and easy to review.
3. Update documentation when behavior, architecture, or contributor expectations change.
4. Add or update tests when changing runtime logic, imports, schemas, or evaluation behavior.
5. Open a pull request with a clear explanation of:
   - the problem
   - the intended change
   - any safety, provenance, or data implications

## Validation expectations

Run the checks that match your change:

```bash
npm run test:domain
uv run --project apps/api python -m unittest discover -s apps/api/tests -p 'test_*.py'
npm --workspace apps/web run build
```

If you change data import or validation logic, also review the workflows in `docs/data-team/`.

## Responsible AI contribution rules

When proposing changes involving retrieval, embeddings, or LLM-assisted behavior:

- keep the deterministic path understandable and authoritative
- treat semantic retrieval as assistive, not self-justifying
- keep provenance visible
- preserve manual review and uncertainty surfaces
- avoid language that overstates clinical reliability
- prefer reversible, inspectable logic over opaque magic

## Data contribution rules

Please do not contribute:

- private clinical records
- protected health information
- confidential PDFs or internal presentations
- third-party datasets or papers that cannot be publicly redistributed

If you contribute data-related examples or fixtures, make sure they are safe to publish and clearly documented.

## Security

If you discover a security issue or secret exposure, please do **not** open a public exploit-style issue with sensitive details. Instead, contact the repository maintainers through GitHub in a private and responsible way.

## License

By contributing to this repository, you agree that your contributions will be released under the MIT License that governs the code in this repository.
