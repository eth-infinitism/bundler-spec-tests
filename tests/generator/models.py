from remerkleable.complex import Container, List
from remerkleable.basic import (
    uint64,
    uint256,
)
from remerkleable.bitfields import Bitvector
from remerkleable.byte_arrays import ByteVector, ByteList

MAX_OPS_PER_REQUEST = 4096  # based on the bundler p2p spec
MAX_BYTES_LENGTH = 4096  # There is actually not hard limit for the max bytes but ssz require maximum length
MEMPOOL_SUBNET_COUNT = 8  # unspcified in the spec

Address = ByteVector[20]

# pylint: disable=too-many-ancestors
class UserOperation(Container):
    sender: Address
    nonce: uint256
    init_data: ByteList[MAX_BYTES_LENGTH]
    call_data: ByteList[MAX_BYTES_LENGTH]
    call_gas_limit: uint256
    verification_gas_limit: uint256
    pre_verification_gas: uint256
    max_fee_per_gas: uint256
    max_priority_fee_per_gas: uint256
    paymaster_and_data: ByteList[MAX_BYTES_LENGTH]
    signature: ByteList[MAX_BYTES_LENGTH]


class MetaData(Container):
    seq_number: uint64
    mempool_nets: Bitvector[MEMPOOL_SUBNET_COUNT]


Status = List[ByteVector[32], MAX_OPS_PER_REQUEST]


class PooledUserOpHashesReq(Container):
    mempool: ByteVector[32]
    offset: uint64


class PooledUserOpHashesRes(Container):
    more_flag: uint64
    hashes: List[ByteVector[32], MAX_OPS_PER_REQUEST]


class PooledUserOpsByHashReq(Container):
    hashes: List[ByteVector[32], MAX_OPS_PER_REQUEST]


PooledUserOpsByHashRes = List[UserOperation, MAX_OPS_PER_REQUEST]
