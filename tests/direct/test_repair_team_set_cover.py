"""Direct tests for consensus skill masks and deterministic team cover."""

import json


IMAGE = b"public-repair-image:" + b"z" * 64


def _desk(contract, vm, owner, key="COMMUNITY"):
    vm.sender = owner
    return contract.create_desk(
        key,
        "Owner-curated public volunteer roster for scheduled repair-intake appointments.",
        "desk-service-snapshot",
    )


def _volunteer(contract, vm, owner, wallet, desk_id, key, mask):
    vm.sender = owner
    return contract.register_volunteer(
        desk_id,
        key,
        wallet,
        mask,
        "Available for scheduled public repair-intake appointments.",
    )


def _case(contract, vm, requester, desk_id):
    vm.sender = requester
    return contract.open_case("CASE-1", desk_id, "A small household device with a mechanical switch and control board.", "The switch moves but the device does not respond when activated.", IMAGE)


def _assess(contract, vm, requester, case_id, skills=None, hold=False):
    vm.sender = requester
    vm.mock_llm(r".*Identify broad repair workstreams.*", json.dumps({"required_skills": skills or ["MECHANICAL", "ELECTRICAL"], "safety_hold": hold}))
    return contract.assess_and_form_team(case_id, IMAGE)


def test_registers_skill_mask(contract, direct_vm, direct_alice, direct_bob):
    desk_id = _desk(contract, direct_vm, direct_alice)
    volunteer_id = _volunteer(contract, direct_vm, direct_alice, direct_bob, desk_id, "MECH", 1)
    assert contract.get_volunteer(volunteer_id)["skills"] == ["MECHANICAL"]


def test_rejects_empty_skill_mask(contract, direct_vm, direct_alice, direct_bob):
    desk_id = _desk(contract, direct_vm, direct_alice)
    with direct_vm.expect_revert("invalid_skill_mask"):
        _volunteer(contract, direct_vm, direct_alice, direct_bob, desk_id, "BAD", 0)


def test_case_binds_public_image(contract, direct_vm, direct_alice, direct_bob):
    desk_id = _desk(contract, direct_vm, direct_alice)
    _volunteer(contract, direct_vm, direct_alice, direct_bob, desk_id, "MECH", 1)
    case_id = _case(contract, direct_vm, direct_alice, desk_id)
    assert contract.get_case(case_id)["image_sha256"].startswith("sha256:")


def test_greedy_cover_selects_two_volunteers(contract, direct_vm, direct_alice, direct_bob, direct_charlie):
    desk_id = _desk(contract, direct_vm, direct_alice)
    first = _volunteer(contract, direct_vm, direct_alice, direct_bob, desk_id, "MECH", 1)
    second = _volunteer(contract, direct_vm, direct_alice, direct_charlie, desk_id, "ELEC", 2)
    case_id = _case(contract, direct_vm, direct_alice, desk_id)
    assert _assess(contract, direct_vm, direct_alice, case_id) == "TEAM_PENDING"
    assert [contract.get_team_member(case_id, 0), contract.get_team_member(case_id, 1)] == [first, second]


def test_uncovered_skill_is_unserviceable(contract, direct_vm, direct_alice, direct_bob):
    desk_id = _desk(contract, direct_vm, direct_alice)
    _volunteer(contract, direct_vm, direct_alice, direct_bob, desk_id, "MECH", 1)
    case_id = _case(contract, direct_vm, direct_alice, desk_id)
    assert _assess(contract, direct_vm, direct_alice, case_id, ["ELECTRICAL"]) == "UNSERVICEABLE"


def test_safety_hold_overrides_team(contract, direct_vm, direct_alice, direct_bob):
    desk_id = _desk(contract, direct_vm, direct_alice)
    _volunteer(contract, direct_vm, direct_alice, direct_bob, desk_id, "MECH", 1)
    case_id = _case(contract, direct_vm, direct_alice, desk_id)
    assert _assess(contract, direct_vm, direct_alice, case_id, ["MECHANICAL"], True) == "SAFETY_HOLD"


def test_selected_members_accept_team(contract, direct_vm, direct_alice, direct_bob, direct_charlie):
    desk_id = _desk(contract, direct_vm, direct_alice)
    _volunteer(contract, direct_vm, direct_alice, direct_bob, desk_id, "MECH", 1)
    _volunteer(contract, direct_vm, direct_alice, direct_charlie, desk_id, "ELEC", 2)
    case_id = _case(contract, direct_vm, direct_alice, desk_id)
    _assess(contract, direct_vm, direct_alice, case_id)
    direct_vm.sender = direct_bob
    assert contract.volunteer_response(case_id, True, "Mechanical volunteer accepts the public intake appointment.") == "TEAM_PENDING"
    direct_vm.sender = direct_charlie
    assert contract.volunteer_response(case_id, True, "Electrical volunteer accepts the public intake appointment.") == "TEAM_READY"


def test_bad_model_skill_preserves_open_case(contract, direct_vm, direct_alice, direct_bob):
    desk_id = _desk(contract, direct_vm, direct_alice)
    _volunteer(contract, direct_vm, direct_alice, direct_bob, desk_id, "MECH", 1)
    case_id = _case(contract, direct_vm, direct_alice, desk_id)
    with direct_vm.expect_revert("[LLM_ERROR] invalid_skill"):
        _assess(contract, direct_vm, direct_alice, case_id, ["INVENTED"])
    assert contract.get_case(case_id)["state"] == "OPEN"


def test_foreign_caller_cannot_register_into_owner_roster(contract, direct_vm, direct_alice, direct_bob):
    desk_id = _desk(contract, direct_vm, direct_alice)
    with direct_vm.expect_revert("only_desk_owner"):
        _volunteer(contract, direct_vm, direct_bob, direct_bob, desk_id, "FOREIGN", 1)
    assert contract.get_desk(desk_id)["active_volunteer_count"] == 0


def test_capacity_is_per_desk_and_reclaimable(contract, direct_vm, direct_alice, direct_bob, direct_charlie):
    first_desk = _desk(contract, direct_vm, direct_alice, "FIRST")
    second_desk = _desk(contract, direct_vm, direct_bob, "SECOND")
    first_id = ""
    for index in range(20):
        current = _volunteer(contract, direct_vm, direct_alice, direct_bob, first_desk, f"V-{index}", 1)
        if index == 0:
            first_id = current
    with direct_vm.expect_revert("desk_volunteer_limit"):
        _volunteer(contract, direct_vm, direct_alice, direct_charlie, first_desk, "FULL", 2)
    independent = _volunteer(contract, direct_vm, direct_bob, direct_charlie, second_desk, "INDEPENDENT", 2)
    assert contract.get_volunteer(independent)["desk_id"] == second_desk
    direct_vm.sender = direct_alice
    contract.remove_volunteer(first_id)
    replacement = _volunteer(contract, direct_vm, direct_alice, direct_charlie, first_desk, "REPLACEMENT", 2)
    assert contract.get_volunteer(replacement)["roster_slot"] == 0
    assert contract.get_desk(first_desk)["active_volunteer_count"] == 20


def test_case_freezes_only_selected_desk_roster(contract, direct_vm, direct_alice, direct_bob, direct_charlie):
    trusted = _desk(contract, direct_vm, direct_alice, "TRUSTED")
    foreign = _desk(contract, direct_vm, direct_bob, "FOREIGN")
    trusted_id = _volunteer(contract, direct_vm, direct_alice, direct_charlie, trusted, "TRUSTED", 1)
    foreign_id = _volunteer(contract, direct_vm, direct_bob, direct_bob, foreign, "FOREIGN", 63)
    case_id = _case(contract, direct_vm, direct_alice, trusted)
    record = contract.get_case(case_id)
    assert record["roster_volunteer_ids"] == [trusted_id]
    assert foreign_id not in record["roster_volunteer_ids"]
