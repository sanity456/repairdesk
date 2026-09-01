# RepairTeamSetCover

A reusable repair-intake board where validators derive a closed skill mask and code greedily selects the smallest registration-ordered volunteer team that covers every required workstream.

The repository is standalone and the contract is reusable: one deployment can hold multiple independent records for unrelated callers. It has no frontend and moves no funds.

## Native mechanism

multimodal skill-mask consensus -> deterministic greedy set cover -> individual volunteer acceptance.

## Actors

requester, registered volunteers, GenLayer validators.

## Source boundary

No external collection. Volunteer skills, availability, descriptions, symptoms, and images are public caller declarations and are not authenticated.

## Safety boundary

It does not diagnose faults, certify safety, authenticate skills, guarantee repairability, or replace in-person inspection.

All inputs and results are public. Untrusted public data is delimited in prompts and cannot change the closed response schema. A malformed or non-consensus model result fails without committing the intended state transition.

## Verification

    genvm-lint check contracts/repair_team_set_cover.py
    genvm-lint typecheck contracts/repair_team_set_cover.py --strict
    python -m pytest tests/direct -q -p no:cacheprovider
    python tests/run_glsim.py --port 4000 --validators 5 --no-browser
    python -m pytest tests/integration -q -s -p no:cacheprovider

See ARCHITECTURE.md, SECURITY.md, SOURCE_PROVENANCE.md, AUDIT.md, SUBMISSION_CHECKLIST.md, and deployments/studionet.json.

MIT licensed.

<!-- correction-release-start -->
## Corrected release integrity

The full twelve-repository correction audit applied both steward findings to this contract. Skill validation now binds mask and digest to the attached canonical skill payload. Volunteer catalogs are isolated per owner-created desk with fixed reclaimable slots, cases freeze one explicitly selected desk roster, and team selection cannot scan or fall back to a foreign catalog.

The current StudioNet release is `0x7a0C7B6515497F96df3cfF768df32c6299413863`. Its source bytes and full schema were read back from StudioNet and matched this repository exactly. Use `CORRECTION.md`, `REVIEW_RESPONSE.txt`, and the commit-pinned `deployments/studionet.json` for submission evidence; do not reuse the superseded address `0xFd238073c0DB65a0A5Dafc2bA6A45D90C9f456fb`.
<!-- correction-release-end -->
