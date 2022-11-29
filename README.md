# EIP4337 bundler compatibility tests.

#### Prerequisites 

Python version 3.8+
PDM - python package and dependency manager version 2.2.1+

#### Installation
Run `pdm install && git submodule update --init --recursive`
#### Running the tests

While running your bundler, open another windown and run
```sh
pdm run pytest --url <bundler_url> --entry-point <entry_point> --ethereum-node <ethereum_node_url>
```
