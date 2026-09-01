"""Adversarial skill-assessment payload binding regressions."""

import hashlib
import json

from tests.direct.test_repair_team_set_cover import IMAGE, _assess, _case, _desk, _volunteer


def _hash(skills, hold):
    value = {"required_skills": sorted(skills), "safety_hold": hold}
    wire = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return "sha256:" + hashlib.sha256(wire.encode("ascii")).hexdigest()


FORGED = {
    "required_skills": ["MECHANICAL"],
    "required_mask": 1,
    "safety_hold": False,
    "assessment_sha256": _hash(["MECHANICAL", "ELECTRICAL"], False),
}


def _prepared(contract, vm, owner, mechanical, electrical):
    desk_id = _desk(contract, vm, owner)
    _volunteer(contract, vm, owner, mechanical, desk_id, "MECH", 1)
    _volunteer(contract, vm, owner, electrical, desk_id, "ELEC", 2)
    case_id = _case(contract, vm, owner, desk_id)
    return case_id


def test_validator_rejects_changed_skills_with_honest_hash(contract, direct_vm, direct_alice, direct_bob, direct_charlie):
    case_id = _prepared(contract, direct_vm, direct_alice, direct_bob, direct_charlie)
    _assess(contract, direct_vm, direct_alice, case_id)
    assert direct_vm.run_validator(leader_result=FORGED) is False


def test_validator_rejects_mask_not_derived_from_skill_list(contract, direct_vm, direct_alice, direct_bob, direct_charlie):
    case_id = _prepared(contract, direct_vm, direct_alice, direct_bob, direct_charlie)
    _assess(contract, direct_vm, direct_alice, case_id)
    forged = dict(FORGED)
    forged["required_skills"] = ["ELECTRICAL", "MECHANICAL"]
    assert direct_vm.run_validator(leader_result=forged) is False


def test_validator_accepts_honest_complete_assessment(contract, direct_vm, direct_alice, direct_bob, direct_charlie):
    case_id = _prepared(contract, direct_vm, direct_alice, direct_bob, direct_charlie)
    _assess(contract, direct_vm, direct_alice, case_id)
    assert direct_vm.run_validator() is True


def test_post_consensus_forgery_preserves_open_case(contract, direct_vm, direct_alice, direct_bob, direct_charlie, monkeypatch):
    from genlayer import gl

    case_id = _prepared(contract, direct_vm, direct_alice, direct_bob, direct_charlie)
    before = contract.get_case(case_id)
    direct_vm.sender = direct_alice
    monkeypatch.setattr(gl.vm, "run_nondet_unsafe", lambda *args: FORGED)
    with direct_vm.expect_revert("assessment_hash_mismatch"):
        contract.assess_and_form_team(case_id, IMAGE)
    assert contract.get_case(case_id) == before
