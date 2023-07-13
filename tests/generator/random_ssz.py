# This file is highly inspired by
# https://github.com/ethereum/consensus-specs/blob/2cd967e2bb4f8437cdf70ecd1a8a119a005330a9/tests/core/pyspec/eth2spec/debug/random_value.py
from random import Random
from enum import Enum
from typing import Type
from remerkleable.complex import Container, List, Vector
from remerkleable.basic import uint, boolean
from remerkleable.bitfields import Bitvector, Bitlist
from remerkleable.byte_arrays import ByteVector, ByteList
from remerkleable.core import BasicView, View


# in bytes
UINT_BYTE_SIZES = (1, 2, 4, 8, 16, 32)

random_mode_names = ("random", "zero", "max", "nil", "one", "lengthy")


class RandomizationMode(Enum):
    # random content / length
    RANDOM = 0
    # Zero-value
    ZERO = 1
    # Maximum value, limited to count 1 however
    MAX = 2
    # Return 0 values, i.e. empty
    NIL_COUNT = 3
    # Return 1 value, random content
    ONE_COUNT = 4
    # Return max amount of values, random content
    MAX_COUNT = 5

    def to_name(self):
        return random_mode_names[self.value]

    def is_changing(self):
        return self.value in [0, 4, 5]

# pylint: disable=too-many-arguments,too-many-return-statements,too-many-branches,no-else-return
def get_random_ssz_object(
    rng: Random,
    typ: Type[View],
    max_bytes_length: int,
    max_list_length: int,
    mode: RandomizationMode,
    chaos: bool,
) -> View:
    """
    Create an object for a given type, filled with random data.
    :param rng: The random number generator to use.
    :param typ: The type to instantiate
    :param max_bytes_length: the max. length for a random bytes array
    :param max_list_length: the max. length for a random list
    :param mode: how to randomize
    :param chaos: if true, the randomization-mode will be randomly changed
    :return: the random object instance, of the given type.
    """
    if chaos:
        mode = rng.choice(list(RandomizationMode))
    if issubclass(typ, ByteList):
        # ByteList array
        if mode == RandomizationMode.NIL_COUNT:
            return typ(b"")
        elif mode == RandomizationMode.MAX_COUNT:
            return typ(get_random_bytes_list(rng, min(max_bytes_length, typ.limit())))
        elif mode == RandomizationMode.ONE_COUNT:
            return typ(get_random_bytes_list(rng, min(1, typ.limit())))
        elif mode == RandomizationMode.ZERO:
            return typ(b"\x00" * min(1, typ.limit()))
        elif mode == RandomizationMode.MAX:
            return typ(b"\xff" * min(1, typ.limit()))
        else:
            return typ(
                get_random_bytes_list(
                    rng, rng.randint(0, min(max_bytes_length, typ.limit()))
                )
            )
    if issubclass(typ, ByteVector):
        # Random byte vectors can be bigger than max bytes size, e.g. custody chunk data.
        # No max-bytes-length limitation here.
        if mode == RandomizationMode.ZERO:
            return typ(b"\x00" * typ.type_byte_length())
        elif mode == RandomizationMode.MAX:
            return typ(b"\xff" * typ.type_byte_length())
        else:
            return typ(get_random_bytes_list(rng, typ.type_byte_length()))
    elif issubclass(typ, (uint, boolean)):
        # Basic types
        if mode == RandomizationMode.ZERO:
            return get_min_basic_value(typ)
        elif mode == RandomizationMode.MAX:
            return get_max_basic_value(typ)
        else:
            return get_random_basic_value(rng, typ)
    elif issubclass(typ, (Vector, Bitvector)):
        elem_type = typ.element_cls() if issubclass(typ, Vector) else boolean
        return typ(
            get_random_ssz_object(
                rng, elem_type, max_bytes_length, max_list_length, mode, chaos
            )
            for _ in range(typ.vector_length())
        )
    elif issubclass(typ, List) or issubclass(typ, Bitlist):
        length = rng.randint(0, min(typ.limit(), max_list_length))
        if mode == RandomizationMode.ONE_COUNT:
            length = 1
        elif mode == RandomizationMode.MAX_COUNT:
            length = max_list_length
        elif mode == RandomizationMode.NIL_COUNT:
            length = 0

        if (
            typ.limit() < length
        ):  # SSZ imposes a hard limit on lists, we can't put in more than that
            length = typ.limit()

        elem_type = typ.element_cls() if issubclass(typ, List) else boolean
        return typ(
            get_random_ssz_object(
                rng, elem_type, max_bytes_length, max_list_length, mode, chaos
            )
            for _ in range(length)
        )
    elif issubclass(typ, Container):
        fields = typ.fields()
        # Container
        return typ(
            **{
                field_name: get_random_ssz_object(
                    rng, field_type, max_bytes_length, max_list_length, mode, chaos
                )
                for field_name, field_type in fields.items()
            }
        )
    else:
        raise Exception(f"Type not recognized: typ={typ}")
# pylint: enable=too-many-arguments,too-many-return-statements,too-many-branches

def get_random_bytes_list(rng: Random, length: int) -> bytes:
    return bytes(rng.getrandbits(8) for _ in range(length))


def get_random_basic_value(rng: Random, typ) -> BasicView:
    if issubclass(typ, boolean):
        return typ(rng.choice((True, False)))
    elif issubclass(typ, uint):
        assert typ.type_byte_length() in UINT_BYTE_SIZES
        return typ(rng.randint(0, 256 ** typ.type_byte_length() - 1))
    else:
        raise ValueError(f"Not a basic type: typ={typ}")


def get_min_basic_value(typ) -> BasicView:
    if issubclass(typ, boolean):
        return typ(False)
    elif issubclass(typ, uint):
        assert typ.type_byte_length() in UINT_BYTE_SIZES
        return typ(0)
    else:
        raise ValueError(f"Not a basic type: typ={typ}")


def get_max_basic_value(typ) -> BasicView:
    if issubclass(typ, boolean):
        return typ(True)
    elif issubclass(typ, uint):
        assert typ.type_byte_length() in UINT_BYTE_SIZES
        return typ(256 ** typ.type_byte_length() - 1)
    else:
        raise ValueError(f"Not a basic type: typ={typ}")
