import argparse
import random
from ruamel.yaml import YAML
from .models import (
    UserOperation,
    MetaData,
    Status,
    PooledUserOpHashesReq,
    PooledUserOpHashesRes,
    PooledUserOpsByHashReq,
    PooledUserOpsByHashRes,
)
from .random_ssz import get_random_ssz_object, RandomizationMode

SURPPORTED_TYPES = [
    UserOperation,
    MetaData,
    Status,
    PooledUserOpHashesReq,
    PooledUserOpHashesRes,
    PooledUserOpsByHashReq,
    PooledUserOpsByHashRes,
]

yaml = YAML(pure=True)
yaml.default_flow_style = None


def write_obj(type_name: str, index: int, obj, output_dir: str):
    file_name = f"{output_dir}/{type_name}/{index}.yaml"
    with open(file_name, "w", encoding="utf8") as file_description:
        yaml.dump({"data": obj.to_obj(), "ssz": obj.encode_bytes().hex()}, file_description)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Testcase generator for bundler p2p ssz objects"
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        required=True,
        help="directory which the generated test case file would be dumped",
    )
    parser.add_argument(
        "-r", "--random_seed", help="random seed used for generated test cases"
    )
    parser.add_argument(
        "-c",
        "--count-each-type",
        required=True,
        type=int,
        help="random seed used for generated test cases",
    )
    args = parser.parse_args()
    output_dir = args.output_dir
    count = args.count_each_type
    seed = (
        args.random_seed if args.random_seed else random.Random().randint(0, 10**18)
    )
    random_seed = random.Random(seed)
    print(f"Generating test cases based on seed {seed} to dir {output_dir}")

    for type_ in SURPPORTED_TYPES:
        type_name = type_.__name__
        for i in range(count):
            obj = get_random_ssz_object(
                random_seed,
                type_,
                max_bytes_length=1000,
                max_list_length=10,
                mode=RandomizationMode.RANDOM,
                chaos=True,
            )
            write_obj(type_name, i, obj, output_dir)
