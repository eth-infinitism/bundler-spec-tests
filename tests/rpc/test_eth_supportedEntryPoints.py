from tests.types import RPCRequest

def test_eth_supportedEntryPoints(cmd_args):
    response = RPCRequest(method="eth_supportedEntryPoints").send(cmd_args.url)
    supportedEPs = response.result
    assert len(supportedEPs) == 1
    assert supportedEPs[0] == cmd_args.entry_point
