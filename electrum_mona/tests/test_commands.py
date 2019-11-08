import unittest
from unittest import mock
from decimal import Decimal

from electrum_mona.util import create_and_start_event_loop
from electrum_mona.commands import Commands, eval_bool
from electrum_mona import storage
from electrum_mona.wallet import restore_wallet_from_text
from electrum_mona.simple_config import SimpleConfig

from . import TestCaseForTestnet, ElectrumTestCase


class TestCommands(ElectrumTestCase):

    def setUp(self):
        super().setUp()
        self.asyncio_loop, self._stop_loop, self._loop_thread = create_and_start_event_loop()
        self.config = SimpleConfig({'electrum_path': self.electrum_path})

    def tearDown(self):
        super().tearDown()
        self.asyncio_loop.call_soon_threadsafe(self._stop_loop.set_result, 1)
        self._loop_thread.join(timeout=1)       

    def test_setconfig_non_auth_number(self):
        self.assertEqual(7777, Commands._setconfig_normalize_value('rpcport', "7777"))
        self.assertEqual(7777, Commands._setconfig_normalize_value('rpcport', '7777'))
        self.assertAlmostEqual(Decimal(2.3), Commands._setconfig_normalize_value('somekey', '2.3'))

    def test_setconfig_non_auth_number_as_string(self):
        self.assertEqual("7777", Commands._setconfig_normalize_value('somekey', "'7777'"))

    def test_setconfig_non_auth_boolean(self):
        self.assertEqual(True, Commands._setconfig_normalize_value('show_console_tab', "true"))
        self.assertEqual(True, Commands._setconfig_normalize_value('show_console_tab', "True"))

    def test_setconfig_non_auth_list(self):
        self.assertEqual(['file:///var/www/', 'https://electrum.org'],
            Commands._setconfig_normalize_value('url_rewrite', "['file:///var/www/','https://electrum.org']"))
        self.assertEqual(['file:///var/www/', 'https://electrum.org'],
            Commands._setconfig_normalize_value('url_rewrite', '["file:///var/www/","https://electrum.org"]'))

    def test_setconfig_auth(self):
        self.assertEqual("7777", Commands._setconfig_normalize_value('rpcuser', "7777"))
        self.assertEqual("7777", Commands._setconfig_normalize_value('rpcuser', '7777'))
        self.assertEqual("7777", Commands._setconfig_normalize_value('rpcpassword', '7777'))
        self.assertEqual("2asd", Commands._setconfig_normalize_value('rpcpassword', '2asd'))
        self.assertEqual("['file:///var/www/','https://electrum.org']",
            Commands._setconfig_normalize_value('rpcpassword', "['file:///var/www/','https://electrum.org']"))

    def test_eval_bool(self):
        self.assertFalse(eval_bool("False"))
        self.assertFalse(eval_bool("false"))
        self.assertFalse(eval_bool("0"))
        self.assertTrue(eval_bool("True"))
        self.assertTrue(eval_bool("true"))
        self.assertTrue(eval_bool("1"))

    def test_convert_xkey(self):
        cmds = Commands(config=self.config)
        xpubs = {
            ("xpub6CCWFbvCbqF92kGwm9nV7t7RvVoQUKaq5USMdyVP6jvv1NgN52KAX6NNYCeE8Ca7JQC4K5tZcnQrubQcjJ6iixfPs4pwAQJAQgTt6hBjg11", "standard"),
            ("ypub6X2mZGb7kWnct3U4bWa7KyCw6TwrQwaKzaxaRNPGUkJo4UVbKgUj9A2WZQbp87E2i3Js4ZV85SmQnt2BSzWjXCLzjQXMkK7egQXXVHT4eKn", "p2wpkh-p2sh"),
            ("zpub6qs2rwG2uCL6jLfBRsMjY4JSGS6JMZZpuhUoCmH9rkgg7aJpaLeHmDgeacZQ81sx7gRfp35gY77xgAdkAgvkKS2bbkDnLDw8x8bAsuKBrvP", "p2wpkh"),
        }
        for xkey1, xtype1 in xpubs:
            for xkey2, xtype2 in xpubs:
                self.assertEqual(xkey2, cmds._run('convert_xkey', (xkey1, xtype2)))

        xprvs = {
            ("xprv9yD9r6PJmTgqpGCUf8FUkkAhNTxv4rryiFWkqb5mYQPw8aMDXUzuyJ3tgv5vUqYkdK1E6Q5jKxPss4HkMBYV4q8AfG8t7rxgyS4xQX4ndAm", "standard"),
            ("yprvAJ3R9m4Dv9EKfZPbVV36xqGCYS7N1UrUdN2ycyyevQmpBgASn9AUbMi2i83WUkCg2x82qsgHnckRkLuK4sxVs4omXbqJhmnBFA8bo8ssinK", "p2wpkh-p2sh"),
            ("zprvAcsgTRj94pmoWraiKqpjAvMhiQFox6qyYUZCQNsYJR9hEmyg2oL3DRNAjL16UerbSbEqbMGrFH6yddWsnaNWfJVNPwXjHgbfWtCFBgDxFkX", "p2wpkh"),
        }
        for xkey1, xtype1 in xprvs:
            for xkey2, xtype2 in xprvs:
                self.assertEqual(xkey2, cmds._run('convert_xkey', (xkey1, xtype2)))

    @mock.patch.object(storage.WalletStorage, '_write')
    def test_encrypt_decrypt(self, mock_write):
        wallet = restore_wallet_from_text('p2wpkh:T8a4cDwcDBCe7XnbULMWTFF2JS3ZduMPiQ7n2TafyZXN3dAqzEg5',
                                          path='if_this_exists_mocking_failed_648151893',
                                          config=self.config)['wallet']
        cmds = Commands(config=self.config)
        cleartext = "asdasd this is the message"
        pubkey = "03b9ace321eddd5037f35bc141a9f6cbd54d5064b917da1ef02e1b575f410f5e11"
        ciphertext = cmds._run('encrypt', (pubkey, cleartext))
        self.assertEqual(cleartext, cmds._run('decrypt', (pubkey, ciphertext), wallet=wallet))

    @mock.patch.object(storage.WalletStorage, '_write')
    def test_export_private_key_imported(self, mock_write):
        wallet = restore_wallet_from_text('p2wpkh:TAgoypi14k5Y54svysG62xp5QFRWiF1W64zxaFRFPo2jMPSMoa5D p2wpkh:T4jS4CCdekC3hvV6AY7gKoRU3PFpJdoKY9uczbR3dpv8ypZHiP65',
                                          path='if_this_exists_mocking_failed_648151893',
                                          config=self.config)['wallet']
        cmds = Commands(config=self.config)
        # single address tests
        with self.assertRaises(Exception):
            cmds._run('getprivatekeys', ("asdasd",), wallet=wallet)  # invalid addr, though might raise "not in wallet"
        with self.assertRaises(Exception):
            cmds._run('getprivatekeys', ("mona1qy7ykhcu6608jqulvw5amkym7rhkk2z9vpugy22",), wallet=wallet)  # not in wallet
        self.assertEqual("p2wpkh:T4jS4CCdekC3hvV6AY7gKoRU3PFpJdoKY9uczbR3dpv8ypZHiP65",
                         cmds._run('getprivatekeys', ("mona1qsahc3f7s9mw407aqttez283zmffx0u86t6xh8h",), wallet=wallet))
        # list of addresses tests
        with self.assertRaises(Exception):
            cmds._run('getprivatekeys', (['mona1qsahc3f7s9mw407aqttez283zmffx0u86t6xh8h', 'asd'], ), wallet=wallet)
        self.assertEqual(['p2wpkh:T4jS4CCdekC3hvV6AY7gKoRU3PFpJdoKY9uczbR3dpv8ypZHiP65', 'p2wpkh:TAgoypi14k5Y54svysG62xp5QFRWiF1W64zxaFRFPo2jMPSMoa5D'],
                         cmds._run('getprivatekeys', (['mona1qsahc3f7s9mw407aqttez283zmffx0u86t6xh8h', 'mona1q9pzjpjq4nqx5ycnywekcmycqz0wjp2nq7urx8j'], ), wallet=wallet))

    @mock.patch.object(storage.WalletStorage, '_write')
    def test_export_private_key_deterministic(self, mock_write):
        wallet = restore_wallet_from_text('bitter grass shiver impose acquire brush forget axis eager alone wine silver',
                                          gap_limit=2,
                                          path='if_this_exists_mocking_failed_648151893',
                                          config=self.config)['wallet']
        cmds = Commands(config=self.config)
        # single address tests
        with self.assertRaises(Exception):
            cmds._run('getprivatekeys', ("asdasd",), wallet=wallet)  # invalid addr, though might raise "not in wallet"
        with self.assertRaises(Exception):
            cmds._run('getprivatekeys', ("mona1qy7ykhcu6608jqulvw5amkym7rhkk2z9vpugy22",), wallet=wallet)  # not in wallet
        self.assertEqual("p2wpkh:T6v5Q8KEmjLmJoTxPfXfyNcCEFYC7Lfmwmp9Y8dce9knevo9ZkPk",
                         cmds._run('getprivatekeys', ("mona1q3g5tmkmlvxryhh843v4dz026avatc0zz8fpnsg",), wallet=wallet))
        # list of addresses tests
        with self.assertRaises(Exception):
            cmds._run('getprivatekeys', (['mona1q3g5tmkmlvxryhh843v4dz026avatc0zz8fpnsg', 'asd'],), wallet=wallet)
        self.assertEqual(['p2wpkh:T6v5Q8KEmjLmJoTxPfXfyNcCEFYC7Lfmwmp9Y8dce9knevo9ZkPk', 'p2wpkh:TAgoypi14k5Y54svysG62xp5QFRWiF1W64zxaFRFPo2jMPSMoa5D'],
                         cmds._run('getprivatekeys', (['mona1q3g5tmkmlvxryhh843v4dz026avatc0zz8fpnsg', 'mona1q9pzjpjq4nqx5ycnywekcmycqz0wjp2nq7urx8j'], ), wallet=wallet))


class TestCommandsTestnet(TestCaseForTestnet):

    def setUp(self):
        super().setUp()
        self.asyncio_loop, self._stop_loop, self._loop_thread = create_and_start_event_loop()
        self.config = SimpleConfig({'electrum_path': self.electrum_path})

    def tearDown(self):
        super().tearDown()
        self.asyncio_loop.call_soon_threadsafe(self._stop_loop.set_result, 1)
        self._loop_thread.join(timeout=1)

    def test_convert_xkey(self):
        cmds = Commands(config=self.config)
        xpubs = {
            ("tpubD8p5qNfjczgTGbh9qgNxsbFgyhv8GgfVkmp3L88qtRm5ibUYiDVCrn6WYfnGey5XVVw6Bc5QNQUZW5B4jFQsHjmaenvkFUgWtKtgj5AdPm9", "standard"),
            ("upub59wfQ8qJTg6ZSuvwtR313Qdp8gP8TSBwTof5dPQ3QVsYp1N9t29Rr9TGF1pj8kAXUg3mKbmrTKasA2qmBJKb1bGUzB6ApDZpVC7LoHhyvBo", "p2wpkh-p2sh"),
            ("vpub5UmvhoWDcMe3JD84impdFVjKJeXaQ4BSNvBJQnHvnWFRs7BP8gJzUD7QGDnK8epStKAa55NQuywR3KTKtzjbopx5rWnbQ8PJkvAzBtgaGBc", "p2wpkh"),
        }
        for xkey1, xtype1 in xpubs:
            for xkey2, xtype2 in xpubs:
                self.assertEqual(xkey2, cmds._run('convert_xkey', (xkey1, xtype2)))

        xprvs = {
            ("tprv8c83gxdVUcznP8fMx2iNUBbaQgQC7MUbBUDG3c6YU9xgt7Dn5pfcgHUeNZTAvuYmNgVHjyTzYzGWwJr7GvKCm2FkPaaJipyipbfJeB3tdPW", "standard"),
            ("uprv8vxJzdJQdJYGERrUnPVzgGh5aeYe3yU66ajUpzzRrALZwD31LUqBJM8nPmQkvpCgnKc6VT4Z1ed4pbTfzcjDZFwMFvGjJjoD6Kix2pCwVe7", "p2wpkh-p2sh"),
            ("vprv9FnaJHyKmz5k5j3bckHctMnakch5zbTb1hFhcPtKEAiSzJrEb8zjvQnvQyNLvircBxiuEvf7UJycht5EiK9EMVcx8Fy9techN3nbRQRFhEv", "p2wpkh"),
        }
        for xkey1, xtype1 in xprvs:
            for xkey2, xtype2 in xprvs:
                self.assertEqual(xkey2, cmds._run('convert_xkey', (xkey1, xtype2)))

    def test_serialize(self):
        cmds = Commands(config=self.config)
        jsontx = {
            "inputs": [
                {
                    "prevout_hash": "9d221a69ca3997cbeaf5624d723e7dc5f829b1023078c177d37bdae95f37c539",
                    "prevout_n": 1,
                    "value": 1000000,
                    "privkey": "p2wpkh:cVDXzzQg6RoCTfiKpe8MBvmm5d5cJc6JLuFApsFDKwWa6F5TVHpD"
                }
            ],
            "outputs": [
                {
                    "address": "tmona1q6h4n2rkl9vr2dka0ac00gpztrx0xkd0568925z",
                    "value": 990000
                }
            ]
        }
        self.assertEqual("0200000000010139c5375fe9da7bd377c1783002b129f8c57d3e724d62f5eacb9739ca691a229d0100000000feffffff01301b0f0000000000160014d5eb350edf2b06a6dbafee1ef4044b199e6b35f40247304402201ced9264e057d026c025eec26044cfa4552dc04d4b68c974a51554150bb3de600220109b8cea264e3b7ea0a7f9d8a9ce8be333a81df3d3b6e4f54b4827bb653486da0121021f110909ded653828a254515b58498a6bafc96799fb0851554463ed44ca7d9da00000000",
                         cmds._run('serialize', (jsontx,)))
