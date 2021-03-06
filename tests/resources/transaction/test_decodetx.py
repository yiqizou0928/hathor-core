from twisted.internet.defer import inlineCallbacks

from hathor.transaction.genesis import get_genesis_transactions
from hathor.transaction.resources import DecodeTxResource
from hathor.transaction.scripts import parse_address_script
from tests.resources.base_resource import StubSite, _BaseResourceTest
from tests.utils import add_blocks_unlock_reward, create_tokens


class DecodeTxTest(_BaseResourceTest._ResourceTest):
    def setUp(self):
        super().setUp()
        self.web = StubSite(DecodeTxResource(self.manager))

    @inlineCallbacks
    def test_get(self):
        genesis_tx = get_genesis_transactions(self.manager.tx_storage)[1]
        response_success = yield self.web.get("decode_tx", {b'hex_tx': bytes(genesis_tx.get_struct().hex(), 'utf-8')})
        data_success = response_success.json_value()

        self.assertTrue(data_success['success'])
        data_genesis = genesis_tx.to_json(decode_script=True)
        data_genesis['raw'] = genesis_tx.get_struct().hex()
        self.assertEqual(data_success['tx'], data_genesis)
        self.assertTrue('meta' in data_success)
        self.assertTrue('spent_outputs' in data_success)

        # Invalid hex
        response_error1 = yield self.web.get("decode_tx", {b'hex_tx': b'XXXX'})
        data_error1 = response_error1.json_value()

        self.assertFalse(data_error1['success'])

        # Invalid tx hex
        response_error2 = yield self.web.get("decode_tx", {b'hex_tx': b'a12c'})
        data_error2 = response_error2.json_value()

        self.assertFalse(data_error2['success'])

        # Token creation tx
        script_type_out = parse_address_script(get_genesis_transactions(self.manager.tx_storage)[0].outputs[0].script)
        address = script_type_out.address
        add_blocks_unlock_reward(self.manager)
        tx2 = create_tokens(self.manager, address, mint_amount=100, propagate=True)
        response = yield self.web.get('decode_tx', {b'hex_tx': bytes(tx2.get_struct().hex(), 'utf-8')})
        data = response.json_value()
        self.assertTrue(data['success'])
