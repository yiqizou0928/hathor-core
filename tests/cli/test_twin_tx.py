import json
import unittest as ut
from contextlib import redirect_stdout
from io import StringIO

from hathor.cli.twin_tx import create_parser, execute
from hathor.conf import HathorSettings
from hathor.transaction import Transaction, TransactionMetadata
from tests import unittest
from tests.utils import (
    add_blocks_unlock_reward,
    add_new_blocks,
    add_new_transactions,
    execute_mining,
    execute_tx_gen,
    request_server,
    run_server,
)

settings = HathorSettings()


class TwinTxTest(unittest.TestCase):
    def setUp(self):
        super().setUp()

        self.network = 'testnet'
        self.manager = self.create_peer(self.network, unlock_wallet=True)

        add_new_blocks(self.manager, 1, advance_clock=1)
        add_blocks_unlock_reward(self.manager)
        self.tx = add_new_transactions(self.manager, 1, advance_clock=1)[0]

        self.parser = create_parser()

    def test_twin(self):
        # Normal twin
        params = ['--raw_tx', self.tx.get_struct().hex()]
        args = self.parser.parse_args(params)

        f = StringIO()
        with redirect_stdout(f):
            execute(args)

        # Transforming prints str in array
        output = f.getvalue().split('\n')
        # Last element is always empty string
        output.pop()

        twin_tx = Transaction.create_from_struct(bytes.fromhex(output[0]))
        # Parents are the same but in different order
        self.assertEqual(twin_tx.parents[0], self.tx.parents[1])
        self.assertEqual(twin_tx.parents[1], self.tx.parents[0])

        # Testing metadata creation from json
        meta_before_conflict = self.tx.get_metadata()
        meta_before_conflict_json = meta_before_conflict.to_json()
        del meta_before_conflict_json['conflict_with']
        del meta_before_conflict_json['voided_by']
        del meta_before_conflict_json['twins']
        new_meta = TransactionMetadata.create_from_json(meta_before_conflict_json)
        self.assertEqual(meta_before_conflict, new_meta)

        self.manager.propagate_tx(twin_tx)

        # Validate they are twins
        meta = self.tx.get_metadata(force_reload=True)
        self.assertEqual(meta.twins, [twin_tx.hash])

        meta2 = twin_tx.get_metadata()
        self.assertFalse(meta == meta2)

    @ut.skip
    def test_twin_different(self):
        server = run_server()

        # Unlock wallet to start mining
        request_server('wallet/unlock', 'POST', data={'passphrase': '123'})

        # Mining
        execute_mining(count=2)

        # Generating txs
        execute_tx_gen(count=4)

        response = request_server('transaction', 'GET', data={b'count': 4, b'type': 'tx'})
        tx = response['transactions'][-1]

        response = request_server('transaction', 'GET', data={b'id': tx['tx_id']})
        tx = response['tx']

        # Twin different weight and parents
        host = 'http://localhost:8085/{}/'.format(settings.API_VERSION_PREFIX)
        params = ['--url', host, '--hash', tx['hash'], '--parents', '--weight', '14']
        args = self.parser.parse_args(params)

        f = StringIO()
        with redirect_stdout(f):
            execute(args)

        # Transforming prints str in array
        output = f.getvalue().split('\n')
        # Last element is always empty string
        output.pop()

        twin_tx = Transaction.create_from_struct(bytes.fromhex(output[0]))
        # Parents are differents
        self.assertNotEqual(twin_tx.parents[0], tx['parents'][0])
        self.assertNotEqual(twin_tx.parents[0], tx['parents'][1])
        self.assertNotEqual(twin_tx.parents[1], tx['parents'][0])
        self.assertNotEqual(twin_tx.parents[1], tx['parents'][1])

        self.assertNotEqual(twin_tx.weight, tx['weight'])
        self.assertEqual(twin_tx.weight, 14.0)

        server.terminate()

    def test_twin_human(self):
        # Twin in human form
        params = ['--raw_tx', self.tx.get_struct().hex(), '--human']
        args = self.parser.parse_args(params)

        f = StringIO()
        with redirect_stdout(f):
            execute(args)

        # Transforming prints str in array
        output = f.getvalue().split('\n')
        # Last element is always empty string
        output.pop()

        human = output[0].replace("'", '"')
        tx_data = json.loads(human)

        self.assertTrue(isinstance(tx_data, dict))
        self.assertTrue('hash' in tx_data)
        self.assertTrue('timestamp' in tx_data)

        self.assertEqual(tx_data['parents'][0], self.tx.parents[1].hex())
        self.assertEqual(tx_data['parents'][1], self.tx.parents[0].hex())
        self.assertEqual(tx_data['weight'], self.tx.weight)

    def test_struct_error(self):
        # Struct error
        tx_hex = self.tx.get_struct().hex()
        params = ['--raw_tx', tx_hex + 'aa']
        args = self.parser.parse_args(params)

        f = StringIO()
        with redirect_stdout(f):
            execute(args)

        # Transforming prints str in array
        output = f.getvalue().split('\n')
        # Last element is always empty string
        output.pop()

        self.assertEqual('Error getting transaction from bytes', output[0])

    def test_parameter_error(self):
        # Parameter error
        args = self.parser.parse_args([])

        f = StringIO()
        with redirect_stdout(f):
            execute(args)

        # Transforming prints str in array
        output = f.getvalue().split('\n')
        # Last element is always empty string
        output.pop()

        self.assertEqual('The command expects raw_tx or hash and url as parameters', output[0])
