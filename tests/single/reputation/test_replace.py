from tests.conftest import assert_ok, deploy_and_deposit, paymaster_contract
from tests.single.bundle.test_bundle import bump_fee_by
from tests.utils import clear_reputation, dump_mempool, dump_reputation, to_number


def bump_gas_fees(userop):
    userop.maxPriorityFeePerGas = hex(
        bump_fee_by(to_number(userop.maxPriorityFeePerGas), 15)
    )
    userop.maxFeePerGas = hex(bump_fee_by(to_number(userop.maxFeePerGas), 15))


def pm_opsSeen(pmAddr):
    reputation = dump_reputation()
    for entry in reputation:
        if entry["entryId"].lower() == pmAddr.lower():
            return to_number(entry["opsSeen"])


# when userop is replaced, old userop opsSeen increments should be reverted
def test_replace_paymaster(w3, manual_bundling_mode, entrypoint_contract, userop):
    clear_reputation()
    pm1 = deploy_and_deposit(w3, entrypoint_contract, "TestRulesPaymaster", False)

    userop.paymaster = pm1.address
    userop.paymasterVerificationGasLimit = hex(100000)
    userop.paymasterPostOpGasLimit = hex(100000)
    userop.paymasterData = "0x"

    assert_ok(userop.send())
    assert dump_mempool() == [userop]
    assert pm_opsSeen(pm1.address) == 1
    bump_gas_fees(userop)

    # replace with unmodified userop.
    assert_ok(userop.send())
    assert dump_mempool() == [userop]
    assert pm_opsSeen(pm1.address) == 1, "replace with unmodified userop"

    # replace paymaster: should "move" opsSeen to new paymaster
    pm2 = deploy_and_deposit(w3, entrypoint_contract, "TestRulesPaymaster", False)
    userop.paymaster = pm2.address

    bump_gas_fees(userop)
    assert_ok(userop.send())
    assert dump_mempool() == [userop]
    assert pm_opsSeen(pm2.address) == 1, "replaced paymaster"
    assert pm_opsSeen(pm1.address) == 0, "old paymaster should have no opsSeen"

    # remove paymaster completely:
    userop.paymaster = None
    userop.paymasterVerificationGasLimit = None
    userop.paymasterPostOpGasLimit = None
    userop.paymasterData = None
    bump_gas_fees(userop)

    assert_ok(userop.send())
    assert dump_mempool() == [userop]
    assert pm_opsSeen(pm2.address) == 0, "removed paymaster"
