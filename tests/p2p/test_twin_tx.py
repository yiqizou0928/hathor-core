from twisted.internet.task import Clock

from tests import unittest
from tests.utils import add_new_blocks

from hathor.transaction import Transaction
from hathor.wallet.base_wallet import WalletOutputInfo

import time


class TwinTransactionTestCase(unittest.TestCase):
    def setUp(self):
        super().setUp()

        self.clock = Clock()
        self.clock.advance(time.time())
        self.network = 'testnet'
        self.manager = self.create_peer(self.network, unlock_wallet=True)

    def test_twin_tx(self):
        add_new_blocks(self.manager, 5, advance_clock=15)

        address = '3JEcJKVsHddj1Td2KDjowZ1JqGF1'
        value1 = 100
        value2 = 101
        value3 = 102

        outputs = [
            WalletOutputInfo(address=self.manager.wallet.decode_address(address), value=int(value1), timelock=None),
            WalletOutputInfo(address=self.manager.wallet.decode_address(address), value=int(value2), timelock=None)
        ]

        outputs2 = [
            WalletOutputInfo(address=self.manager.wallet.decode_address(address), value=int(value1), timelock=None),
            WalletOutputInfo(address=self.manager.wallet.decode_address(address), value=int(value3), timelock=None)
        ]

        tx1 = self.manager.wallet.prepare_transaction_compute_inputs(Transaction, outputs)
        tx1.weight = 10
        tx1.parents = self.manager.get_new_tx_parents()
        tx1.timestamp = int(self.clock.seconds())
        tx1.resolve()

        # Change of parents only, so it's a twin
        tx2 = Transaction.create_from_struct(tx1.get_struct())
        tx2.parents = [tx1.parents[1], tx1.parents[0]]
        tx2.resolve()
        self.assertNotEqual(tx1.hash, tx2.hash)

        # The same as tx1 but with one input different, so it's not a twin
        tx3 = self.manager.wallet.prepare_transaction_compute_inputs(Transaction, outputs2)
        tx3.inputs = tx1.inputs
        tx3.weight = tx1.weight
        tx3.parents = tx1.parents
        tx3.timestamp = tx1.timestamp
        tx3.resolve()

        self.manager.propagate_tx(tx1)
        meta1 = tx1.get_metadata()
        self.assertEqual(meta1.conflict_with, set())
        self.assertEqual(meta1.voided_by, set())
        self.assertEqual(meta1.twins, set())

        # Propagate a conflicting twin transaction
        self.manager.propagate_tx(tx2)

        meta1 = tx1.get_metadata()
        self.assertEqual(meta1.conflict_with, {tx2.hash})
        self.assertEqual(meta1.voided_by, {tx1.hash})
        self.assertEqual(meta1.twins, {tx2.hash})

        meta2 = tx2.get_metadata()
        self.assertEqual(meta2.conflict_with, {tx1.hash})
        self.assertEqual(meta2.voided_by, {tx2.hash})
        self.assertEqual(meta2.twins, {tx1.hash})

        # Propagate another conflicting transaction but it's not a twin
        self.manager.propagate_tx(tx3)

        meta1 = tx1.get_metadata()
        self.assertEqual(meta1.twins, {tx2.hash})

        meta3 = tx3.get_metadata()
        self.assertEqual(meta3.twins, set())
