# Architecture

Project: RepairTeamSetCover

Reusable primitive: multimodal skill-mask consensus -> deterministic greedy set cover -> individual volunteer acceptance.

The contract separates caller-attested public inputs, validator-agreed semantic fields, deterministic state transitions, and role-bound final actions. It stores canonical JSON strings in GenVM maps, validates every identifier and bound before consensus, and keeps source references explicitly unverified.

The mechanism is not a renamed assessment record. Its state transitions, role topology, storage layout, deterministic algorithm, and public ABI are specific to this project.

<!-- correction-release-start -->
## Consensus and storage safety boundary

Skill validation now binds mask and digest to the attached canonical skill payload. Volunteer catalogs are isolated per owner-created desk with fixed reclaimable slots, cases freeze one explicitly selected desk roster, and team selection cannot scan or fall back to a foreign catalog.

The on-chain state transition consumes only the canonical value returned by the post-consensus binding boundary. Operational records are isolated by an explicitly selected owner catalog, and fixed capacity is scoped or reclaimable.
<!-- correction-release-end -->
