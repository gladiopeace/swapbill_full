from __future__ import print_function
import unittest
from SwapBill import State
from SwapBill.State import OutputsSpecDoesntMatch, InvalidTransactionType, InvalidTransactionParameters
from SwapBill.Amounts import e

class Test(unittest.TestCase):
	outputsLookup = {
	    'Burn':('destination',),
	    'Pay':('change','destination'),
	    'LTCBuyOffer':('change','refund'),
	    'LTCSellOffer':('change','receiving'),
	    'LTCExchangeCompletion':(),
	    'Collect':('destination',),
	    'ForwardToFutureNetworkVersion':('change',)
	    }

	def __init__(self, *args, **kwargs):
		super(Test, self).__init__(*args, **kwargs)
		self._nextTX = 0

	def test_state_setup(self):
		state = State.State(100, 'mockhash', minimumBalance=1)
		assert state.startBlockMatches('mockhash')
		assert not state.startBlockMatches('mockhosh')

	def test_bad_transactions(self):
		state = State.State(100, 'mochhash', minimumBalance=1)
		self.assertRaises(InvalidTransactionType, state.checkTransaction, 'Burnee', ('destination',), {'amount':0})
		self.assertRaises(InvalidTransactionParameters, state.checkTransaction, 'Burn', ('destination',), {})
		self.assertRaises(InvalidTransactionParameters, state.checkTransaction, 'Burn', ('destination',), {'amount':0, 'spuriousAdditionalDetail':0})

	def TXID(self):
		self._nextTX += 1
		return 'tx' + str(self._nextTX)

	def Burn(self, amount):
		txID = self.TXID()
		self.state.applyTransaction(transactionType='Burn', txID=txID, outputs=('destination',), transactionDetails={'amount':amount})
		return (txID, 1)

	def Apply_AssertSucceeds(self, state, transactionType, **details):
		outputs = self.outputsLookup[transactionType]
		### note that applyTransaction now calls check and asserts success internally
		### but this then also asserts that there is no warning
		canApply, reason = state.checkTransaction(transactionType, outputs, details)
		self.assertEqual(reason, '')
		self.assertEqual(canApply, True)
		txID = self.TXID()
		state.applyTransaction(transactionType, txID=txID, outputs=outputs, transactionDetails=details)
		txOutputs = {}
		for i in range(len(outputs)):
			txOutputs[outputs[i]] = (txID, i + 1)
		return txOutputs

	def Apply_AssertFails(self, state, transactionType, **details):
		outputs = self.outputsLookup[transactionType]
		canApply, reason = state.checkTransaction(transactionType, outputs, details)
		self.assertEqual(canApply, False)
		self.assertRaises(AssertionError, state.applyTransaction, transactionType, txID='AssertFails_TXID', outputs=outputs, transactionDetails=details)
		return reason

	def test_burn(self):
		state = State.State(100, 'mockhash', minimumBalance=10)
		self.assertRaises(OutputsSpecDoesntMatch, state.checkTransaction, 'Burn', (), {'amount':0})
		self.assertRaises(OutputsSpecDoesntMatch, state.checkTransaction, 'Burn', ('madeUpOutput',), {'amount':0})
		self.assertRaises(OutputsSpecDoesntMatch, state.checkTransaction, 'Burn', ('destination','destination'), {'amount':0})
		succeeds, reason = state.checkTransaction('Burn', ('destination',), {'amount':0})
		self.assertEqual(succeeds, False)
		self.assertEqual(reason, 'burn amount is below minimum balance')
		succeeds, reason = state.checkTransaction('Burn', ('destination',), {'amount':9})
		self.assertEqual(succeeds, False)
		self.assertEqual(reason, 'burn amount is below minimum balance')
		succeeds, reason = state.checkTransaction('Burn', ('destination',), {'amount':10})
		self.assertEqual(succeeds, True)
		self.assertEqual(reason, '')
		state.applyTransaction(transactionType='Burn', txID=self.TXID(), outputs=('destination',), transactionDetails={'amount':10})
		self.assertEqual(state._balances, {('tx1',1):10})
		# state should assert if you try to apply a bad transaction, and exit without any effect
		self.assertRaises(AssertionError, state.applyTransaction, 'Burn', 'badTX', ('destination',), {'amount':0})
		self.assertEqual(state._balances, {('tx1',1):10})
		state.applyTransaction(transactionType='Burn', txID=self.TXID(), outputs=('destination',), transactionDetails={'amount':20})
		self.assertEqual(state._balances, {('tx1',1):10, ('tx2',1):20})
		self.assertEqual(state.totalAccountedFor(), state._totalCreated)

	def test_forwarding(self):
		state = State.State(100, 'mochhash', minimumBalance=10)
		self.state = state
		burn = self.Burn(100000000)
		self.assertEqual(state._balances, {burn:100000000})
		details = {'sourceAccount':burn, 'amount':10, 'maxBlock':200}
		self.assertRaises(OutputsSpecDoesntMatch, state.checkTransaction, 'ForwardToFutureNetworkVersion', (), details)
		self.assertRaises(OutputsSpecDoesntMatch, state.checkTransaction, 'ForwardToFutureNetworkVersion', ('madeUpOutput'), details)
		self.assertRaises(OutputsSpecDoesntMatch, state.checkTransaction, 'ForwardToFutureNetworkVersion', ('change', 'madeUpOutput'), details)
		outputs = self.Apply_AssertSucceeds(state, 'ForwardToFutureNetworkVersion', **details)
		change = outputs['change']
		self.assertEqual(state._balances, {change:99999990})
		self.assertEqual(state.totalAccountedFor(), state._totalCreated)
		self.assertEqual(state._totalForwarded, 10)
		details = {'sourceAccount':change, 'amount':10, 'maxBlock':200}
		details['amount'] = 100000000
		reason = self.Apply_AssertFails(state, 'ForwardToFutureNetworkVersion', **details)
		self.assertEqual(reason, 'insufficient balance in source account (transaction ignored)')
		details['amount'] = 0
		reason = self.Apply_AssertFails(state, 'ForwardToFutureNetworkVersion', **details)
		self.assertEqual(reason, 'amount is below minimum balance')
		details['amount'] = 9
		reason = self.Apply_AssertFails(state, 'ForwardToFutureNetworkVersion', **details)
		self.assertEqual(reason, 'amount is below minimum balance')
		details['amount'] = 10
		details['maxBlock'] = 99
		reason = self.Apply_AssertFails(state, 'ForwardToFutureNetworkVersion', **details)
		self.assertEqual(reason, 'max block for transaction has been exceeded')
		reason = self.Apply_AssertFails(state, 'ForwardToFutureNetworkVersion', **details)
		details['maxBlock'] = 100
		details['sourceAccount'] = 'madeUpSourceAccount'
		reason = self.Apply_AssertFails(state, 'ForwardToFutureNetworkVersion', **details)
		self.assertEqual(reason, 'source account does not exist' )
		self.assertEqual(state._balances, {change:99999990})
		self.assertEqual(state.totalAccountedFor(), state._totalCreated)
		self.assertEqual(state._totalForwarded, 10)
		burn2 = self.Burn(20)
		self.assertEqual(state._balances, {change:99999990, burn2:20})
		details = {'sourceAccount':burn2, 'amount':11, 'maxBlock':200}
		reason = self.Apply_AssertFails(state, 'ForwardToFutureNetworkVersion', **details)
		self.assertEqual(reason, 'transaction includes change output, with change amount below minimum balance')
		self.assertEqual(state.totalAccountedFor(), state._totalCreated)

	def test_burn_and_pay(self):
		state = State.State(100, 'mochhash', minimumBalance=10)
		self.state = state
		output1 = self.Burn(10)
		self.assertEqual(state._balances, {output1:10})
		output2 = self.Burn(20)
		self.assertEqual(state._balances, {output1:10, output2:20})
		output3 = self.Burn(30)
		self.assertEqual(state._balances, {output1:10, output2:20, output3:30})
		self.assertEqual(state._balances, {('tx1',1):10, ('tx2',1):20, ('tx3',1):30})

		self.assertRaises(OutputsSpecDoesntMatch, state.checkTransaction, 'Pay', (), {'sourceAccount':('tx3',1), 'amount':0, 'maxBlock':200})
		self.assertRaises(OutputsSpecDoesntMatch, state.checkTransaction, 'Pay', ('madeUpOutput',), {'sourceAccount':('tx3',1), 'amount':0, 'maxBlock':200})
		self.assertRaises(OutputsSpecDoesntMatch, state.checkTransaction, 'Pay', ('destination','change'), {'sourceAccount':('tx3',1), 'amount':0, 'maxBlock':200})

		# destination amount below minimum balance
		reason = self.Apply_AssertFails(state, 'Pay', sourceAccount=('tx3',1), amount=0, maxBlock=200)
		self.assertEqual(reason, 'amount is below minimum balance')
		reason = self.Apply_AssertFails(state, 'Pay', sourceAccount=('tx3',1), amount=9, maxBlock=200)
		self.assertEqual(reason, 'amount is below minimum balance')
		# change amount below minimum balance
		reason = self.Apply_AssertFails(state, 'Pay', sourceAccount=('tx2',1), amount=11, maxBlock=200)
		self.assertEqual(reason, 'transaction includes change output, with change amount below minimum balance')

		self.assertEqual(state._balances, {('tx1',1):10, ('tx2',1):20, ('tx3',1):30})

		self.Apply_AssertSucceeds(state, 'Pay', sourceAccount=('tx3',1), amount=20, maxBlock=200)
		self.assertEqual(state._balances, {('tx1',1):10, ('tx2',1):20, ('tx4',1):10, ('tx4',2):20})

		# can't repeat the same transaction (output has been consumed)
		reason = self.Apply_AssertFails(state, 'Pay', sourceAccount=('tx3',1), amount=20, maxBlock=200)
		self.assertEqual(reason, 'source account does not exist')
		self.assertEqual(state._balances, {('tx1',1):10, ('tx2',1):20, ('tx4',1):10, ('tx4',2):20})

		# can't pay from a nonexistant account
		reason = self.Apply_AssertFails(state, 'Pay', sourceAccount=('tx12',2), amount=20, maxBlock=200)
		self.assertEqual(reason, 'source account does not exist')
		self.assertEqual(state._balances, {('tx1',1):10, ('tx2',1):20, ('tx4',1):10, ('tx4',2):20})

		# pay transaction fails and has no affect on state if there is not enough balance for payment
		reason = self.Apply_AssertFails(state, 'Pay', sourceAccount=('tx1',1), amount=11, maxBlock=200)
		self.assertEqual(reason, 'insufficient balance in source account (transaction ignored)')
		self.assertEqual(state._balances, {('tx1',1):10, ('tx2',1):20, ('tx4',1):10, ('tx4',2):20})

		# (but reduce by one and this should go through)
		self.Apply_AssertSucceeds(state, 'Pay', sourceAccount=('tx1',1), amount=10, maxBlock=200)
		self.assertEqual(state._balances, {('tx2',1):20, ('tx4',1):10, ('tx4',2):20, ('tx5',2):10})

		# transaction with maxBlock before current block
		canApply, reason = state.checkTransaction('Pay', ('change','destination'), {'sourceAccount':('tx2',1), 'amount':10, 'maxBlock':99})
		self.assertEqual(canApply, True)
		self.assertEqual(reason, 'max block for transaction has been exceeded')
		self.assertEqual(state._balances, {('tx2',1):20, ('tx4',1):10, ('tx4',2):20, ('tx5',2):10})
		payTX = self.TXID()
		state.applyTransaction('Pay', payTX, ('change','destination'), {'sourceAccount':('tx2',1), 'amount':10, 'maxBlock':99})
		self.assertEqual(state._balances, {(payTX,1):20, ('tx4',1):10, ('tx4',2):20, ('tx5',2):10})

		# but maxBlock exactly equal to current block is ok
		self.Apply_AssertSucceeds(state, 'Pay', sourceAccount=('tx5',2), amount=10, maxBlock=100)
		self.assertEqual(state._balances, {(payTX,1):20, ('tx4',1):10, ('tx4',2):20, ('tx7',2):10})
		self.assertEqual(state.totalAccountedFor(), state._totalCreated)

	def test_burn_and_collect(self):
		state = State.State(100, 'mochhash', minimumBalance=1)
		self.state = state
		output1 = self.Burn(10)
		self.assertEqual(state._balances, {output1:10})
		output2 = self.Burn(20)
		self.assertEqual(state._balances, {output1:10, output2:20})
		output3 = self.Burn(30)
		self.assertEqual(state._balances, {output1:10, output2:20, output3:30})
		self.assertEqual(state._balances, {('tx1',1):10, ('tx2',1):20, ('tx3',1):30})
		sourceAccounts = [('tx1',1),('tx2',1),('tx3',1)]
		# bad output specs
		self.assertRaises(OutputsSpecDoesntMatch, state.checkTransaction, 'Collect', (), {'sourceAccounts':sourceAccounts})
		self.assertRaises(OutputsSpecDoesntMatch, state.checkTransaction, 'Collect', ('madeUpOutput'), {'sourceAccounts':sourceAccounts})
		self.assertRaises(OutputsSpecDoesntMatch, state.checkTransaction, 'Collect', ('destination', 'madeUpOutput'), {'sourceAccounts':sourceAccounts})
		# no max block limit parameter
		self.assertRaises(InvalidTransactionParameters, state.checkTransaction, 'Collect', ('destination'), {'sourceAccounts':sourceAccounts, 'maxBlock':200})
		self.assertRaises(InvalidTransactionParameters, state.applyTransaction, 'Collect', 'madeUpTXID', ('destination'), {'sourceAccounts':sourceAccounts, 'maxBlock':200})
		# bad source account
		reason = self.Apply_AssertFails(state, 'Collect', sourceAccounts=[('tx1',1),('tx2',1),('madeUpTX',1)])
		self.assertEqual(reason, 'at least one source account does not exist')
		self.assertEqual(state._balances, {('tx1',1):10, ('tx2',1):20, ('tx3',1):30})
		# successful transaction
		self.Apply_AssertSucceeds(state, 'Collect', sourceAccounts=sourceAccounts)
		self.assertEqual(state._balances, {('tx4',1):60})
		self.assertEqual(state.totalAccountedFor(), state._totalCreated)

	def test_minimum_exchange_amount(self):
		state = State.State(100, 'mockhash', minimumBalance=1)
		self.state = state
		burnOutput = self.Burn(10000)
		self.assertEqual(state._balances, {burnOutput:10000})
		# cannot post buy or sell offers, because of minimum exchange amount constraint
		reason = self.Apply_AssertFails(state, 'LTCBuyOffer', sourceAccount=burnOutput, swapBillOffered=100, exchangeRate=0x80000000, maxBlockOffset=0, receivingAddress='a_receive', maxBlock=200)
		self.assertEqual(reason, 'does not satisfy minimum exchange amount (offer not posted)')
		self.assertEqual(state._balances, {burnOutput:10000})
		reason = self.Apply_AssertFails(state, 'LTCSellOffer', sourceAccount=burnOutput, swapBillDesired=100, exchangeRate=0x80000000, maxBlockOffset=0, maxBlock=200)
		self.assertEqual(reason, 'does not satisfy minimum exchange amount (offer not posted)')
		self.assertEqual(state._balances, {burnOutput:10000})
		self.assertEqual(state.totalAccountedFor(), state._totalCreated)

	def test_trade_offers_leave_less_than_minimum_balance(self):
		state = State.State(100, 'mockhash', minimumBalance=100000)
		self.state = state
		burnOutput = self.Burn(100000)
		self.assertEqual(state._balances, {burnOutput:100000})
		reason = self.Apply_AssertFails(state, 'LTCBuyOffer', sourceAccount=burnOutput, swapBillOffered=1000000, exchangeRate=0x80000000, maxBlockOffset=0, receivingAddress='a_receive', maxBlock=200)
		self.assertEqual(reason, 'insufficient balance in source account (offer not posted)')
		self.assertEqual(state._balances, {burnOutput:100000})
		reason = self.Apply_AssertFails(state, 'LTCSellOffer', sourceAccount=burnOutput, swapBillDesired=1000000, exchangeRate=0x80000000, maxBlockOffset=0, maxBlock=200)
		self.assertEqual(reason, 'insufficient balance in source account (offer not posted)')
		self.assertEqual(state._balances, {burnOutput:100000})
		self.assertEqual(state.totalAccountedFor(), state._totalCreated)

	def test_ltc_trading1(self):
		# this test adds tests against the ltc transaction types, and also runs through a simple exchange scenario
		# let's give out some real money, and then try again
		state = State.State(100, 'mochhash', minimumBalance=1)
		self.state = state
		burnA = self.Burn(100000000)
		burnB = self.Burn(200000000)
		burnC = self.Burn(200000000)
		self.assertEqual(state._balances, {burnA:100000000, burnB:200000000, burnC:200000000})

		# A wants to buy

		details = {
		    'sourceAccount':burnA,
		    'swapBillOffered':30000000, 'exchangeRate':0x80000000,
		    'maxBlock':100, 'maxBlockOffset':0,
		    'receivingAddress':'a_receive'
		}

		self.assertRaises(OutputsSpecDoesntMatch, state.checkTransaction, 'LTCBuyOffer', (), details)
		self.assertRaises(OutputsSpecDoesntMatch, state.checkTransaction, 'LTCBuyOffer', ('madeUpOutput'), details)
		self.assertRaises(OutputsSpecDoesntMatch, state.checkTransaction, 'LTCBuyOffer', ('refund', 'change'), details)
		self.assertRaises(OutputsSpecDoesntMatch, state.checkTransaction, 'LTCBuyOffer', ('change', 'refund', 'extraOutput'), details)

		# nonexistant source account
		details['sourceAccount'] = 'madeUpAccount'
		reason = self.Apply_AssertFails(state, 'LTCBuyOffer', **details)
		details['sourceAccount'] = burnA
		self.assertEqual(reason, 'source account does not exist')

		# bad max block
		details['maxBlock'] = 99
		canApply, reason = state.checkTransaction('LTCBuyOffer', ('change','refund'), details)
		self.assertEqual(canApply, True)
		self.assertEqual(reason, 'max block for transaction has been exceeded')
		self.assertEqual(state._balances, {burnA:100000000, burnB:200000000, burnC:200000000})
		self.assertEqual(state._LTCBuys.size(), 0)
		expiredBuyOfferChange = (self.TXID(), 1)
		state.applyTransaction('LTCBuyOffer', expiredBuyOfferChange[0], ('change','refund'), details)
		self.assertEqual(state._balances, {expiredBuyOfferChange:100000000, burnB:200000000, burnC:200000000})
		self.assertEqual(state._LTCBuys.size(), 0)
		details['maxBlock'] = 100
		details['sourceAccount'] = expiredBuyOfferChange

		# try offering more than available
		details['swapBillOffered'] = 3000000000
		reason = self.Apply_AssertFails(state, 'LTCBuyOffer', **details)
		self.assertEqual(reason, 'insufficient balance in source account (offer not posted)')

		# zero amount not permitted
		details['swapBillOffered'] = 0
		reason = self.Apply_AssertFails(state, 'LTCBuyOffer', **details)
		self.assertEqual(reason, 'zero amount not permitted')

		self.assertEqual(state._balances, {expiredBuyOfferChange:100000000, burnB:200000000, burnC:200000000})
		self.assertEqual(state._LTCBuys.size(), 0)

		# reasonable buy offer that should go through
		details['swapBillOffered'] = 30000000
		details['maxBlock'] = 0xfffffff0 # these two details changed to add test coverage for expiry overflow
		details['maxBlockOffset'] = 400
		outputs = self.Apply_AssertSucceeds(state, 'LTCBuyOffer', **details)
		changeA = outputs['change']
		refundA = outputs['refund']
		self.assertEqual(state._balances, {changeA:70000000-1, burnB:200000000, burnC:200000000, refundA:1})
		self.assertEqual(state._LTCBuys.size(), 1)

		# refund account can't be spent yet as it is locked during the trade
		reason = self.Apply_AssertFails(state, 'Pay', sourceAccount=refundA, amount=1, maxBlock=200)
		self.assertEqual(reason, "source account is linked to an outstanding trade offer or pending exchange and can't be spent until the trade is completed or expires")
		self.assertEqual(state._balances, {changeA:70000000-1, burnB:200000000, burnC:200000000, refundA:1})

		# B wants to sell

		details = {
		    'sourceAccount':burnB,
		    'swapBillDesired':40000000, 'exchangeRate':0x80000000,
		    'maxBlock':200, 'maxBlockOffset':0
		}

		self.assertRaises(OutputsSpecDoesntMatch, state.checkTransaction, 'LTCSellOffer', (), details)
		self.assertRaises(OutputsSpecDoesntMatch, state.checkTransaction, 'LTCSellOffer', ('madeUpOutput'), details)
		self.assertRaises(OutputsSpecDoesntMatch, state.checkTransaction, 'LTCSellOffer', ('receiving', 'change'), details)
		self.assertRaises(OutputsSpecDoesntMatch, state.checkTransaction, 'LTCSellOffer', ('change', 'receiving', 'extraOutput'), details)

		# nonexistant source account
		details['sourceAccount'] = 'madeUpAccount'
		reason = self.Apply_AssertFails(state, 'LTCSellOffer', **details)
		details['sourceAccount'] = burnB
		self.assertEqual(reason, 'source account does not exist')

		# bad max block
		details['maxBlock'] = 99
		canApply, reason = state.checkTransaction('LTCSellOffer', ('change','receiving'), details)
		self.assertEqual(canApply, True)
		self.assertEqual(reason, 'max block for transaction has been exceeded')
		self.assertEqual(state._balances, {changeA:70000000-1, burnB:200000000, burnC:200000000, refundA:1})
		self.assertEqual(state._LTCSells.size(), 0)
		expiredSellOfferChange = (self.TXID(), 1)
		state.applyTransaction('LTCSellOffer', expiredSellOfferChange[0], ('change','receiving'), details)
		self.assertEqual(state._balances, {changeA:70000000-1, expiredSellOfferChange:200000000, burnC:200000000, refundA:1})
		self.assertEqual(state._LTCSells.size(), 0)
		details['maxBlock'] = 100
		details['sourceAccount'] = expiredSellOfferChange

		#details['maxBlock'] = 99
		#reason = self.Apply_AssertFails(state, 'LTCSellOffer', **details)
		#details['maxBlock'] = 100
		#self.assertEqual(reason, 'max block for transaction has been exceeded' )

		# try offering more than available
		details['swapBillDesired'] = 40000000000
		reason = self.Apply_AssertFails(state, 'LTCSellOffer', **details)
		self.assertEqual(reason, 'insufficient balance in source account (offer not posted)')
		self.assertEqual(state._balances, {changeA:70000000-1, expiredSellOfferChange:200000000, burnC:200000000, refundA:1})

		# zero amount
		details['swapBillDesired'] = 0
		reason = self.Apply_AssertFails(state, 'LTCSellOffer', **details)
		self.assertEqual(reason, 'zero amount not permitted')
		self.assertEqual(state._balances, {changeA:70000000-1, expiredSellOfferChange:200000000, burnC:200000000, refundA:1})

		self.assertEqual(state._LTCBuys.size(), 1)
		self.assertEqual(state._LTCSells.size(), 0)

		# reasonable sell offer that should go through (and match)
		details['swapBillDesired'] = 40000000
		details['maxBlock'] = 0xfffffff0 # these two details changed to add test coverage for expiry overflow
		details['maxBlockOffset'] = 400
		outputs = self.Apply_AssertSucceeds(state, 'LTCSellOffer', **details)
		changeB = outputs['change']
		receivingB = outputs['receiving']
		self.assertEqual(state._balances, {changeA:70000000-1, changeB:197500000-1, burnC:200000000, refundA:1, receivingB:1})
		self.assertEqual(state._LTCBuys.size(), 0)
		self.assertEqual(state._LTCSells.size(), 1)
		self.assertEqual(len(state._pendingExchanges), 1)
		self.assertTrue(0 in state._pendingExchanges)

		# B must now complete with appropriate ltc payment

		details = {'pendingExchangeIndex':1, 'destinationAddress':'a_receive', 'destinationAmount':20000000}

		self.assertRaises(OutputsSpecDoesntMatch, state.checkTransaction, 'LTCExchangeCompletion', ('madeUpOutput'), details)

		# bad pending exchange index
		reason = self.Apply_AssertFails(state, 'LTCExchangeCompletion', **details)
		self.assertEqual(reason, 'no pending exchange with the specified index (transaction ignored)')
		# no state change
		self.assertEqual(state._balances, {changeA:70000000-1, changeB:197500000-1, burnC:200000000, refundA:1, receivingB:1})
		self.assertEqual(state._LTCBuys.size(), 0)
		self.assertEqual(state._LTCSells.size(), 1)
		self.assertEqual(len(state._pendingExchanges), 1)
		self.assertTrue(0 in state._pendingExchanges)

		# bad receive address
		reason = self.Apply_AssertFails(state, 'LTCExchangeCompletion', pendingExchangeIndex=0, destinationAddress='randomAddress', destinationAmount=20000000)
		self.assertEqual(reason, 'destination account does not match destination for pending exchange with the specified index (transaction ignored)')
		# no state change
		self.assertEqual(state._balances, {changeA:70000000-1, changeB:197500000-1, burnC:200000000, refundA:1, receivingB:1})
		self.assertEqual(state._LTCBuys.size(), 0)
		self.assertEqual(state._LTCSells.size(), 1)
		self.assertEqual(len(state._pendingExchanges), 1)
		self.assertTrue(0 in state._pendingExchanges)

		# insufficient payment
		reason = self.Apply_AssertFails(state, 'LTCExchangeCompletion', pendingExchangeIndex=0, destinationAddress='a_receive', destinationAmount=14999999)
		self.assertEqual(reason, 'amount is less than required payment amount (transaction ignored)')
		# no state change (b just loses these ltc)
		self.assertEqual(state._balances, {changeA:70000000-1, changeB:197500000-1, burnC:200000000, refundA:1, receivingB:1})
		self.assertEqual(state._LTCBuys.size(), 0)
		self.assertEqual(state._LTCSells.size(), 1)
		self.assertEqual(len(state._pendingExchanges), 1)
		self.assertTrue(0 in state._pendingExchanges)

		# pays amount offered for sale, not the amount
		# state should warn us about the ltc overpay, but allow the transaction to go through
		details= {'pendingExchangeIndex':0, 'destinationAddress':'a_receive', 'destinationAmount':20000000}
		canApply, warning = state.checkTransaction('LTCExchangeCompletion', outputs=(), transactionDetails=details)
		self.assertEqual(canApply, True)
		self.assertEqual(warning, 'amount is greater than required payment amount (exchange completes, but with ltc overpay)')

		# pays actual amount required for match with A's buy offer
		# (well formed completion transaction which should go through)
		self.Apply_AssertSucceeds(state, 'LTCExchangeCompletion', pendingExchangeIndex=0, destinationAddress='a_receive', destinationAmount=15000000)
		# B gets
		# payment of the 30000000 offered by A
		# plus fraction of deposit for the amount matched (=1875000)
		# (the rest of the deposit is left with an outstanding remainder sell offer)
		# refund account for a, with zero amount, is cleaned up
		self.assertEqual(state._balances, {changeA:70000000-1, changeB:197500000-1, burnC:200000000, refundA:1, receivingB:31875000+1})
		self.assertEqual(state._LTCBuys.size(), 0)
		self.assertEqual(state._LTCSells.size(), 1)
		self.assertEqual(len(state._pendingExchanges), 0)
		self.assertEqual(state.totalAccountedFor(), state._totalCreated)

	def SellOffer(self, state, source, swapBillDesired, exchangeRate, maxBlock=200, maxBlockOffset=0):
		details = {'sourceAccount':source, 'swapBillDesired':swapBillDesired, 'exchangeRate':exchangeRate, 'maxBlockOffset':maxBlockOffset, 'maxBlock':maxBlock}
		outputs = self.Apply_AssertSucceeds(state, 'LTCSellOffer', **details)
		self.assertEqual(state.totalAccountedFor(), state._totalCreated)
		return outputs['change'], outputs['receiving']
	def BuyOffer(self, state, source, receiveAddress, swapBillOffered, exchangeRate, maxBlock=200, maxBlockOffset=0):
		details = {'sourceAccount':source, 'receivingAddress':receiveAddress, 'swapBillOffered':swapBillOffered, 'exchangeRate':exchangeRate, 'maxBlockOffset':maxBlockOffset, 'maxBlock':maxBlock}
		outputs = self.Apply_AssertSucceeds(state, 'LTCBuyOffer', **details)
		self.assertEqual(state.totalAccountedFor(), state._totalCreated)
		return outputs['change'], outputs['refund']
	def Completion(self, state, pendingExchangeIndex, destinationAddress, destinationAmount):
		details = {'pendingExchangeIndex':pendingExchangeIndex, 'destinationAddress':destinationAddress, 'destinationAmount':destinationAmount}
		self.Apply_AssertSucceeds(state, 'LTCExchangeCompletion', **details)
		self.assertEqual(state.totalAccountedFor(), state._totalCreated)

	def test_ltc_buy_change_added_to_refund(self):
		state = State.State(100, 'starthash', minimumBalance=1*e(8))
		self.state = state
		burn = self.Burn(22*e(7))
		change, refund = self.BuyOffer(state, burn, 'madeUpReceiveAddress', swapBillOffered=3*e(7), exchangeRate=0x80000000)
		self.assertEqual(state._balances, {refund:19*e(7)})
		self.assertEqual(state.totalAccountedFor(), state._totalCreated)
	def test_ltc_sell_change_added_to_receiving(self):
		state = State.State(100, 'starthash', minimumBalance=1*e(8))
		self.state = state
		burn = self.Burn(22*e(7))
		change, receive = self.SellOffer(state, burn, swapBillDesired=3*16*e(7), exchangeRate=0x80000000)
		# deposit is 3*16*e(7) // 16
		self.assertEqual(state._balances, {receive:19*e(7)})
		self.assertEqual(state.totalAccountedFor(), state._totalCreated)

	def test_small_sell_remainder_refunded(self):
		state = State.State(100, 'starthash', minimumBalance=1)
		self.state = state
		burnB = self.Burn(10000000)
		changeB, receiveB = self.SellOffer(state, burnB, swapBillDesired=10000000, exchangeRate=0x80000000)
		# deposit is 10000000 // 16 = 625000
		self.assertEqual(state._balances, {changeB:9375000-1, receiveB:1})
		burnA = self.Burn(9900001)
		changeA, refundA = self.BuyOffer(state, burnA, 'receiveLTC', swapBillOffered=9900000, exchangeRate=0x80000000)
		# b should be refunded 100000 // 10000000 of his depost = 6250
		self.assertEqual(state._balances, {changeB:9375000-1, receiveB:6250+1, refundA:1})
		self.assertEqual(len(state._pendingExchanges), 1)
		# but receiving account can't be spent yet as this is locked until exchange completed
		reason = self.Apply_AssertFails(state, 'Pay', sourceAccount=receiveB, amount=1, maxBlock=200)
		self.assertEqual(reason, "source account is linked to an outstanding trade offer or pending exchange and can't be spent until the trade is completed or expires")
		self.assertEqual(state.getSpendableAmount(receiveB), 0)
		self.assertEqual(state._balances, {changeB:9375000-1, receiveB:6250+1, refundA:1})
		self.Completion(state, 0, 'receiveLTC', 9900000 // 2)
		self.assertEqual(len(state._pendingExchanges), 0)
		# b gets the rest of his depost refunded
		self.assertEqual(state._balances, {changeB:9375000-1, receiveB:10525000+1, refundA:1})
		# and the receiving account *can* now be used
		self.assertEqual(state.getSpendableAmount(receiveB), 10525000+1)
		outputs = self.Apply_AssertSucceeds(state, 'Pay', sourceAccount=receiveB, amount=1, maxBlock=200)
		payDestination = outputs['destination']
		payChange = outputs['change']
		self.assertEqual(state._balances, {changeB:9375000-1, payChange:10525000, refundA:1, payDestination:1})
		self.assertEqual(state.totalAccountedFor(), state._totalCreated)

	def test_small_buy_remainder_refunded(self):
		state = State.State(100, 'starthash', minimumBalance=1)
		self.state = state
		burnB = self.Burn(10000000)
		changeB, receiveB = self.SellOffer(state, burnB, swapBillDesired=10000000, exchangeRate=0x80000000)
		# deposit is 10000000 // 16 = 625000
		self.assertEqual(state._balances, {changeB:9375000-1, receiveB:1})
		burnA = self.Burn(10100001 + 3) # 3 added here to test collect when locked
		changeA, refundA = self.BuyOffer(state, burnA, 'receiveLTC', swapBillOffered=10100000, exchangeRate=0x80000000)
		# a should be refunded 100000 remainder from buy offer
		self.assertEqual(state._balances, {changeB:9375000-1, receiveB:1, changeA:3, refundA:100000+1})
		self.assertEqual(len(state._pendingExchanges), 1)
		# but refund account can't be spent yet as this is locked until exchange completed
		# (bunch of tests for stuff not being able to use this follow)
		reason = self.Apply_AssertFails(state, 'Pay', sourceAccount=refundA, amount=1, maxBlock=200)
		self.assertEqual(reason, "source account is linked to an outstanding trade offer or pending exchange and can't be spent until the trade is completed or expires")
		self.assertEqual(state.getSpendableAmount(refundA), 0)
		reason = self.Apply_AssertFails(state, 'Collect', sourceAccounts=[changeA, refundA])
		self.assertEqual(reason, "at least one source account is linked to an outstanding trade offer or pending exchange and can't be spent until the trade is completed or expires")
		details = {
		    'sourceAccount':refundA,
		    'swapBillOffered':100000, 'exchangeRate':0x80000000,
		    'maxBlock':100, 'maxBlockOffset':0,
		    'receivingAddress':'madeUpAddressButNotUsed'
		}
		reason = self.Apply_AssertFails(state, 'LTCBuyOffer', **details)
		self.assertEqual(reason, "source account is linked to an outstanding trade offer or pending exchange and can't be spent until the trade is completed or expires")
		details = {
		    'sourceAccount':refundA,
		    'swapBillDesired':100000, 'exchangeRate':0x80000000,
		    'maxBlock':100, 'maxBlockOffset':0
		}
		reason = self.Apply_AssertFails(state, 'LTCSellOffer', **details)
		self.assertEqual(reason, "source account is linked to an outstanding trade offer or pending exchange and can't be spent until the trade is completed or expires")
		details = {'sourceAccount':refundA, 'amount':10, 'maxBlock':200}
		reason = self.Apply_AssertFails(state, 'ForwardToFutureNetworkVersion', **details)
		self.assertEqual(reason, "source account is linked to an outstanding trade offer or pending exchange and can't be spent until the trade is completed or expires")
		# (end of bunch of tests for stuff not being able to use refund account)
		self.assertEqual(state._balances, {changeB:9375000-1, receiveB:1, changeA:3, refundA:100000+1})
		self.Completion(state, 0, 'receiveLTC', 10000000 // 2)
		self.assertEqual(len(state._pendingExchanges), 0)
		self.assertEqual(state._balances, {changeB:9375000-1, changeA:3, refundA:100000+1, receiveB:10625000+1})
		# and the refund account *can* now be used
		self.assertEqual(state.getSpendableAmount(refundA), 100000+1)
		outputs = self.Apply_AssertSucceeds(state, 'Pay', sourceAccount=refundA, amount=1, maxBlock=200)
		payDestination = outputs['destination']
		payChange = outputs['change']
		self.assertEqual(state._balances, {changeB:9375000-1, changeA:3, payChange:100000, payDestination:1, receiveB:10625000+1})
		self.assertEqual(state.totalAccountedFor(), state._totalCreated)

	def test_exact_match(self):
		state = State.State(100, 'starthash', minimumBalance=1)
		self.state = state
		burnB = self.Burn(1*e(7))
		changeB, receiveB = self.SellOffer(state, burnB, swapBillDesired=1*e(7), exchangeRate=0x80000000)
		# deposit is 10000000 // 16 = 625000
		self.assertEqual(state._balances, {changeB: 1*e(7)-625000-1, receiveB:1})
		burnA = self.Burn(1*e(7)+1)
		changeA, refundA = self.BuyOffer(state, burnA, 'receiveLTC', swapBillOffered=1*e(7), exchangeRate=0x80000000)
		# nothing refunded, no change to balances
		self.assertEqual(state._balances, {changeB:1*e(7)-625000-1, receiveB:1, refundA:1})
		self.assertEqual(len(state._pendingExchanges), 1)
		self.Completion(state, 0, 'receiveLTC', 1*e(7) // 2)
		self.assertEqual(len(state._pendingExchanges), 0)
		self.assertEqual(state._balances, {changeB:1*e(7)-625000-1, receiveB:1*e(7)+625000+1, refundA:1})
		self.assertEqual(state.totalAccountedFor(), state._totalCreated)

	def test_pending_exchange_expires(self):
		# based on test_exact_match, but with pending exchange left to expire
		state = State.State(100, 'starthash', minimumBalance=1)
		self.state = state
		burnB = self.Burn(1*e(7))
		changeB, receiveB = self.SellOffer(state, burnB, swapBillDesired=1*e(7), exchangeRate=0x80000000)
		# deposit is 10000000 // 16 = 625000
		self.assertEqual(state._balances, {changeB: 1*e(7)-625000-1, receiveB:1})
		burnA = self.Burn(1*e(7)+1)
		changeA, refundA = self.BuyOffer(state, burnA, 'receiveLTC', swapBillOffered=1*e(7), exchangeRate=0x80000000)
		# nothing refunded, no change to balances
		self.assertEqual(state._balances, {changeB:1*e(7)-625000-1, receiveB:1, refundA:1})
		self.assertEqual(len(state._pendingExchanges), 1)
		for i in range(50):
			state.advanceToNextBlock()
		self.assertEqual(len(state._pendingExchanges), 1)
		state.advanceToNextBlock()
		self.assertEqual(len(state._pendingExchanges), 0)
		self.assertRaisesRegexp(AssertionError, 'no pending exchange with the specified index', self.Completion, state, 0, 'receiveLTC', 1*e(7) // 2)
		self.assertEqual(state._balances, {changeB:1*e(7)-625000-1, receiveB:1, refundA:1*e(7)+625000+1})
		self.assertEqual(state.totalAccountedFor(), state._totalCreated)

	def test_offers_dont_meet(self):
		state = State.State(100, 'starthash', minimumBalance=1)
		self.state = state
		burnB = self.Burn(1*e(7))
		changeB, receiveB = self.SellOffer(state, burnB, swapBillDesired=1*e(7), exchangeRate=0x40000000)
		# deposit is 10000000 // 16 = 625000
		self.assertEqual(state._balances, {changeB: 1*e(7)-625000-1, receiveB:1})
		burnA = self.Burn(10000001)
		changeA, refundA = self.BuyOffer(state, burnA, 'receiveLTC', swapBillOffered=1*e(7), exchangeRate=0x80000000)
		# nothing refunded, no change to balances (except minimum balance seeded in a's refund accounts)
		self.assertEqual(state._balances, {changeB: 1*e(7)-625000-1, receiveB:1, refundA:1})
		self.assertEqual(len(state._pendingExchanges), 0)
		self.assertEqual(state.totalAccountedFor(), state._totalCreated)

	def test_sell_remainder_outstanding(self):
		state = State.State(100, 'starthash', minimumBalance=1)
		self.state = state
		burnB = self.Burn(20000000)
		changeB, receiveB = self.SellOffer(state, burnB, swapBillDesired=20000000, exchangeRate=0x80000000)
		# deposit is 20000000 // 16 = 1250000
		self.assertEqual(state._balances, {changeB:18750000-1, receiveB:1})
		burnA = self.Burn(10000001)
		changeA, refundA = self.BuyOffer(state, burnA, 'receiveLTC', swapBillOffered=10000000, exchangeRate=0x80000000)
		# nothing refunded, no change to balances
		self.assertEqual(state._balances, {changeB:18750000-1, receiveB:1, refundA:1})
		self.assertEqual(len(state._pendingExchanges), 1)
		self.assertEqual(state._LTCBuys.size(), 0)
		self.assertEqual(state._LTCSells.size(), 1) ## half of sell offer is left outstanding
		self.Completion(state, 0, 'receiveLTC', 10000000 // 2)
		self.assertEqual(len(state._pendingExchanges), 0)
		# b should be refunded half his deposit = 625000, plus payment of 10000000
		# (and b now has all swapbill except deposit for outstanding sell offer = 625000)
		self.assertEqual(state._balances, {changeB:18750000-1, receiveB:10625000+1, refundA:1})
		# but receiving account can't be spent yet as this is locked until exchange completed
		reason = self.Apply_AssertFails(state, 'Pay', sourceAccount=receiveB, amount=1, maxBlock=200)
		self.assertEqual(reason, "source account is linked to an outstanding trade offer or pending exchange and can't be spent until the trade is completed or expires")
		self.assertEqual(state._balances, {changeB:18750000-1, receiveB:10625000+1, refundA:1})
		# a goes on to buy the rest
		burnA2 = self.Burn(10000001)
		changeA2, refundA2 = self.BuyOffer(state, burnA2, 'receiveLTC2', swapBillOffered=10000000, exchangeRate=0x80000000)
		self.Completion(state, 1, 'receiveLTC2', 10000000 // 2)
		# other second payment counterparty + second half of deposit are credited to b's receive account
		self.assertEqual(state._balances, {changeB:18750000-1, receiveB:21250000+1, refundA:1, refundA2:1})
		# and the receive account *can* now be used
		outputs = self.Apply_AssertSucceeds(state, 'Pay', sourceAccount=receiveB, amount=1, maxBlock=200)
		payDestination = outputs['destination']
		payChange = outputs['change']
		self.assertEqual(state._balances, {changeB:18750000-1, payChange:21250000, refundA:1, refundA2:1, payDestination:1})
		self.assertEqual(state.totalAccountedFor(), state._totalCreated)

	def test_buy_remainder_outstanding(self):
		state = State.State(100, 'starthash', minimumBalance=1)
		self.state = state
		burnB = self.Burn(20000000)
		changeB, receiveB = self.SellOffer(state, burnB, swapBillDesired=20000000, exchangeRate=0x80000000)
		# deposit is 20000000 // 16 = 1250000
		self.assertEqual(state._balances, {changeB:18750000-1, receiveB:1})
		burnA = self.Burn(30000001)
		changeA, refundA = self.BuyOffer(state, burnA, 'receiveLTC', swapBillOffered=30000000, exchangeRate=0x80000000)
		# nothing refunded, no change to balances
		self.assertEqual(state._balances, {changeB:18750000-1, receiveB:1, refundA:1})
		self.assertEqual(len(state._pendingExchanges), 1)
		self.assertEqual(state._LTCBuys.size(), 1) ## half of buy offer is left outstanding
		self.assertEqual(state._LTCSells.size(), 0)
		self.Completion(state, 0, 'receiveLTC', 20000000 // 2)
		self.assertEqual(len(state._pendingExchanges), 0)
		# b should be refunded all his deposit, and receives payment in swapbill
		# refund account for a, is still locked by the buy offer
		self.assertEqual(state._balances, {changeB:18750000-1, receiveB:21250000+1, refundA:1})
		# b goes on to sell the rest
		burnB2 = self.Burn(10000000)
		changeB2, receiveB2 = self.SellOffer(state, burnB2, swapBillDesired=10000000, exchangeRate=0x80000000)
		# refund account for a, with zero amount, is still locked, now by the pending exchange
		self.assertEqual(state._balances, {changeB:18750000-1, receiveB:21250000+1, changeB2:9375000-1, receiveB2:1, refundA:1})
		self.assertEqual(len(state._pendingExchanges), 1)
		self.Completion(state, 1, 'receiveLTC', 10000000 // 2)
		self.assertEqual(len(state._pendingExchanges), 0)
		self.assertEqual(state._balances, {changeB:18750000-1, receiveB:21250000+1, changeB2:9375000-1, receiveB2:10625000+1, refundA:1})
		self.assertEqual(state.totalAccountedFor(), state._totalCreated)

	def test_trade_offers_expire(self):
		state = State.State(100, 'starthash', minimumBalance=1)
		self.state = state
		burnB = self.Burn(1*e(7))
		changeB, receiveB = self.SellOffer(state, burnB, swapBillDesired=1*e(7), exchangeRate=0x80000000, maxBlock=100, maxBlockOffset=1)
		# deposit is 10000000 // 16 = 625000
		self.assertEqual(state._balances, {changeB: 1*e(7)-625000-1, receiveB:1})
		state.advanceToNextBlock()
		self.assertEqual(state._balances, {changeB: 1*e(7)-625000-1, receiveB:1})
		self.assertEqual(state._LTCSells.size(), 1)
		state.advanceToNextBlock()
		self.assertEqual(state._LTCSells.size(), 0)
		self.assertEqual(state._balances, {changeB: 1*e(7)-625000-1, receiveB:1+625000})
		burnA = self.Burn(1*e(7)+1)
		changeA, refundA = self.BuyOffer(state, burnA, 'receiveLTC', swapBillOffered=1*e(7), exchangeRate=0x80000000, maxBlock=103, maxBlockOffset=2)
		self.assertEqual(state._balances, {changeB: 1*e(7)-625000-1, receiveB:1+625000, refundA:1})
		state.advanceToNextBlock()
		state.advanceToNextBlock()
		state.advanceToNextBlock()
		self.assertEqual(state._balances, {changeB: 1*e(7)-625000-1, receiveB:1+625000, refundA:1})
		self.assertEqual(state._LTCBuys.size(), 1)
		state.advanceToNextBlock()
		self.assertEqual(state._balances, {changeB: 1*e(7)-625000-1, receiveB:1+625000, refundA:1*e(7)+1})
		self.assertEqual(state._LTCBuys.size(), 0)
		self.assertEqual(state.totalAccountedFor(), state._totalCreated)

	def test_buy_matches_multiple_sells(self):
		state = State.State(100, 'starthash', minimumBalance=1)
		self.state = state
		changeOutputs = []
		receiveOutputs = []
		expectedBalances = {}
		for i in range(4):
			burn = self.Burn(1*e(7))
			changeOutput, receiveOutput = self.SellOffer(state, burn, swapBillDesired=1*e(7), exchangeRate=0x80000000)
			changeOutputs.append(changeOutput)
			receiveOutputs.append(receiveOutput)
			# deposit is 10000000 // 16 = 625000
			expectedBalances[changeOutput] = 1*e(7)-625000-1
			expectedBalances[receiveOutput] = 1
		self.assertEqual(state._balances, expectedBalances)
		burn = self.Burn(3*e(7)+1)
		self.assertEqual(state._LTCSells.size(), 4)
		self.assertEqual(state._LTCBuys.size(), 0)
		change, refund = self.BuyOffer(state, burn, 'receiveLTC', swapBillOffered=25*e(6), exchangeRate=0x80000000)
		# 2 sellers matched completely
		# 1 seller partially matched
		expectedBalances[change] = 5*e(6)
		expectedBalances[refund] = 1
		self.assertEqual(state._LTCSells.size(), 2)
		self.assertEqual(state._LTCBuys.size(), 0)
		self.assertEqual(len(state._pendingExchanges), 3)
		self.assertEqual(state._balances, expectedBalances)
		self.Completion(state, 0, 'receiveLTC', 5*e(6))
		# matched seller gets deposit refund + swapbill counterparty payment
		expectedBalances[receiveOutputs[0]] += 1*e(7) + 625000
		self.assertEqual(state._balances, expectedBalances)
		self.assertEqual(len(state._pendingExchanges), 2)
		self.Completion(state, 1, 'receiveLTC', 5*e(6))
		# matched seller gets deposit refund + swapbill counterparty payment
		expectedBalances[receiveOutputs[1]] += 1*e(7) + 625000
		self.assertEqual(state._balances, expectedBalances)
		self.assertEqual(len(state._pendingExchanges), 1)
		# at this point, refund account should still be locked for the trade
		reason = self.Apply_AssertFails(state, 'Pay', sourceAccount=refund, amount=1, maxBlock=200)
		self.assertEqual(reason, "source account is linked to an outstanding trade offer or pending exchange and can't be spent until the trade is completed or expires")
		# go ahead and complete last pending exchange
		self.Completion(state, 2, 'receiveLTC', 25*e(5))
		# matched seller gets deposit refund + swapbill counterparty payment
		expectedBalances[receiveOutputs[2]] += 5*e(6) + 312500
		self.assertEqual(state._balances, expectedBalances)
		self.assertEqual(len(state._pendingExchanges), 0)
		# and refund account can now be spent
		self.Apply_AssertSucceeds(state, 'Pay', sourceAccount=refund, amount=1, maxBlock=200)
		self.assertEqual(state.totalAccountedFor(), state._totalCreated)

	def test_sell_matches_multiple_buys(self):
		state = State.State(100, 'starthash', minimumBalance=1)
		self.state = state
		refundOutputs = []
		expectedBalances = {}
		for i in range(4):
			burn = self.Burn(1*e(7) + 1)
			changeOutput, refundOutput = self.BuyOffer(state, burn, 'receiveLTC', swapBillOffered=1*e(7), exchangeRate=0x80000000)
			refundOutputs.append(refundOutput)
			expectedBalances[refundOutput] = 1
		self.assertEqual(state._balances, expectedBalances)
		burn = self.Burn(25*e(6)//16 + 1)
		self.assertEqual(state._LTCBuys.size(), 4)
		self.assertEqual(state._LTCSells.size(), 0)
		change, receive = self.SellOffer(state, burn, swapBillDesired=25*e(6), exchangeRate=0x80000000)
		# deposit is 25*e(6) // 16
		# 2 buyers matched completely
		# 1 buyer partially matched
		expectedBalances[receive] = 1
		self.assertEqual(state._LTCBuys.size(), 2)
		self.assertEqual(state._LTCSells.size(), 0)
		self.assertEqual(len(state._pendingExchanges), 3)
		self.assertEqual(state._balances, expectedBalances)
		self.Completion(state, 0, 'receiveLTC', 5*e(6))
		# seller gets deposit refund + swapbill counterparty payment for this trade
		expectedBalances[receive] += 1*e(7) + 625000
		self.assertEqual(state._balances, expectedBalances)
		self.assertEqual(len(state._pendingExchanges), 2)
		self.Completion(state, 1, 'receiveLTC', 5*e(6))
		# seller gets deposit refund + swapbill counterparty payment for this trade
		expectedBalances[receive] += 1*e(7) + 625000
		self.assertEqual(state._balances, expectedBalances)
		self.assertEqual(len(state._pendingExchanges), 1)
		# at this point, receive account should still be locked for the trade
		reason = self.Apply_AssertFails(state, 'Pay', sourceAccount=receive, amount=1, maxBlock=200)
		self.assertEqual(reason, "source account is linked to an outstanding trade offer or pending exchange and can't be spent until the trade is completed or expires")
		# go ahead and complete last pending exchange
		self.Completion(state, 2, 'receiveLTC', 25*e(5))
		# seller gets deposit refund + swapbill counterparty payment for this trade
		expectedBalances[receive] += 5*e(6) + 312500
		self.assertEqual(state._balances, expectedBalances)
		self.assertEqual(len(state._pendingExchanges), 0)
		# and receive account can now be spent
		self.Apply_AssertSucceeds(state, 'Pay', sourceAccount=receive, amount=1, maxBlock=200)
		self.assertEqual(state.totalAccountedFor(), state._totalCreated)


