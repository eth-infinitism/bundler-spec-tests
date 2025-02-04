pragma solidity ^0.8;
// SPDX-License-Identifier: GPL-3.0

import "@account-abstraction/node_modules/@openzeppelin/contracts/proxy/Proxy.sol";

contract TestProxy is Proxy {
    address immutable impl;

    constructor(address _impl) {
        impl = _impl;
    }

    function _implementation() internal view override returns (address) {
        return impl;
    }
}
