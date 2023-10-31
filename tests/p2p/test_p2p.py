import collections
import pytest
import os
import time

from tests.types import UserOperation
from tests.utils import (
    clear_mempool,
    deploy_and_deposit,
    dump_mempool,
    p2p_mempool,
    set_manual_bundling_mode
)


#todo: relies on 'ports: [ "3001:3000" ]' for peer bundler.
BUNDLER2 = "http://localhost:3001/rpc"

#todo: this is the "real" bundler2 definition. 
# However, it can only work if the script runs inside the docker-compose environment.
# BUNDLER2 = "http://bundler2:3000/rpc"

# Sanity test: make sure a simple userop is propagated
def test_simple_p2p(w3, entrypoint_contract, manual_bundling_mode):
    wallet = deploy_and_deposit(w3, entrypoint_contract, "SimpleWallet", False)
    op = UserOperation(sender=wallet.address)

    set_manual_bundling_mode(BUNDLER2)
    clear_mempool()
    clear_mempool(BUNDLER2)

    ref = dump_mempool(BUNDLER2)
    op.send()
    assert dump_mempool() == [op], "failed to appear in same mempool"
    assert p2p_mempool(ref, url=BUNDLER2) == [op], "failed to propagate to remote mempool"



