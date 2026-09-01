# Security

All contract data is public. Do not submit secrets, private documents, personal data, or private images.

Threat controls include bounded ASCII inputs, closed identifiers and model responses, prompt delimiting, exact consensus comparison, role checks, duplicate-state guards, content fingerprints where relevant, deterministic post-consensus algorithms, and no fund custody.

Residual boundary: It does not diagnose faults, certify safety, authenticate skills, guarantee repairability, or replace in-person inspection.

Report a vulnerability privately to the repository owner before public disclosure.

<!-- correction-release-start -->
## Corrected review controls

- Leader output is not trusted merely because a leader-provided digest matches an independently computed digest.
- The leader's substantive attached payload is canonicalized, its derived values are recomputed, and the full payload is independently compared.
- Consensus output is canonicalized and rebound again immediately before state mutation.
- Catalog ownership, per-catalog capacity, and reclaim behavior are enforced.
- Active deployment evidence is valid only when source bytes, full ABI/schema, address, transaction, and commit-pinned links resolve to the same release.
<!-- correction-release-end -->
