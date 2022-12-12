# EIP4337 bundler compatibility tests.

#### Prerequisites 

Python version 3.8+
PDM - python package and dependency manager version 2.2.1+

#### Installation
Run `pdm install && git submodule update --init --recursive`

#### Running the tests

##### Running with an up and running Ethereum node and bundler
Assuming you already have an Ethereum node running, EntryPoint deployed and your bundler running and ready for requests, you can run the test suite with:
```shell script
pdm run pytest -rA -W ignore::DeprecationWarning --url <bundler_url> --entry-point <entry_point> --ethereum-node <ethereum_node_url>
```

##### Running with a launcher script
You can provide a launcher script by adding the option `--launcher-script` to the command:
```shell script
pdm run pytest -rA -W ignore::DeprecationWarning --url <bundler_url> --entry-point <entry_point> --ethereum-node <ethereum_node_url> --launcher-script <launcher-script-file>
```

Your launcher script will be invoked by shell with:
```shell script
<launcher-script-file> {start|stop|restart}
```  
where:
- `start` should start an Ethereum node, deploy an EntryPoint contract and start your bundler.
- `stop` should terminate both the Ethereum node and your bundler processes, and cleanup if necessary.
- `restart` should stop and start atomically.  
