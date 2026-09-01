import hashlib
import json
from pathlib import Path

from gltest import get_contract_factory, get_validator_factory
from gltest.accounts import create_accounts
from gltest.assertions import tx_execution_succeeded
from gltest.types import TransactionStatus
from gltest.utils import extract_contract_address


def _ok(receipt):
    assert tx_execution_succeeded(receipt), json.dumps(receipt, default=str)


def _context(fragment, response):
    validators = get_validator_factory().batch_create_mock_validators(
        5,
        mock_llm_response={"nondet_exec_prompt": {fragment: json.dumps(response)}},
    )
    return {
        "validators": [validator.to_dict() for validator in validators],
        "genvm_datetime": "2026-08-25T12:00:00Z",
    }


def _deploy(contract_file, owner_account):
    factory = get_contract_factory(
        contract_file_path=Path(__file__).resolve().parents[2] / "contracts" / contract_file
    )
    receipt = factory.deploy_contract_tx(
        args=[],
        account=owner_account,
        wait_transaction_status=TransactionStatus.FINALIZED,
    )
    _ok(receipt)
    return factory, extract_contract_address(receipt)


def _send(method, args, context=None):
    if context is None:
        receipt = method(args=args).transact(
            wait_transaction_status=TransactionStatus.FINALIZED
        )
    else:
        receipt = method(args=args).transact(
            transaction_context=context,
            wait_transaction_status=TransactionStatus.FINALIZED,
        )
    _ok(receipt)
    return receipt


def test_five_validator_skill_assessment_and_team_cover_flow():
    requester_account, mechanical_account, electrical_account = create_accounts(3)
    factory, address = _deploy("repair_team_set_cover.py", requester_account)
    requester = factory.build_contract(address, account=requester_account)
    mechanical = factory.build_contract(address, account=mechanical_account)
    electrical = factory.build_contract(address, account=electrical_account)
    desk_id = f"{str(requester_account.address).lower()}:COMMUNITY"
    case_id = f"{str(requester_account.address).lower()}:CASE-1"
    image = b"public-repair-image:" + b"z" * 64
    _send(requester.create_desk, ["COMMUNITY", "Owner-curated public volunteer roster for scheduled repair-intake appointments.", "desk-service-snapshot"])
    _send(requester.register_volunteer, [desk_id, "MECH", mechanical_account.address, 1, "Available for scheduled public repair-intake appointments."])
    _send(requester.register_volunteer, [desk_id, "ELEC", electrical_account.address, 2, "Available for scheduled public repair-intake appointments."])
    _send(requester.open_case, [
        "CASE-1",
        desk_id,
        "A small household device with a mechanical switch and control board.",
        "The switch moves but the device does not respond when activated.",
        image,
    ])
    _send(
        requester.assess_and_form_team,
        [case_id, image],
        _context("Identify broad repair workstreams", {"required_skills": ["MECHANICAL", "ELECTRICAL"], "safety_hold": False}),
    )
    _send(mechanical.volunteer_response, [case_id, True, "Mechanical volunteer accepts the public intake appointment."])
    _send(electrical.volunteer_response, [case_id, True, "Electrical volunteer accepts the public intake appointment."])
    assert requester.get_case(args=[case_id]).call()["state"] == "TEAM_READY"
