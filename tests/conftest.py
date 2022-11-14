import pytest
from dataclasses import dataclass


@dataclass()
class CommandLineArgs:
    url: str
    entry_point: str
    ethereum_node: str


def pytest_addoption(parser):
    parser.addoption(
        "--url",
        action="store"
    )
    parser.addoption(
        "--chain-id",
        action="store"
    )
    parser.addoption(
        "--entry-point",
        action="store"
    )
    parser.addoption(
        "--ethereum-node",
        action="store"
    )


@pytest.fixture()
def cmd_args(request):
    return CommandLineArgs(
        url=request.config.getoption("--url"),
        entry_point=request.config.getoption("--entry-point"),
        ethereum_node=request.config.getoption("--ethereum-node")
    )
