# EIP4337 bundler compatibility tests.

## Version 0.7

For more information on the motivation and importance of having a compatibility test suite, see https://notes.ethereum.org/@yoav/unified-erc-4337-mempool

For the formal schema EIP-4337 bundler RPC API spec, see https://github.com/eth-infinitism/bundler-spec

The spec test for previous release is at [releases/v0.6](https://github.com/eth-infinitism/bundler-spec-tests/tree/releases/v0.6)

#### Prerequisites 

Python version 3.8+
PDM - python package and dependency manager version 2.2.1+

#### Installation
Run `pdm install && pdm run update-deps`

#### Running the tests

##### Running with an up and running Ethereum node and bundler
Assuming you already have an Ethereum node running, EntryPoint deployed and your bundler running and ready for requests, you can run the test suite with:
```shell script
pdm test
```
With the following parameters:

  * **--url** the bundler to test (defaults to http://localhost:3000)
  * **--entry-point** (defaults to `0x0000000071727De22E5E9d8BAf0edAc6f37da032`)
  * **--ethereum-node** (defaults to http://localhost:8545)
  * **--launcher-script** (See below)
  * **-k** &lt;regex>, (or any other pytest param)

##### Running with a launcher script
You can provide a launcher script by adding the option `--launcher-script` to the command line.

Your launcher script will be invoked by the shell with:
```shell script
<launcher-script-file> {start|stop|restart}
```  
where:
- `start` should start an Ethereum node, deploy an EntryPoint contract and start your bundler.
- `stop` should terminate both the Ethereum node and your bundler processes, and cleanup if necessary.
- `restart` should stop and start atomically.  


##### Running using the "test executor"

See https://github.com/eth-infinitism/bundler-test-executor, for the test executor to run the test suite against all registered bundler implementations.
