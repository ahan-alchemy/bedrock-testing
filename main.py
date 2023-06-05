import requests
import unittest

BEDROCK_URL = 'http://internal-Opt-Goer-Bedrock-Arch-prod-alb-701384941.us-east-1.elb.amazonaws.com:8545'
LEGACY_URL = 'http://internal-Opt-Goer-Legacy-Arch-prod-alb-188237485.us-east-1.elb.amazonaws.com:8545'
GENESIS_BLOCKHASH = '0xc1fc15cd51159b1f1e5cbc4b82e85c1447ddfa33c52cf1d98d14fba0d6354be1'
LEGACY_LAST_BLOCKHASH = '0x31267a44f1422f4cab59b076548c075e79bd59e691a23fbce027f572a2a49dc9'
LEGACY_LAST_BLOCKNUMBER = 4061223


def json_rpc(self, method, params, legacy):
    headers = {'Content-Type': 'application/json'}
    data = {'method': method, 'params': params, 'id': 1, 'jsonrpc': '2.0'}
    res = requests.post(LEGACY_URL if legacy else BEDROCK_URL, headers=headers, json=data, timeout=10)
    print(res.json())
    # assert 200
    self.assertEqual(200, res.status_code)
    return res.json()


def hex_to_dec(hex):
    return int(hex, 16)


def dec_to_hex(dec):
    return hex(dec)


# Tests to compare calls hitting bedrock and legacy clusters directly
class TestCompareEthCalls(unittest.TestCase):
    def test_eth_getBlockByNumber__genesis(self):
        bedrock_json = json_rpc(self, 'eth_getBlockByNumber', ['0x0', False], legacy=False)
        legacy_json = json_rpc(self, 'eth_getBlockByNumber', ['0x0', False], legacy=True)

        self.assertIn('hash', bedrock_json['result'])
        self.assertIn('hash', legacy_json['result'])
        # both will be equal
        self.assertEqual(GENESIS_BLOCKHASH, bedrock_json['result']['hash'])
        self.assertEqual(GENESIS_BLOCKHASH, legacy_json['result']['hash'])
        self.assertEqual(bedrock_json, legacy_json)

    def test_eth_getBlockByNumber__pre_fork(self):
        bedrock_json = json_rpc(self, 'eth_getBlockByNumber', [str(dec_to_hex(LEGACY_LAST_BLOCKNUMBER)), False], legacy=False)
        legacy_json = json_rpc(self, 'eth_getBlockByNumber', [str(dec_to_hex(LEGACY_LAST_BLOCKNUMBER)), False], legacy=True)

        self.assertIn('hash', bedrock_json['result'])
        self.assertIn('hash', legacy_json['result'])
        # both will be equal
        self.assertEqual(LEGACY_LAST_BLOCKHASH, bedrock_json['result']['hash'])
        self.assertEqual(LEGACY_LAST_BLOCKHASH, legacy_json['result']['hash'])
        self.assertEqual(bedrock_json, legacy_json)

    def test_eth_getBlockByNumber__post_fork(self):
        bedrock_json = json_rpc(self, 'eth_getBlockByNumber', [str(dec_to_hex(LEGACY_LAST_BLOCKNUMBER + 1)), False], legacy=False)
        legacy_json = json_rpc(self, 'eth_getBlockByNumber', [str(dec_to_hex(LEGACY_LAST_BLOCKNUMBER + 1)), False], legacy=True)
        # legacy will not have the data but bedrock will
        self.assertIsNone(legacy_json['result'])
        self.assertIn('hash', bedrock_json['result'])
        self.assertEqual('0x0f783549ea4313b784eadd9b8e8a69913b368b7366363ea814d7707ac505175f', bedrock_json['result']['hash'])

    """
    Only requests for historical execution (e.g., debug_traceTransaction) will 
    be routed to op-legacy so these pre-fork calls WILL be re-routed
    """
    def test_debug_traceBlockByNumber__genesis(self):
        bedrock_json = json_rpc(self, 'debug_traceBlockByNumber', ['0x1', {'tracer': 'callTracer'}], legacy=False)
        legacy_json = json_rpc(self, 'debug_traceBlockByNumber', ['0x1', {'tracer': 'callTracer'}], legacy=True)
        # both will be equal
        self.assertIn('result', bedrock_json)
        self.assertIn('result', legacy_json)

    def test_debug_traceBlockByNumber__pre_fork(self):
        bedrock_json = json_rpc(self, 'debug_traceBlockByNumber', [str(dec_to_hex(LEGACY_LAST_BLOCKNUMBER)), {'tracer': 'callTracer'}], legacy=False)
        legacy_json = json_rpc(self, 'debug_traceBlockByNumber', [str(dec_to_hex(LEGACY_LAST_BLOCKNUMBER)), {'tracer': 'callTracer'}], legacy=True)
        # both will be equal
        self.assertTrue(bedrock_json['result'])
        self.assertTrue(legacy_json['result'])

    def test_debug_traceBlockByNumber__post_fork(self):
        bedrock_json = json_rpc(self, 'debug_traceBlockByNumber', [str(dec_to_hex(LEGACY_LAST_BLOCKNUMBER + 1)), {'tracer': 'callTracer'}], legacy=False)
        legacy_json = json_rpc(self, 'debug_traceBlockByNumber', [str(dec_to_hex(LEGACY_LAST_BLOCKNUMBER + 1)), {'tracer': 'callTracer'}], legacy=True)
        # legacy will not have the data but bedrock will
        self.assertIn('result', bedrock_json)
        self.assertNotIn('result', legacy_json)


# All responses from op-legacy for these calls should be static
class TestLegacyEthCalls(unittest.TestCase):
    def test_eth_blockNumber(self):
        res_json = json_rpc(self, 'eth_blockNumber', [], legacy=True)
        self.assertEqual(LEGACY_LAST_BLOCKNUMBER, hex_to_dec(res_json['result']))

    def test_eth_syncing(self):
        res_json = json_rpc(self, 'eth_syncing', [], legacy=True)
        self.assertFalse(res_json['result'])


if __name__ == "__main__":
    unittest.main()
