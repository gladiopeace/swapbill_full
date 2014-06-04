from __future__ import print_function
import struct, binascii
from SwapBill import Address, HostTransaction, ControlAddressPrefix

class UnsupportedTransaction(Exception):
	pass
class NotValidSwapBillTransaction(Exception):
	pass

_fundedMappingByTypeCode = (
    ('Burn', ((0, 16), 'amount'), ('destination',), ()),
    ('Pay', (('amount', 6, 'maxBlock', 4, None, 6), None), ('change','destination'), ()),
    ('LTCBuyOffer',
     (('swapBillOffered', 6, 'maxBlock', 4, 'exchangeRate', 4, None, 2), None),
     ('change', 'ltcBuy'),
     (('receivingAddress', None),)
	),
    ('LTCSellOffer',
     (('ltcOffered', 6, 'maxBlock', 4, 'exchangeRate', 4, None, 2), None),
     ('change', 'ltcSell'),
     ()
	),
    #('BackLTCSells',
     #(('backingAmount', 6, 'maxBlock', 4, None, 6), None),
     #('change', 'refund'),
     #(('receivingAddress', None),),
	#),
	)

_forwardCompatibilityMapping = ('ForwardToFutureNetworkVersion', (('amount', 6, 'maxBlock', 4, None, 6), None), ('change',), ())

_unfundedMappingByTypeCode = (
    ('LTCExchangeCompletion',
     (('pendingExchangeIndex', 6, None, 10), None),
     (),
     (('destinationAddress', 'destinationAmount'),)
    ),
	)

def _mappingFromTypeString(transactionType):
	for i in range(len(_fundedMappingByTypeCode)):
		if transactionType == _fundedMappingByTypeCode[i][0]:
			return i, _fundedMappingByTypeCode[i]
	for i in range(len(_unfundedMappingByTypeCode)):
		if transactionType == _unfundedMappingByTypeCode[i][0]:
			return 128 + i, _unfundedMappingByTypeCode[i]
	raise Exception('Unknown transaction type string', transactionType)
def _mappingFromTypeCode(typeCode):
	if typeCode < len(_fundedMappingByTypeCode):
		return _fundedMappingByTypeCode[typeCode]
	if typeCode < 128:
		return _forwardCompatibilityMapping
	typeCode -= 128
	if typeCode < len(_unfundedMappingByTypeCode):
		return _unfundedMappingByTypeCode[typeCode]
	raise UnsupportedTransaction()

def _decodeInt(data):
	multiplier = 1
	result = 0
	for i in range(len(data)):
		byteValue = struct.unpack('<B', data[i:i + 1])[0]
		result += byteValue * multiplier
		multiplier = multiplier << 8
	return result

def _encodeInt(value, numberOfBytes):
	result = b''
	for i in range(numberOfBytes):
		byteValue = value & 255
		value = value // 256
		result += struct.pack('<B', byteValue)
	assert value == 0
	return result

def ToStateTransaction(tx):
	controlAddressData = tx.outputPubKeyHash(0)
	assert controlAddressData.startswith(ControlAddressPrefix.prefix)
	assert len(ControlAddressPrefix.prefix) == 3
	typeCode = _decodeInt(controlAddressData[3:4])
	mapping = _mappingFromTypeCode(typeCode)
	funded = (len(mapping[2]) > 0)
	transactionType = mapping[0]
	details = {}
	controlAddressMapping, amountMapping = mapping[1]
	pos = 4
	for i in range(len(controlAddressMapping) // 2):
		valueMapping = controlAddressMapping[i * 2]
		numberOfBytes = controlAddressMapping[i * 2 + 1]
		data = controlAddressData[pos:pos + numberOfBytes]
		if valueMapping == 0:
			if data != struct.pack('<B', 0) * numberOfBytes:
				raise NotValidSwapBillTransaction
		elif valueMapping is not None:
			value = _decodeInt(data)
			details[valueMapping] = value
		pos += numberOfBytes
	assert pos == 20
	if amountMapping is not None:
		details[amountMapping] = tx.outputAmount(0)
	sourceAccounts = None
	if funded:
		sourceAccounts = []
		for i in range(tx.numberOfInputs()):
			sourceAccounts.append((tx.inputTXID(i), tx.inputVOut(i)))
	outputs = mapping[2]
	destinations = mapping[3]
	for i in range(len(destinations)):
		addressMapping, amountMapping = destinations[i]
		assert addressMapping is not None
		if addressMapping is not None:
			details[addressMapping] = tx.outputPubKeyHash(1 + len(outputs) + i)
		if amountMapping is not None:
			details[amountMapping] = tx.outputAmount(1 + len(outputs) + i)
	return transactionType, sourceAccounts, outputs, details

def FromStateTransaction(transactionType, sourceAccounts, outputs, outputPubKeyHashes, details):
	assert len(outputs) == len(outputPubKeyHashes)
	typeCode, mapping = _mappingFromTypeString(transactionType)
	tx = HostTransaction.InMemoryTransaction()
	originalDetails = details
	details = originalDetails.copy()
	funded = (len(mapping[2]) > 0)
	assert funded == (sourceAccounts is not None)
	if sourceAccounts is not None:
		for txID, vout in sourceAccounts:
			tx.addInput(txID, vout)
	details[None] = 0
	details[0] = 0
	controlAddressMapping, amountMapping = mapping[1]
	controlAddressData = ControlAddressPrefix.prefix + _encodeInt(typeCode, 1)
	for i in range(len(controlAddressMapping) // 2):
		valueMapping = controlAddressMapping[i * 2]
		numberOfBytes = controlAddressMapping[i * 2 + 1]
		controlAddressData += _encodeInt(details[valueMapping], numberOfBytes)
	assert len(controlAddressData) == 20
	tx.addOutput(controlAddressData, details[amountMapping])
	expectedOutputs = mapping[2]
	assert expectedOutputs == outputs
	for pubKeyHash in outputPubKeyHashes:
		tx.addOutput(pubKeyHash, 0)
	destinations = mapping[3]
	for addressMapping, amountMapping in destinations:
		assert addressMapping is not None
		tx.addOutput(details[addressMapping], details[amountMapping])
	return tx
