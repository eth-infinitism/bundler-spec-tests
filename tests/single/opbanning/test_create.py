# create opcode rules

"""
 **[OP-031]** `CREATE2` is allowed exactly once in the deployment phase and must deploy code for the "sender" address.
      (Either by the factory itself, or by a utility contract it calls)
* **[OP-032]** If there is a `factory` (even unstaked), the `sender` contract is allowed to use `CREATE` opcode
    (That is, only the sender contract itself, not through utility contract)
* Staked factory creation rules:
  * **[EREP-060]** If the factory is staked, either the factory itself or the sender may use the CREATE2 and CREATE opcode
    (the sender is allowed to use the CREATE with unstaked factory, with OP-032)
  * **[EREP-061]** A staked factory may also use a utility contract that calls the `CREATE`

 if no factory, create/create2 are banned (even for staked entities: they could potentially create another account, and thus
 "blame" another userop, which we can't link back to this one)
"""

from dataclasses import dataclass
import pytest
from tests.conftest import assert_ok, deploy_contract
from tests.force_userop import force_userop
from tests.types import RPCErrorCode
from tests.user_operation_erc4337 import UserOperation
from tests.utils import (
    assert_rpc_error,
    deposit_to_undeployed_sender,
    staked_contract,
    to_hex,
    to_prefixed_hex
)


@pytest.mark.parametrize("create_op", ["CREATE", "CREATE2"])
def test_account_no_factory(rules_account_contract, create_op):
    userop = UserOperation(
        sender=rules_account_contract.address, signature=to_prefixed_hex(create_op)
    )
    assert_rpc_error(
        userop.send(),
        "account uses banned opcode: " + create_op,
        RPCErrorCode.BANNED_OPCODE,
    )


@pytest.mark.parametrize("create_op", ["CREATE", "CREATE2"])
def test_paymaster_banned_create(paymaster_contract, wallet_contract, create_op):
    userop = UserOperation(
        sender=wallet_contract.address,
        paymaster=paymaster_contract.address,
        paymasterData="0x" + to_hex(create_op),
        paymasterVerificationGasLimit=hex(300_000),
    )
    assert_rpc_error(
        userop.send(),
        "paymaster uses banned opcode: " + create_op,
        RPCErrorCode.BANNED_OPCODE,
    )


# OP-031 CREATE2 is allowed exactly once in the deployment phase.
# (so we check that it fails if it called more than once)
def test_account_create2_once(w3, factory_contract, entrypoint_contract):
    factoryData = factory_contract.functions.create(
        123, "CREATE2", entrypoint_contract.address
    ).build_transaction()["data"]
    sender = deposit_to_undeployed_sender(
        w3, entrypoint_contract, factory_contract.address, factoryData
    )
    response = UserOperation(
        sender=sender, factory=factory_contract.address, factoryData=factoryData
    ).send()
    assert_rpc_error(
        response,
        "factory",
        RPCErrorCode.BANNED_OPCODE,
    )
    assert_rpc_error(
        response,
        "CREATE2",
        RPCErrorCode.BANNED_OPCODE,
    )


# generic dataclass: can be constructed with any named param.
#
@dataclass
class Case:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def str(self):
        return ",".join([k + "=" + str(v) for k, v in self.__dict__.items()])


# [OP-031] `CREATE2` is allowed exactly once in the deployment phase and must deploy code for the "sender" address.
# [OP-032] If there is a `factory` (even unstaked), the `sender` contract is allowed to use `CREATE` opcode

# [EREP-060] If the factory is staked, either the factory itself or the sender may use the CREATE2 and CREATE opcode
# [EREP-061] A staked factory may also use a utility contract that calls the `CREATE`
account_cases = [
    Case(factory="unstaked", op="CREATE", expect="ok", rule="OP-032"),
    Case(factory="unstaked", op="CREATE2", expect="err", rule="OP-032"),
    Case(factory="staked", op="CREATE", expect="ok", rule="EREP-060"),
    Case(factory="staked", op="nested-CREATE", expect="err", rule="EREP-060"),
    Case(factory="staked", op="nested-CREATE2", expect="err", rule="EREP-060"),
    Case(factory="staked", op="CREATE2", expect="ok", rule="EREP-060"),
]


@pytest.mark.parametrize("case", account_cases, ids=Case.str)
def test_account_create_with_factory(w3, entrypoint_contract, case):
    factory = deploy_contract(
        w3, "TestRulesAccountFactory", ctrparams=[entrypoint_contract.address]
    )
    if case.factory == "staked":
        staked_contract(w3, entrypoint_contract, factory)

    factoryData = factory.functions.create(
        123, "", entrypoint_contract.address
    ).build_transaction()["data"]

    sender = deposit_to_undeployed_sender(
        w3, entrypoint_contract, factory.address, factoryData
    )

    userop = UserOperation(
        sender=sender,
        signature=to_prefixed_hex(case.op),
        factory=factory.address,
        factoryData=factoryData,
        verificationGasLimit=hex(5000000),
    )
    response = userop.send()
    if case.expect == "ok":
        assert_ok(response)
    else:
        assert_rpc_error(
            response,
            "account uses banned opcode: " + case.op.replace("nested-", ""),
            RPCErrorCode.BANNED_OPCODE,
        )
