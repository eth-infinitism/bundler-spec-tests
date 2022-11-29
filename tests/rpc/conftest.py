import pytest

from tests.types import UserOperation


@pytest.fixture
def userOp(wallet_contract):
    return UserOperation(
        wallet_contract.address,
        hex(0),
        '0x',
        wallet_contract.encodeABI(fn_name='setState', args=[1111111]),
        hex(30000),
        hex(1213945),
        hex(47124),
        hex(2107373890),
        hex(1500000000),
        '0x',
        '0xface'
    )


@pytest.fixture
def badSigUserOp(wallet_contract):
    return UserOperation(
        wallet_contract.address,
        hex(0),
        '0x',
        wallet_contract.encodeABI(fn_name='setState', args=[1111111]),
        hex(30000),
        hex(1213945),
        hex(47124),
        hex(2107373890),
        hex(1500000000),
        '0x',
        '0xdead'
    )
