import json
import os

import pytest
from tests.types import UserOperation


@pytest.fixture
def bad_sig_userop(wallet_contract):
    return UserOperation(
        sender=wallet_contract.address,
        callData=wallet_contract.encodeABI(fn_name="setState", args=[1111111]),
        signature="0xdead",
    )


@pytest.fixture
def invalid_sig_userop(wallet_contract):
    return UserOperation(
        sender=wallet_contract.address,
        callData=wallet_contract.encodeABI(fn_name="setState", args=[1111111]),
        signature="0xdeaf",
    )


@pytest.fixture(scope="session")
def openrpcschema():
    current_dirname = os.path.dirname(__file__)
    spec_filename = "openrpc.json"
    spec_path = os.path.realpath(current_dirname + "/../../spec/")
    with open(os.path.join(spec_path, spec_filename), encoding="utf-8") as contractfile:
        return json.load(contractfile)


@pytest.fixture
def schema(openrpcschema, schema_method):
    return next(
        m["result"]["schema"]
        for m in openrpcschema["methods"]
        if m["name"] == schema_method
    )
