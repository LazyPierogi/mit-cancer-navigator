# Universal Rules: Security Baseline

## U-SEC-01
- Rule: Validate all external inputs at trust boundaries.
- Rationale: Boundary validation blocks malformed and hostile payloads early.
- Adoption signal: API/UI/file inputs are schema-validated before use.
- Failure signal: Runtime crashes or unsafe assumptions from unchecked input.

## U-SEC-02
- Rule: Keep secrets and runtime config out of code.
- Rationale: Hard-coded secrets are high-impact breach vectors.
- Adoption signal: Env schema is centralized and validated on startup.
- Failure signal: Tokens/URLs/keys appear in source files.

## U-SEC-03
- Rule: Minimize sensitive data handling by default.
- Rationale: Data minimization lowers legal, privacy, and breach exposure.
- Adoption signal: Only required fields are sent to external AI/services.
- Failure signal: Convenience payloads include unnecessary personal data.

## U-SEC-04
- Rule: Sanitize logs and diagnostics for privacy.
- Rationale: Debug logs often leak sensitive content unintentionally.
- Adoption signal: Logs include IDs/metrics but redact sensitive payloads.
- Failure signal: User content or PII appears in plaintext logs.

## U-SEC-05
- Rule: Design external side effects to be reversible when possible.
- Rationale: Undo/rollback protects data integrity after integration failures.
- Adoption signal: External write IDs are persisted for compensating actions.
- Failure signal: Undo cannot cleanly revert external writes.

## U-SEC-06
- Rule: Apply least-privilege and explicit capability checks.
- Rationale: Constrained permissions limit blast radius.
- Adoption signal: Features requiring platform/API permissions are gated and tested.
- Failure signal: Hidden failures from missing permissions in production.

## U-SEC-07
- Rule: Enforce dependency and supply-chain hygiene in release flow.
- Rationale: Known vulnerable packages and compromised transitive deps are common breach paths.
- Adoption signal: Dependency audit/SBOM checks run before release with defined remediation policy.
- Failure signal: Releases ship with known critical vulnerabilities.

## U-SEC-08
- Rule: Automate secret-leak detection in repository and CI workflows.
- Rationale: Exposed credentials are high-impact and often discovered too late.
- Adoption signal: Secret scanning runs on commit/PR and blocks high-confidence leaks.
- Failure signal: Tokens/keys are found after publishing artifacts or source history.
