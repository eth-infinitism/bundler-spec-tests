import collections
import pytest
import os
import time

from tests.types import UserOperation
from tests.utils import (
    clear_mempool,
    dump_mempool,
    deploy_and_deposit
)


#todo: relies on 'ports: [ "3001:3000" ]' for peer bundler.
BUNDLER2 = "http://localhost:3001/rpc"

#todo: this is the "real" bundler2 definition. 
# However, it can only work if the script runs inside the docker-compose environment.
# BUNDLER2 = "http://bundler2:3000/rpc"

#read mempool from the given bundler, after mempool propagation.
# refDump - a "dump_mempool" taken from that bundler before the tested operation.
# wait for the mempool to change before returning anything.
def p2p_mempool(refDump, url=None):
    count=5
    print("ref=", refDump)
    while True:
        newDump = dump_mempool(url)
        if refDump != newDump:
            return newDump
        count=count-1
        if count<=0:
            raise  Exception("timed-out waiting mempool change propagate to {0}".format(url))
        time.sleep(1)



def test_simple_p2p(w3, entrypoint_contract, manual_bundling_mode):
    wallet = deploy_and_deposit(w3, entrypoint_contract, "SimpleWallet", False)
    op = UserOperation(sender=wallet.address)

    clear_mempool()
    clear_mempool(BUNDLER2)

    ref = dump_mempool(BUNDLER2)
    op.send()
    assert dump_mempool() == [op], "failed to appear in same mempool"
    assert p2p_mempool(ref, url=BUNDLER2) == [op], "failed to propagate to remote mempool"



