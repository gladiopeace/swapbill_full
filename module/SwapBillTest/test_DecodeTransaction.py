from __future__ import print_function
import unittest
from SwapBill import DecodeTransaction

class Test(unittest.TestCase):
	def test(self):
		txHex = '0100000002796bb0667fc809635e55d3083e9f08c9ad006ab06727bf9d0e8ead3590fee829010000006c493046022100f0b4528a8811a7f6922fd6605c54aa8290d3f41a357c2010ea7ff4f50cd266d9022100c5dba0fe903c513d0d80f3d43de5f0ec6e634baa94c709352bc5d550f1223c65012103478dff646fce10f2f9bb39ac3d57655a6c831d9c716a08f22087f54930cab63effffffff796bb0667fc809635e55d3083e9f08c9ad006ab06727bf9d0e8ead3590fee829000000006a47304402206f3174c81b1535173b45c2e8082e463f5e72a52aa8bcc97879f8d465cbe885d30220689ce3b1bb9ebc9c83e6e17b19a4241afdb67c310e141a909e9524182356b09e012102a559bedd392daf095937ae725446695b06cfe1d03776d09f172821beef1fd73bffffffff03eb2c2b02000000001976a91486ee1634949c9172183de8ce39ee078c4278cf0a88aca0860100000000001976a91433a6231c75e5a14cc3fb6989a49e1e2d4422053288ac80841e00000000001976a914535750000000000000000000000000000000000088ac00000000'
		tx = DecodeTransaction.Decode(txHex)
		self.assertEqual(tx.outputPubKeyHash(0), b'SWP\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		self.assertEqual(tx.numberOfInputs(), 2)
		self.assertEqual(tx.inputTXID(0), '29e8fe9035ad8e0e9dbf2767b06a00adc9089f3e08d3555e6309c87f66b06b79')
		self.assertEqual(tx.inputVOut(0), 1)
		self.assertEqual(tx.inputTXID(1), '29e8fe9035ad8e0e9dbf2767b06a00adc9089f3e08d3555e6309c87f66b06b79')
		self.assertEqual(tx.inputVOut(1), 0)
		self.assertEqual(tx.numberOfOutputs(), 3)
		self.assertEqual(tx.outputAmount(0), 2000000)
		self.assertEqual(tx.outputPubKeyHash(1), b'3\xa6#\x1cu\xe5\xa1L\xc3\xfbi\x89\xa4\x9e\x1e-D"\x052')
		self.assertEqual(tx.outputAmount(1), 100000)
		self.assertEqual(tx.outputPubKeyHash(2), b'\x86\xee\x164\x94\x9c\x91r\x18=\xe8\xce9\xee\x07\x8cBx\xcf\n')
		self.assertEqual(tx.outputAmount(2), 36383979)
		nonSwapBillTXHex = txHex.replace('5357500000', '5457500000')
		self.assertIsNone(DecodeTransaction.Decode(nonSwapBillTXHex))
		nonSwapBillTXHex = txHex.replace('5357500000', '5358500000')
		self.assertIsNone(DecodeTransaction.Decode(nonSwapBillTXHex))
		nonSwapBillTXHex = txHex.replace('5357500000', '5357510000')
		self.assertIsNone(DecodeTransaction.Decode(nonSwapBillTXHex))
		## TODO - check different transaction types
		#txHex = '0100000003f4dcbefc65134eedd0e4c51972d0153559373ca792d418224be7c28ba63ede20010000006b48304502206e0271aeb1b91673f9e0de8f0131d0c8d673ea738b94a0937a65e3cc1bd431460221008c00646703d19b6ce348e689df81b2429ffa8b57674cd26c7d3ac1003167f02401210210f8d9c2aa007e2024b85e419406a07e278febfc5828df523c45697129c81aaffffffffff4dcbefc65134eedd0e4c51972d0153559373ca792d418224be7c28ba63ede20030000006b483045022100faf3bc5cec4c3be0e8595c922617c20f05b9628a32c1a75548d305e25a6b2e18022035975ce25e2e987739d91feeccc9f0fd4e9a40fff24b1f92b730fd249009da71012103eb1932850c6ffdfbe806f534ead01a0b618a357782d8de6e947993c7a1334553ffffffff8c270b204ef48ee923b5ab0e2f3269447b1777af31d2bc84ef5a04e690970520010000006b48304502210087c1ee75391d2da87493ce0444c34a237d3418990e7ba45878e263148480e6d402203d89e68755925de0c852c03956fe540af9a3232b45a853796c08f3938c0d812b01210222bd9a33a910e7d7e08071424fa06c462605069de8ea99826eed02675e02f9d7ffffffff03a0860100000000001976a91453575003881300000000ffffffff99999959000088aca0860100000000001976a9147e877cb57a375c4525229942326f5e51fb6ad16288ac91790529000000001976a91431b05dabe3fc38cdb5a2de8e07123fd0b945047888ac00000000'
		#tx = DecodeTransaction.Decode(txHex)
		#self.assertEqual(tx.outputPubKeyHash(2), b'SWP\x03\x88\x13\x00\x00\x00\x00\xff\xff\xff\xff\x99\x99\x99Y\x00\x00')
		#self.assertEqual(tx.numberOfOutputs(), 3)
