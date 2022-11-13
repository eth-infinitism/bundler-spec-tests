import pytest


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

@pytest.fixture()
def url(request):
    return request.config.getoption("--url")

@pytest.fixture()
def chain_id(request):
    return request.config.getoption("--chain-id")

@pytest.fixture()
def entry_point(request):
    return request.config.getoption("--entry-point")
