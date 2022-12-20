# import pytest
# from web3 import Web3
# from tests.utils import (
#     deploy_contract,
#     compile_contract,
#     deploy_wallet_contract,
#     dumpMempool,
# )
# from tests.types import CommandLineArgs, UserOperation
# import jsonrpcclient
#
# w3 = None
# entryPoint = None
#
#
# def save_w3(saved_w3):
#     global w3
#     w3 = saved_w3
#     compiled = compile_contract("EP")
#     global entryPoint
#     entryPoint = w3.eth.contract(
#         abi=compiled["abi"], address=CommandLineArgs.entryPoint
#     )
#
#
# def test_save_w3(w3, setBundleInterval):
#     print("saving w3..")
#     save_w3(w3)
#
#
# # expect test to add exactly one entry to the mempool
# @pytest.fixture
# def addToPool(clearState):
#     yield
#     mempool = dumpMempool()
#     # assert len(mempool) == 1
#
#
# # expect test not to add anything to mempool
# @pytest.fixture
# def noAdd(clearState):
#     yield
#     assert dumpMempool() == []
#
#
# # todo: any better way to convert string to hex, e.g. using  web3.py ?
# def tohex(str, prefix=True):
#     return ("0x" if prefix else "") + "".join(
#         [format(ord(x), "02x") for x in list(str)]
#     )
#
#
# def depositTo(addr, value):
#     # entryPoint.functions.depositTo(addr, dict(value=value))
#     encoded = entryPoint.encodeABI(fn_name="depositTo", args=[addr])
#     print("deposit=", encoded)
#     # entryPoint.functions.depositTo(self.paymasterAddr, {'value':1})
#
#
# class BaseTestPaymaster:
#     @classmethod
#     def setup_class(self):
#         self.init()
#
#     @classmethod
#     def init(self):
#         assert w3 is not None
#         self.paymaster = deploy_contract(w3, "TestRulesPaymaster")
#         self.paymasterAddr = self.paymaster.address
#         account = w3.eth.accounts[0]
#         entryPoint.functions.depositTo(self.paymasterAddr).transact(
#             {"from": account, "value": Web3.toWei(1, "ether")}
#         )
#         # no need for deposit... paymaster pays for them.
#         a = deploy_contract(w3, "TestRulesAccount", [entryPoint.address])
#         self.a = a.address
#         self.b = deploy_contract(w3, "TestRulesAccount", [entryPoint.address]).address
#
#     # helper: send userOp with given rule for paymaster
#     # sender is filled from
#     # - initcode, if specified
#     # - sender, if specified
#     # - otherwise, from self.a
#     def send(self, paymasterRule, **kw):
#         if kw.get("initCode") is not None:
#             sender = entryPoint.functions.getSenderAddress(kw["initCode"]).call()
#         else:
#             sender = kw.get("sender") or self.a
#         kw["sender"] = sender
#         op = UserOperation(
#             paymasterAndData=self.createPaymasterAndData(paymasterRule), **kw
#         )
#         ret = op.send()
#         if isinstance(ret, jsonrpcclient.Ok):
#             return ret.result
#         else:
#             print("sender=", op.sender, "paymasdter=", op.paymasterAndData[:42])
#             ex = Exception(ret.message)
#             ex.data = ret.data
#             ex.code = ret.code
#             raise ex
#
#     def createPaymasterAndData(self, rule):
#         return self.paymasterAddr + tohex(rule, prefix=False)
#
#
# class TestUnstakedPaymaster(BaseTestPaymaster):
#     def test_nostorage(self, addToPool):
#         self.send("")
#
#     def te1st_acct_ref_storage_no_initCode(self, addToPool):
#         self.send("acct-balance")
#
#     # def createInitCode(self):
#     #     factory = deploy_contract(w3, 'TestFactory')
#     #     return factory.address
#
#     # def test_acct_ref_storage_with_initCode(self, noAdd):
#     #     with pytest.raises(Exception, match='asd'):
#     #         self.send('acct-ref', initCode=self.createInitCode())
#
#     def test_acct_self_storage(self, addToPool):
#         self.send("acct-self")
#
#     def test_selfstorage_revert(self, noAdd):
#         with pytest.raises(Exception, match="unstaked paymaster accessed its own"):
#             self.send("self-storage")
#
#     def test_context_revert(self, noAdd):
#         with pytest.raises(Exception, match="unstaked paymaster.*context"):
#             self.send("context")
#
#     def test_many_throttle_to_1(self, addToPool):
#         op = self.send("")
#         with pytest.raises(Exception, match="unstaked paymaster.*too many"):
#             self.send("", sender=self.b)
#         assert dumpMempool() == [op]
#
#
# class TestStakedPaymaster(BaseTestPaymaster):
#     @classmethod
#     def setup_class(self):
#         self.init()
#         account = w3.eth.accounts[0]
#         self.paymaster.functions.addStake(entryPoint.address, 1).transact(
#             {"from": account, "value": Web3.toWei(1, "ether")}
#         )
#
#     def test_selfstorage(self, addToPool):
#         self.send("self-storage")
#
#     def test_context(self, addToPool):
#         self.send("context")
#
#     def test_many(self):
#         op1 = self.send("")
#         op2 = self.send("", sender=self.b)
#         assert dumpMempool() == [op1, op2]
