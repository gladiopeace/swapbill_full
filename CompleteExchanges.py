from __future__ import print_function
import sys, time
from os import path
scriptPath = path.dirname(path.abspath(__file__))
sys.path.append(path.join(scriptPath, 'module'))
sys.dont_write_bytecode = True
from SwapBill import ClientMain
from SwapBill.ExceptionReportedToUser import ExceptionReportedToUser
from SwapBill.HardCodedProtocolConstraints import Constraints

def getMatchingExchange(result, backerID):
	for s, key, d in result:
		if d.get('backer id', None) != backerID:
			continue
		if d['blocks until expiry'] > Constraints.blocksForExchangeCompletion - 10:
			# not enough confirmations
			continue
		return key, d
	return None, None

startBlockIndex=300909
startBlockHash='3610b1e7ea80e3a4a73cac696261736e849290dce07598c4da85a9f5a4504c29'

while True:
	try:
		result = ClientMain.Main(commandLineArgs=['get_pending_exchanges'], startBlockIndex=startBlockIndex, startBlockHash=startBlockHash, useTestNet=True)
	except ExceptionReportedToUser as e:
		print("get_pending_exchanges failed:", e)
		time.sleep(40)
		continue
	exchangeID, exchangeDetails = getMatchingExchange(result, 0)
	if exchangeID is None:
		time.sleep(40)
		continue
	# go ahead and complete
	try:
		result = ClientMain.Main(commandLineArgs=['complete_ltc_sell', '--pendingExchangeID', str(exchangeID)], startBlockIndex=startBlockIndex, startBlockHash=startBlockHash, useTestNet=True)
	except ExceptionReportedToUser as e:
		print("complete_ltc_sell failed:", e)
	time.sleep(40)
