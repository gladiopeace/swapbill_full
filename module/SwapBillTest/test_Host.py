from __future__ import print_function
import unittest, shutil, os, binascii
from os import path
from SwapBill import Host, RPC
from SwapBillTest import MockRPC

# litecoin testnet address versions
addressVersion = b'\x6f'
privateKeyAddressVersion = b'\xef'

dataDirectory = 'dataDirectoryForTests'

def InitHost(rpcHost):
	if path.exists(dataDirectory):
		assert path.isdir(dataDirectory)
		shutil.rmtree(dataDirectory)
	os.mkdir(dataDirectory)
	submittedTransactionsLogFileName = path.join(dataDirectory, 'submittedTransactions.txt')
	return Host.Host(rpcHost=rpcHost, addressVersion=addressVersion, privateKeyAddressVersion=privateKeyAddressVersion, submittedTransactionsLogFileName=submittedTransactionsLogFileName)

class Test(unittest.TestCase):

	def test_setup(self):
		rpcHost = MockRPC.Host()
		host = InitHost(rpcHost);

	def test_get_unspent(self):
		rpcHost = MockRPC.Host()
		host = InitHost(rpcHost);
		expectedQuery = ('listunspent',)
		queryResult = [
		    {'scriptPubKey': '76a914ea9273c05d44d57317274f252df2b7605c5e1d7e88ac', 'confirmations': 47, 'account': '', 'txid': 'c4d9603031f72b948e434f09c6d7c95d2a031ee18534b41760d8f12ed54948a5', 'address': 'n2uFrchnqXnEfcX8ewoGZyHQNCNp8cxcPk', 'vout': 2, 'amount': 899.998},
		    {'scriptPubKey': '76a914707c085200b226a7a39080c2a58468debe0b8e6f88ac', 'confirmations': 48, 'account': '', 'txid': 'f0205c8be59f924e79d1c02d91342dfcc791a0e9acc7c780b38e9c1235c6d896', 'address': 'mqmiZU7cFg4czRPiU55wfQEBgPmnRzZ7kW', 'vout': 1, 'amount': 1000.0}
		]
		rpcHost.queue.append((expectedQuery, queryResult))
		unspent = host.getUnspent()
		self.assertEqual(unspent, [
		    {'txid': 'f0205c8be59f924e79d1c02d91342dfcc791a0e9acc7c780b38e9c1235c6d896', 'scriptPubKey': '76a914707c085200b226a7a39080c2a58468debe0b8e6f88ac', 'address': b'p|\x08R\x00\xb2&\xa7\xa3\x90\x80\xc2\xa5\x84h\xde\xbe\x0b\x8eo', 'vout': 1, 'amount': 100000000000},
		    {'txid': 'c4d9603031f72b948e434f09c6d7c95d2a031ee18534b41760d8f12ed54948a5', 'scriptPubKey': '76a914ea9273c05d44d57317274f252df2b7605c5e1d7e88ac', 'address': b"\xea\x92s\xc0]D\xd5s\x17'O%-\xf2\xb7`\\^\x1d~", 'vout': 2, 'amount': 89999800000},
		])

	def test_unspent_sorting(self):
		rpcHost = MockRPC.Host()
		host = InitHost(rpcHost);
		expectedQuery = ('listunspent',)
		spk = '76a914707c085200b226a7a39080c2a58468debe0b8e6f88ac'
		txid = 'f0205c8be59f924e79d1c02d91342dfcc791a0e9acc7c780b38e9c1235c6d896'
		adr = 'mqmiZU7cFg4czRPiU55wfQEBgPmnRzZ7kW'
		pubKeyHash = b'p|\x08R\x00\xb2&\xa7\xa3\x90\x80\xc2\xa5\x84h\xde\xbe\x0b\x8eo'
		queryResult = [
		    {'scriptPubKey':spk , 'confirmations':47, 'account':'', 'txid':txid, 'address':adr, 'vout':1, 'amount':1.0},
		    {'scriptPubKey':spk , 'confirmations':48, 'account':'', 'txid':txid, 'address':adr, 'vout':1, 'amount':2.0},
		    {'scriptPubKey':spk , 'confirmations':10, 'account':'', 'txid':txid, 'address':adr, 'vout':1, 'amount':3.0},
		    {'scriptPubKey':spk , 'confirmations':11, 'account':'', 'txid':txid, 'address':adr, 'vout':1, 'amount':4.0},
		    {'scriptPubKey':spk , 'confirmations':60, 'account':'', 'txid':txid, 'address':adr, 'vout':1, 'amount':5.0},
		    {'scriptPubKey':spk , 'confirmations':45, 'account':'', 'txid':txid, 'address':adr, 'vout':1, 'amount':6.0},
		]
		rpcHost.queue.append((expectedQuery, queryResult))
		unspent = host.getUnspent()
		self.assertEqual(unspent, [
		    {'txid':txid, 'scriptPubKey':spk, 'address':pubKeyHash, 'vout':1, 'amount':500000000},
		    {'txid':txid, 'scriptPubKey':spk, 'address':pubKeyHash, 'vout':1, 'amount':200000000},
		    {'txid':txid, 'scriptPubKey':spk, 'address':pubKeyHash, 'vout':1, 'amount':100000000},
		    {'txid':txid, 'scriptPubKey':spk, 'address':pubKeyHash, 'vout':1, 'amount':600000000},
		    {'txid':txid, 'scriptPubKey':spk, 'address':pubKeyHash, 'vout':1, 'amount':400000000},
		    {'txid':txid, 'scriptPubKey':spk, 'address':pubKeyHash, 'vout':1, 'amount':300000000},
		])

	def doConvertTest(self, amountJSONFloat, expectedSatoshis):
		rpcHost = MockRPC.Host()
		host = InitHost(rpcHost);
		expectedQuery = ('listunspent',)
		queryResult = [
		    {'scriptPubKey': '76a914707c085200b226a7a39080c2a58468debe0b8e6f88ac', 'confirmations': 48, 'account': '', 'txid': 'f0205c8be59f924e79d1c02d91342dfcc791a0e9acc7c780b38e9c1235c6d896', 'address': 'mqmiZU7cFg4czRPiU55wfQEBgPmnRzZ7kW', 'vout': 1, 'amount': amountJSONFloat}]
		rpcHost.queue.append((expectedQuery, queryResult))
		unspent = host.getUnspent()
		self.assertEqual(unspent, [
		    {'txid': 'f0205c8be59f924e79d1c02d91342dfcc791a0e9acc7c780b38e9c1235c6d896', 'scriptPubKey': '76a914707c085200b226a7a39080c2a58468debe0b8e6f88ac', 'address': b'p|\x08R\x00\xb2&\xa7\xa3\x90\x80\xc2\xa5\x84h\xde\xbe\x0b\x8eo', 'vout': 1, 'amount': expectedSatoshis}
		])
	def test_get_unspent_float_convert(self):
		self.doConvertTest(8.83, 883000000)
		self.doConvertTest(0.00000001, 1)
		self.doConvertTest(0.00000002, 2)
		self.doConvertTest(0.00000003, 3)
		self.doConvertTest(10000.00000001, 1000000000001)
		self.doConvertTest(900000.00000001, 90000000000001)
		self.doConvertTest(9000000.00000001, 900000000000001)
		# *** ran out of float precision here, by the looks of things, when I tried this
		#self.doConvertTest(90000000.00000001, 9000000000000001)

	def test_new_address(self):
		rpcHost = MockRPC.Host()
		host = InitHost(rpcHost);
		expectedQuery = ('getnewaddress',)
		queryResult = 'mujT1HnMuekKoNRdKG5h1YWwXYb5orcJ7h'
		rpcHost.queue.append((expectedQuery, queryResult))
		address = host.getManagedAddress()
		self.assertEqual(address, b'\x9b\xee\xb8\x1f\x07Lo\x9c\xe8?\x9d\x1b\xf1\xda2\xbf\x8bVE\xbb')

	def test_sign_without_swapbill_inputs(self):
		rpcHost = MockRPC.Host()
		host = InitHost(rpcHost);
		# burn transaction, no private keys supplied
		expectedQuery = ('signrawtransaction', '0100000001b05cc2f613103155a269afef52d9c7b315c753f787b5d6ce35f27b0c4e62f274040000001976a91430ba34c619b0eb22a2938df756f658bbf9ca7c1488acffffffff0300e1f505000000001976a914534200000000000000000000000000000000000088aca0860100000000001976a914a58cbff63bce0e8c594892e5c5ee9822bbca78ae88acba5d1d09010000001976a914dcdc3c70d70a0a839e6a38eac17312cd0df289eb88ac00000000')
		queryResult = {'complete': True, 'hex': '0100000001b05cc2f613103155a269afef52d9c7b315c753f787b5d6ce35f27b0c4e62f274040000006b483045022100b56798fed395bb462cc9f4954ad4a50a6a2b71618bb58812ba16d96c53fcae7802200be93e0347d67ed76d4be3b9f49287d57d0e65e18a0106dd4950fb579a6c0d3301210315d3cd37fe4bb353fd901326a0860d86dbe304fe90f0253f4239fb6cc16d0a9fffffffff0300e1f505000000001976a914534200000000000000000000000000000000000088aca0860100000000001976a914a58cbff63bce0e8c594892e5c5ee9822bbca78ae88acba5d1d09010000001976a914dcdc3c70d70a0a839e6a38eac17312cd0df289eb88ac00000000'}
		rpcHost.queue.append((expectedQuery, queryResult))
		expectedQuery = ('sendrawtransaction', '0100000001b05cc2f613103155a269afef52d9c7b315c753f787b5d6ce35f27b0c4e62f274040000006b483045022100b56798fed395bb462cc9f4954ad4a50a6a2b71618bb58812ba16d96c53fcae7802200be93e0347d67ed76d4be3b9f49287d57d0e65e18a0106dd4950fb579a6c0d3301210315d3cd37fe4bb353fd901326a0860d86dbe304fe90f0253f4239fb6cc16d0a9fffffffff0300e1f505000000001976a914534200000000000000000000000000000000000088aca0860100000000001976a914a58cbff63bce0e8c594892e5c5ee9822bbca78ae88acba5d1d09010000001976a914dcdc3c70d70a0a839e6a38eac17312cd0df289eb88ac00000000')
		queryResult = '9531adb0b8a47cca5779ddf979af8668fcfedf595388dc8687c60a144c286bad'
		rpcHost.queue.append((expectedQuery, queryResult))
		unsignedTransactionHex = '0100000001b05cc2f613103155a269afef52d9c7b315c753f787b5d6ce35f27b0c4e62f274040000001976a91430ba34c619b0eb22a2938df756f658bbf9ca7c1488acffffffff0300e1f505000000001976a914534200000000000000000000000000000000000088aca0860100000000001976a914a58cbff63bce0e8c594892e5c5ee9822bbca78ae88acba5d1d09010000001976a914dcdc3c70d70a0a839e6a38eac17312cd0df289eb88ac00000000'
		privateKeys = []
		maximumSignedSize = 999
		txID = host.signAndSend(unsignedTransactionHex, privateKeys, maximumSignedSize)
		self.assertEqual(txID, '9531adb0b8a47cca5779ddf979af8668fcfedf595388dc8687c60a144c286bad')

	def test_sign_with_swapbill_inputs(self):
		rpcHost = MockRPC.Host()
		host = InitHost(rpcHost);
		# ltc buy offer, with private key supplied for one swapbill input
		unsignedTransactionHex = '0100000003296b1b3c9ec3a104e5f5369825ab367fa06f9465c43b422e298e4ab1edc7b631010000001976a9144454f61033d4968c825894206082a0e1fefac51488acffffffff296b1b3c9ec3a104e5f5369825ab367fa06f9465c43b422e298e4ab1edc7b631020000001976a914deb5c235b1edd0cd6cd73d9734c211908a209dcb88acffffffff296b1b3c9ec3a104e5f5369825ab367fa06f9465c43b422e298e4ab1edc7b631030000001976a914e43eb9614d7c586dfb794ffaefabe14f10bfda8a88acffffffff04a0860100000000001976a914534202809fd50000009da10400000000f000000088aca0860100000000001976a914758709ab6ee733ab1a48859bf3136a3e5a4e1bff88aca0860100000000001976a9142736c9ff6e1bdb942b4ebe3cc7c84c9a1f7d405d88acaf4c98b5000000001976a914f259d6c80462cd5aa45a242aabaae36a5d544d2488ac00000000'
		privateKeys = [b"[\xab\xa1\x8cik\xb7\xf7\x90\xc6s\x0bu3\xb5\xbfw\x95\xe6&>M(nO\xc5\xaa\\\xb6'Q\x04"]
		maximumSignedSize = 999
		expectedQuery = ('signrawtransaction', '0100000003296b1b3c9ec3a104e5f5369825ab367fa06f9465c43b422e298e4ab1edc7b631010000001976a9144454f61033d4968c825894206082a0e1fefac51488acffffffff296b1b3c9ec3a104e5f5369825ab367fa06f9465c43b422e298e4ab1edc7b631020000001976a914deb5c235b1edd0cd6cd73d9734c211908a209dcb88acffffffff296b1b3c9ec3a104e5f5369825ab367fa06f9465c43b422e298e4ab1edc7b631030000001976a914e43eb9614d7c586dfb794ffaefabe14f10bfda8a88acffffffff04a0860100000000001976a914534202809fd50000009da10400000000f000000088aca0860100000000001976a914758709ab6ee733ab1a48859bf3136a3e5a4e1bff88aca0860100000000001976a9142736c9ff6e1bdb942b4ebe3cc7c84c9a1f7d405d88acaf4c98b5000000001976a914f259d6c80462cd5aa45a242aabaae36a5d544d2488ac00000000')
		queryResult = {'complete': False, 'hex': '0100000003296b1b3c9ec3a104e5f5369825ab367fa06f9465c43b422e298e4ab1edc7b6310100000000ffffffff296b1b3c9ec3a104e5f5369825ab367fa06f9465c43b422e298e4ab1edc7b631020000006c493046022100e4a3ee175f2cbd8463ca8f944df54cf20f5ffe7c3e2cc1d360ba9132c8bd86b0022100d7c2ee3ff7781639b4d05172c09238a24e27c465b010863479572da452462dbb012102946edab65bbe42522fd6661f4b9f3b9c1de2459f7e4a54c2d086a55b03cc56bbffffffff296b1b3c9ec3a104e5f5369825ab367fa06f9465c43b422e298e4ab1edc7b631030000006c493046022100f374e3dfb188cf3e061d22fbe1823ebcb148c832747e6d572c6d9169fd866990022100cef35782388f8913edc606f227f4ae8f8386d7f2bd6752de2a0cb618770aead1012102cecf80f70d19cf58d42c5085fb834c9ce80637d01c1a531245b8c8141de49659ffffffff04a0860100000000001976a914534202809fd50000009da10400000000f000000088aca0860100000000001976a914758709ab6ee733ab1a48859bf3136a3e5a4e1bff88aca0860100000000001976a9142736c9ff6e1bdb942b4ebe3cc7c84c9a1f7d405d88acaf4c98b5000000001976a914f259d6c80462cd5aa45a242aabaae36a5d544d2488ac00000000'}
		rpcHost.queue.append((expectedQuery, queryResult))
		expectedQuery = ('signrawtransaction', '0100000003296b1b3c9ec3a104e5f5369825ab367fa06f9465c43b422e298e4ab1edc7b6310100000000ffffffff296b1b3c9ec3a104e5f5369825ab367fa06f9465c43b422e298e4ab1edc7b631020000006c493046022100e4a3ee175f2cbd8463ca8f944df54cf20f5ffe7c3e2cc1d360ba9132c8bd86b0022100d7c2ee3ff7781639b4d05172c09238a24e27c465b010863479572da452462dbb012102946edab65bbe42522fd6661f4b9f3b9c1de2459f7e4a54c2d086a55b03cc56bbffffffff296b1b3c9ec3a104e5f5369825ab367fa06f9465c43b422e298e4ab1edc7b631030000006c493046022100f374e3dfb188cf3e061d22fbe1823ebcb148c832747e6d572c6d9169fd866990022100cef35782388f8913edc606f227f4ae8f8386d7f2bd6752de2a0cb618770aead1012102cecf80f70d19cf58d42c5085fb834c9ce80637d01c1a531245b8c8141de49659ffffffff04a0860100000000001976a914534202809fd50000009da10400000000f000000088aca0860100000000001976a914758709ab6ee733ab1a48859bf3136a3e5a4e1bff88aca0860100000000001976a9142736c9ff6e1bdb942b4ebe3cc7c84c9a1f7d405d88acaf4c98b5000000001976a914f259d6c80462cd5aa45a242aabaae36a5d544d2488ac00000000', None, ['92HHm7buWvju96ri9xxNko4rFdQPZK5QfWYGxFC28XxA6pe1NZF'])
		queryResult = {'complete': True, 'hex': '0100000003296b1b3c9ec3a104e5f5369825ab367fa06f9465c43b422e298e4ab1edc7b631010000008a47304402206c47c69927e4db9a0bcf228518a60a136a6fa7e7b8cfa776fa88dc49b1d54f6102200524f67f9ab4f5b78ec8d1f6342665971377cb9bd39359a23a1bb80601a5b0da0141049b387e68b2c1888827cf3f63109079f7b942492e8e632d55f0e4f11adf4512bb5845531ba119b9701b1623fff2f2857877a758f85ab4bafce25bc68246f3be19ffffffff296b1b3c9ec3a104e5f5369825ab367fa06f9465c43b422e298e4ab1edc7b631020000006c493046022100e4a3ee175f2cbd8463ca8f944df54cf20f5ffe7c3e2cc1d360ba9132c8bd86b0022100d7c2ee3ff7781639b4d05172c09238a24e27c465b010863479572da452462dbb012102946edab65bbe42522fd6661f4b9f3b9c1de2459f7e4a54c2d086a55b03cc56bbffffffff296b1b3c9ec3a104e5f5369825ab367fa06f9465c43b422e298e4ab1edc7b631030000006c493046022100f374e3dfb188cf3e061d22fbe1823ebcb148c832747e6d572c6d9169fd866990022100cef35782388f8913edc606f227f4ae8f8386d7f2bd6752de2a0cb618770aead1012102cecf80f70d19cf58d42c5085fb834c9ce80637d01c1a531245b8c8141de49659ffffffff04a0860100000000001976a914534202809fd50000009da10400000000f000000088aca0860100000000001976a914758709ab6ee733ab1a48859bf3136a3e5a4e1bff88aca0860100000000001976a9142736c9ff6e1bdb942b4ebe3cc7c84c9a1f7d405d88acaf4c98b5000000001976a914f259d6c80462cd5aa45a242aabaae36a5d544d2488ac00000000'}
		rpcHost.queue.append((expectedQuery, queryResult))
		expectedQuery = ('sendrawtransaction', '0100000003296b1b3c9ec3a104e5f5369825ab367fa06f9465c43b422e298e4ab1edc7b631010000008a47304402206c47c69927e4db9a0bcf228518a60a136a6fa7e7b8cfa776fa88dc49b1d54f6102200524f67f9ab4f5b78ec8d1f6342665971377cb9bd39359a23a1bb80601a5b0da0141049b387e68b2c1888827cf3f63109079f7b942492e8e632d55f0e4f11adf4512bb5845531ba119b9701b1623fff2f2857877a758f85ab4bafce25bc68246f3be19ffffffff296b1b3c9ec3a104e5f5369825ab367fa06f9465c43b422e298e4ab1edc7b631020000006c493046022100e4a3ee175f2cbd8463ca8f944df54cf20f5ffe7c3e2cc1d360ba9132c8bd86b0022100d7c2ee3ff7781639b4d05172c09238a24e27c465b010863479572da452462dbb012102946edab65bbe42522fd6661f4b9f3b9c1de2459f7e4a54c2d086a55b03cc56bbffffffff296b1b3c9ec3a104e5f5369825ab367fa06f9465c43b422e298e4ab1edc7b631030000006c493046022100f374e3dfb188cf3e061d22fbe1823ebcb148c832747e6d572c6d9169fd866990022100cef35782388f8913edc606f227f4ae8f8386d7f2bd6752de2a0cb618770aead1012102cecf80f70d19cf58d42c5085fb834c9ce80637d01c1a531245b8c8141de49659ffffffff04a0860100000000001976a914534202809fd50000009da10400000000f000000088aca0860100000000001976a914758709ab6ee733ab1a48859bf3136a3e5a4e1bff88aca0860100000000001976a9142736c9ff6e1bdb942b4ebe3cc7c84c9a1f7d405d88acaf4c98b5000000001976a914f259d6c80462cd5aa45a242aabaae36a5d544d2488ac00000000')
		queryResult = 'a0e9f69a8a7e5246e767231573229c72b30c0eaad79cedbff628d62b9c6ad252'
		rpcHost.queue.append((expectedQuery, queryResult))
		txID = host.signAndSend(unsignedTransactionHex, privateKeys, maximumSignedSize)
		self.assertEqual(txID, 'a0e9f69a8a7e5246e767231573229c72b30c0eaad79cedbff628d62b9c6ad252')

	def test_block_chain(self):
		rpcHost = MockRPC.Host()
		host = InitHost(rpcHost);
		expectedQuery = ('getblockhash', 0)
		queryResult = 'f5ae71e26c74beacc88382716aced69cddf3dffff24f384e1808905e0188f68f'
		rpcHost.queue.append((expectedQuery, queryResult))
		block0 = host.getBlockHashAtIndexOrNone(0)
		self.assertEqual(block0, 'f5ae71e26c74beacc88382716aced69cddf3dffff24f384e1808905e0188f68f')
		expectedQuery = ('getblockhash', 400000)
		queryResult = RPC.RPCFailureWithMessage('Block number out of range.',)
		rpcHost.queue.append((expectedQuery, queryResult))
		result = host.getBlockHashAtIndexOrNone(400000)
		self.assertIsNone(result)
		expectedQuery = ('getblock', 'f5ae71e26c74beacc88382716aced69cddf3dffff24f384e1808905e0188f68f')
		queryResult = {'merkleroot': '97ddfbbae6be97fd6cdf3e7ca13232a3afff2353e29badfab7f73011edd4ced9', 'bits': '1e0ffff0', 'version': 1, 'time': 1317798646, 'tx': ['97ddfbbae6be97fd6cdf3e7ca13232a3afff2353e29badfab7f73011edd4ced9'], 'nextblockhash': '4daf3f5d54e7a2d448bd185b0f68fbc97d811ffa1a8bade3b4c1cdbe8a91c90c', 'height': 0, 'confirmations': 302529, 'size': 280, 'difficulty': 0.00024414, 'nonce': 385270584, 'hash': 'f5ae71e26c74beacc88382716aced69cddf3dffff24f384e1808905e0188f68f'}
		rpcHost.queue.append((expectedQuery, queryResult))
		block1 = host.getNextBlockHash(block0)
		self.assertEqual(block1, '4daf3f5d54e7a2d448bd185b0f68fbc97d811ffa1a8bade3b4c1cdbe8a91c90c')
		expectedQuery = ('getblock', 'f5ae71e26c74beacc88382716aced69cddf3dffff24f384e1808905e0188f68f', False)
		queryResult = '010000000000000000000000000000000000000000000000000000000000000000000000d9ced4ed1130f7b7faad9be25323ffafa33232a17c3edf6cfd97bee6bafbdd97f6028c4ef0ff0f1e38c3f6160101000000010000000000000000000000000000000000000000000000000000000000000000ffffffff4804ffff001d0104404e592054696d65732030352f4f63742f32303131205374657665204a6f62732c204170706c65e280997320566973696f6e6172792c2044696573206174203536ffffffff0100f2052a010000004341040184710fa689ad5023690c80f3a49c8f13f8d45b8c857fbcbc8bc4a8e4d3eb4b10f4d4604fa08dce601aaf0f470216fe1b51850b4acf21b179c45070ac7b03a9ac00000000'
		rpcHost.queue.append((expectedQuery, queryResult))
		transactions = host.getBlockTransactions(block0)
		self.assertEqual(transactions, []) # coinbase transaction not included
		expectedQuery = ('getblockhash', 6146)
		queryResult = 'a5915190c5b4336f23665747265ac3efe66293230287b67eaf10f6f48a8ffdd7'
		rpcHost.queue.append((expectedQuery, queryResult))
		block6146 = host.getBlockHashAtIndexOrNone(6146)
		self.assertEqual(block6146, 'a5915190c5b4336f23665747265ac3efe66293230287b67eaf10f6f48a8ffdd7')

		expectedQuery = ('getblock', 'a5915190c5b4336f23665747265ac3efe66293230287b67eaf10f6f48a8ffdd7')
		queryResult = {"hash" : "a5915190c5b4336f23665747265ac3efe66293230287b67eaf10f6f48a8ffdd7",
		"confirmations" : 300801,
		"size" : 868,
		"height" : 6146,
		"version" : 1,
		"merkleroot" : "436f511e4c7ee5a14550045d691d8f2bd6b74639aa291415e21d20b04eee609e",
		"tx" : [
		"823dd1507100e8826936a14030d2e919380c5df2a20b2fe096c79f26690b057c",
		"64975f2bff7cab6e7aef4b9ff7a395b41ed2ea99e9426f8845fc675c01b5fc43",
		"97a57c59b0415fa1b782b263b1c1cee833eacc5142a28ba1d405801a2eab90ba",
		"7e448af1a331c0e961926ad0e7dd21ab22b2c2246fafd6291868bb883ccfaf61"
		],
		"time" : 1365627251,
		"nonce" : 1896284160,
		"bits" : "1e0fffff",
		"difficulty" : 0.00024414,
		"previousblockhash" : "28db29acbc4211436623eee9a3b36688054b380a36f7a6c09a716495b82adf80",
		"nextblockhash" : "9f1f40306323c191fcd3cfc29af688043d225195596d482b67d695456981f64f"
		}
		rpcHost.queue.append((expectedQuery, queryResult))
		expectedQuery = ('getblock', 'a5915190c5b4336f23665747265ac3efe66293230287b67eaf10f6f48a8ffdd7', False)
		queryResult = '0100000080df2ab89564719ac0a6f7360a384b058866b3a3e9ee2366431142bcac29db289e60ee4eb0201de2151429aa3946b7d62b8f1d695d045045a1e57e4c1e516f4373d16551ffff0f1e000007710401000000010000000000000000000000000000000000000000000000000000000000000000ffffffff0e0473d16551013f062f503253482fffffffff01406a832b01000000232102d14fe5849018383aa54efb6b902cbd5f8c2468a575880efd3e2e71766093101cac000000000100000001390779200e9396ba9922f78f6eba34a83e023db6eab98b3f209ffc49fb93cdca010000006b48304502210081fa693e2fde1450283db5b4b9f39ef947c4dd79448cdbd39f2173677536ebde022045a923300a53b5b8fc56c77e5f3ec5cd6cd5707d97c3c50bff7cd71ff33f7d6801210398f83fd675019ac249ca1baec98bd96469d867de3b6930f441a4e53cd79ac876ffffffff02c0548f215d0000001976a9148dbb3488b4fbc5a395c13ea9142eff65a545ea0988ac00e87648170000001976a91454bbe1f4dd67050fd34310bc299a0e7ea1b7cdbb88ac00000000010000000143fcb5015c67fc45886f42e999ead21eb495a3f79f4bef7a6eab7cff2b5f9764000000006b483045022047c22f6ca4df485606a45c8b034aca09608088a10538eb7e63c3ac75f608bbb3022100c22bba6616a9e9d785728aab03ffa5d5539947a2bb12d8a04561f8c23050f82c012103dc33360f2f56f019d0004092067927fe529c20d3d7dfe89d892e1d509cc45122ffffffff0240daeacc5a0000001976a914400d1b16f52cc19a85ae7bfeec717a908831ba4588ac00e40b54020000001976a91443fccad9c7918b14db96b2907718ea99c4ec8eb488ac000000000100000001ba90ab2e1a8005d4a18ba24251ccea33e8cec1b163b282b7a15f41b0597ca597000000006b483045022100c17e678be7176d44ac7363c8287f49b498783d143acb4f80f18d79e4885dcc3b0220023a2f9e94b7db773d8557eac3ec04ade755e764d20462284415e7aea42e0e52012102369971d837172b2348a2c646e1c1338bda283ac12bea621062ad5cf8413e5695ffffffff02c05f4678580000001976a91476c606df95db559307e08f162d8b3828830a7d9088ac00e40b54020000001976a914ce925c4652ccf128dbb5eb37cabc0bcb51f8dad088ac00000000'
		rpcHost.queue.append((expectedQuery, queryResult))

		transactions = host.getBlockTransactions(block6146)
		expectedTransactions_Hex = [('64975f2bff7cab6e7aef4b9ff7a395b41ed2ea99e9426f8845fc675c01b5fc43', '0100000001390779200e9396ba9922f78f6eba34a83e023db6eab98b3f209ffc49fb93cdca010000006b48304502210081fa693e2fde1450283db5b4b9f39ef947c4dd79448cdbd39f2173677536ebde022045a923300a53b5b8fc56c77e5f3ec5cd6cd5707d97c3c50bff7cd71ff33f7d6801210398f83fd675019ac249ca1baec98bd96469d867de3b6930f441a4e53cd79ac876ffffffff02c0548f215d0000001976a9148dbb3488b4fbc5a395c13ea9142eff65a545ea0988ac00e87648170000001976a91454bbe1f4dd67050fd34310bc299a0e7ea1b7cdbb88ac00000000'), ('97a57c59b0415fa1b782b263b1c1cee833eacc5142a28ba1d405801a2eab90ba', '010000000143fcb5015c67fc45886f42e999ead21eb495a3f79f4bef7a6eab7cff2b5f9764000000006b483045022047c22f6ca4df485606a45c8b034aca09608088a10538eb7e63c3ac75f608bbb3022100c22bba6616a9e9d785728aab03ffa5d5539947a2bb12d8a04561f8c23050f82c012103dc33360f2f56f019d0004092067927fe529c20d3d7dfe89d892e1d509cc45122ffffffff0240daeacc5a0000001976a914400d1b16f52cc19a85ae7bfeec717a908831ba4588ac00e40b54020000001976a91443fccad9c7918b14db96b2907718ea99c4ec8eb488ac00000000'), ('7e448af1a331c0e961926ad0e7dd21ab22b2c2246fafd6291868bb883ccfaf61', '0100000001ba90ab2e1a8005d4a18ba24251ccea33e8cec1b163b282b7a15f41b0597ca597000000006b483045022100c17e678be7176d44ac7363c8287f49b498783d143acb4f80f18d79e4885dcc3b0220023a2f9e94b7db773d8557eac3ec04ade755e764d20462284415e7aea42e0e52012102369971d837172b2348a2c646e1c1338bda283ac12bea621062ad5cf8413e5695ffffffff02c05f4678580000001976a91476c606df95db559307e08f162d8b3828830a7d9088ac00e40b54020000001976a914ce925c4652ccf128dbb5eb37cabc0bcb51f8dad088ac00000000')]
		expectedTransactions = []
		for txID, transactionHex in expectedTransactions_Hex:
			data = binascii.unhexlify(transactionHex.encode('ascii'))
			expectedTransactions.append((txID, data))
		self.assertEqual(transactions, expectedTransactions)

	def test_mempool(self):
		rpcHost = MockRPC.Host()
		host = InitHost(rpcHost);
		expectedQuery = ('getrawmempool',)
		queryResult = []
		rpcHost.queue.append((expectedQuery, queryResult))
		transactions = host.getMemPoolTransactions()
		self.assertEqual(transactions, [])
		expectedQuery = ('getrawmempool',)
		queryResult = ['ef7fdd79a749a537961d26963e1cbacd4aa80245df1daf526dae78c16f74bd51']
		rpcHost.queue.append((expectedQuery, queryResult))
		expectedQuery = ('getrawtransaction', 'ef7fdd79a749a537961d26963e1cbacd4aa80245df1daf526dae78c16f74bd51')
		queryResult = '010000000252d26a9c2bd628f6bfed9cd7aa0e0cb3729c2273152367e746527e8a9af6e9a0020000006a47304402205d6af2834d6ac3f4fdd862a8f8c4d9f880c766805a82283407f93bf6f4e383bb02203a5cb33fe2558aebb1bc1de481834527f12629a53859264a9bb54f864051ce76012102099708a691f08269db1b8e34cd474048a12e585b7a0a4aa3c596126a239cf1b5ffffffff52d26a9c2bd628f6bfed9cd7aa0e0cb3729c2273152367e746527e8a9af6e9a0030000006b483045022100e959546384313dc2649233cff2fa61be8613db379b110a99d6bcc1c6674308340220353afa5ee139edb8f2f7189c1df8548be3f9e22c5268947c3d6cc4a7e703266801210329520b9852c2881168dc19746abd94d5b9124b72623680aaf2d0257cdce4738cffffffff0380969800000000001976a914534200000000000000000000000000000000000088aca0860100000000001976a9148819ff5befc6073300552395d5b4fc75da1df88788ac8f2ffeb4000000001976a914d9e9b550c9d462b19a68853168ebcf5a43b60d7388ac00000000'
		rpcHost.queue.append((expectedQuery, queryResult))
		transactions = host.getMemPoolTransactions()
		expectedTransactions_Hex = [('ef7fdd79a749a537961d26963e1cbacd4aa80245df1daf526dae78c16f74bd51', '010000000252d26a9c2bd628f6bfed9cd7aa0e0cb3729c2273152367e746527e8a9af6e9a0020000006a47304402205d6af2834d6ac3f4fdd862a8f8c4d9f880c766805a82283407f93bf6f4e383bb02203a5cb33fe2558aebb1bc1de481834527f12629a53859264a9bb54f864051ce76012102099708a691f08269db1b8e34cd474048a12e585b7a0a4aa3c596126a239cf1b5ffffffff52d26a9c2bd628f6bfed9cd7aa0e0cb3729c2273152367e746527e8a9af6e9a0030000006b483045022100e959546384313dc2649233cff2fa61be8613db379b110a99d6bcc1c6674308340220353afa5ee139edb8f2f7189c1df8548be3f9e22c5268947c3d6cc4a7e703266801210329520b9852c2881168dc19746abd94d5b9124b72623680aaf2d0257cdce4738cffffffff0380969800000000001976a914534200000000000000000000000000000000000088aca0860100000000001976a9148819ff5befc6073300552395d5b4fc75da1df88788ac8f2ffeb4000000001976a914d9e9b550c9d462b19a68853168ebcf5a43b60d7388ac00000000')]
		expectedTransactions = []
		for txID, transactionHex in expectedTransactions_Hex:
			data = binascii.unhexlify(transactionHex.encode('ascii'))
			expectedTransactions.append((txID, data))
		self.assertEqual(transactions, expectedTransactions)
