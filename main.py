import requests
import unittest

BEDROCK_URL = 'http://internal-Opt-Bdrkrehearse-Bdrk-Arch-stg-a-959537455.us-east-1.elb.amazonaws.com:8545'
LEGACY_URL = 'http://internal-Opt-Bdrkrehearse-Legacy-Arch-stg-1316927679.us-east-1.elb.amazonaws.com:8545'
GENESIS_BLOCKHASH = '0xc1fc15cd51159b1f1e5cbc4b82e85c1447ddfa33c52cf1d98d14fba0d6354be1'
LEGACY_LAST_BLOCKHASH = '0x019caf8d6982506581455df287f64b2d612cec6797325c87a51c6a634299a430'
LEGACY_LAST_BLOCKNUMBER = 3324763


def json_rpc(method, params, legacy):
    headers = {'Content-Type': 'application/json'}
    data = {'method': method, 'params': params, 'id': 1, 'jsonrpc': '2.0'}
    print(data)
    res = requests.post(LEGACY_URL if legacy else BEDROCK_URL, headers=headers, json=data, timeout=10)
    print(res.json())
    return res.json()


def hex_to_dec(hex):
    return int(hex, 16)


def dec_to_hex(dec):
    return hex(dec)


# Tests to compare calls hitting bedrock and legacy clusters directly
class TestCompareEthCalls(unittest.TestCase):
    def test_eth_getBlockByNumber__genesis(self):
        bedrock_json = json_rpc('eth_getBlockByNumber', ['0x0', False], legacy=False)
        legacy_json = json_rpc('eth_getBlockByNumber', ['0x0', False], legacy=True)

        self.assertIn('hash', bedrock_json['result'])
        self.assertIn('hash', legacy_json['result'])
        # both will be equal
        self.assertEqual(GENESIS_BLOCKHASH, bedrock_json['result']['hash'])
        self.assertEqual(GENESIS_BLOCKHASH, legacy_json['result']['hash'])
        self.assertEqual(bedrock_json, legacy_json)

    def test_eth_getBlockByNumber__pre_fork(self):
        bedrock_json = json_rpc('eth_getBlockByNumber', [str(dec_to_hex(LEGACY_LAST_BLOCKNUMBER)), False], legacy=False)
        legacy_json = json_rpc('eth_getBlockByNumber', [str(dec_to_hex(LEGACY_LAST_BLOCKNUMBER)), False], legacy=True)

        self.assertIn('hash', bedrock_json['result'])
        self.assertIn('hash', legacy_json['result'])
        # both will be equal
        self.assertEqual(LEGACY_LAST_BLOCKHASH, bedrock_json['result']['hash'])
        self.assertEqual(LEGACY_LAST_BLOCKHASH, legacy_json['result']['hash'])
        self.assertEqual(bedrock_json, legacy_json)

    def test_eth_getBlockByNumber__post_fork(self):
        bedrock_json = json_rpc('eth_getBlockByNumber', [str(dec_to_hex(LEGACY_LAST_BLOCKNUMBER + 1)), False], legacy=False)
        legacy_json = json_rpc('eth_getBlockByNumber', [str(dec_to_hex(LEGACY_LAST_BLOCKNUMBER + 1)), False], legacy=True)
        # legacy will not have the data but bedrock will
        self.assertIsNone(legacy_json['result'])
        self.assertIn('hash', bedrock_json['result'])
        self.assertEqual('0xcae42e6f83ffc8c6dfdae003eb2ed65f6c4b2c27f5629b1dea2be6857cccb342', bedrock_json['result']['hash'])

    """
    Only requests for historical execution (e.g., debug_traceTransaction) will 
    be routed to op-legacy so these pre-fork calls WILL be re-routed
    """
    def test_debug_traceBlockByNumber__genesis(self):
        bedrock_json = json_rpc('debug_traceBlockByNumber', ['0x0', {'tracer': 'callTracer'}], legacy=False)
        legacy_json = json_rpc('debug_traceBlockByNumber', ['0x0', {'tracer': 'callTracer'}], legacy=True)
        # both will be equal
        self.assertTrue(bedrock_json['result'])
        self.assertTrue(legacy_json['result'])

    def test_debug_traceBlockByNumber__pre_fork(self):
        bedrock_json = json_rpc('debug_traceBlockByNumber', [str(dec_to_hex(LEGACY_LAST_BLOCKNUMBER)), {'tracer': 'callTracer'}], legacy=False)
        legacy_json = json_rpc('debug_traceBlockByNumber', [str(dec_to_hex(LEGACY_LAST_BLOCKNUMBER)), {'tracer': 'callTracer'}], legacy=True)
        # both will be equal
        self.assertTrue(bedrock_json['result'])
        self.assertTrue(legacy_json['result'])

    def test_debug_traceBlockByNumber__post_fork(self):
        bedrock_json = json_rpc('debug_traceBlockByNumber', [str(dec_to_hex(LEGACY_LAST_BLOCKNUMBER + 1)), {'tracer': 'callTracer'}], legacy=False)
        legacy_json = json_rpc('debug_traceBlockByNumber', [str(dec_to_hex(LEGACY_LAST_BLOCKNUMBER + 1)), {'tracer': 'callTracer'}], legacy=True)
        # legacy will not have the data but bedrock will
        self.assertFalse(legacy_json['result'])
        self.assertTrue(bedrock_json['result'])


# All responses from op-legacy for these calls should be static
class TestLegacyEthCalls(unittest.TestCase):
    def test_eth_blockNumber(self):
        res_json = json_rpc('eth_blockNumber', [], legacy=True)
        self.assertEqual(LEGACY_LAST_BLOCKNUMBER, hex_to_dec(res_json['result']))

    def test_eth_syncing(self):
        res_json = json_rpc('eth_syncing', [], legacy=True)
        self.assertFalse(res_json['result'])


if __name__ == "__main__":
    unittest.main()
