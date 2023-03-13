"""Tests for the MoneyDatabase class.

To run these tests, execute this command from the project root:
$ python -m unittest discover -v
"""

import tempfile
import unittest
from unittest import mock

from monty import money_db


class FakeGuild:

    def __init__(self, id: int):
        self.id = id


class FakeMember:

    def __init__(self, id: int, guild_id: int):
        self.id = id
        self.guild = FakeGuild(id=guild_id)
        self.display_name = f'user_{self.id}_guild_{self.guild.id}'


class MoneyDatabaseTest(unittest.TestCase):

    def setUp(self) -> None:
        super().setUp()
        self.temp_dir = self.enterContext(tempfile.TemporaryDirectory())
        self.enterContext(
            mock.patch.object(money_db, '_DB_DIR', new=self.temp_dir))
        self.db = money_db.MoneyDatabase()

    def test_new_user_zero_balance(self):
        user = FakeMember(id=1, guild_id=100)
        self.assertEqual(self.db.stale_balance(user), 0.0)

    def test_can_write_one_transaction(self):
        user = FakeMember(id=1, guild_id=100)
        self.db.attempt_transaction(user, 42.0, 'Starting balance.')
        self.assertEqual(self.db.stale_balance(user), 42.0)

    def test_can_write_multiple_transaction(self):
        user = FakeMember(id=1, guild_id=100)
        self.db.attempt_transaction(user, 1.0, 'Just')
        self.db.attempt_transaction(user, 2.0, 'Some')
        self.db.attempt_transaction(user, 4.0, 'Exponential')
        self.db.attempt_transaction(user, 8.0, 'Growth')
        self.assertEqual(self.db.stale_balance(user), 15.0)

    def test_durable_storage(self):
        user = FakeMember(id=1, guild_id=100)
        self.db.attempt_transaction(user, 42.0, 'Starting balance.')
        self.assertEqual(self.db.stale_balance(user), 42.0)
        del self.db
        self.db = money_db.MoneyDatabase()
        self.assertEqual(self.db.stale_balance(user), 42.0)

    def test_cannot_withdraw_when_empty(self):
        user = FakeMember(id=1, guild_id=100)
        self.assertEqual(self.db.stale_balance(user), 0.0)
        with self.assertRaises(money_db.InsufficientFundsError):
            self.db.attempt_transaction(user, -1, 'Buy something.')

    def test_can_withdraw_insufficient(self):
        user = FakeMember(id=1, guild_id=100)
        self.db.attempt_transaction(user, 5.0, 'Starting balance.')
        with self.assertRaises(money_db.InsufficientFundsError):
            self.db.attempt_transaction(user, -10, 'Buy something.')

    def test_failures_do_not_change_balance(self):
        user = FakeMember(id=1, guild_id=100)
        self.db.attempt_transaction(user, 5.0, 'Starting balance.')
        with self.assertRaises(money_db.InsufficientFundsError):
            self.db.attempt_transaction(user, -10, 'Buy something.')
        self.assertEqual(self.db.stale_balance(user), 5.0)
        del self.db
        self.db = money_db.MoneyDatabase()
        self.assertEqual(self.db.stale_balance(user), 5.0)

    def test_mutliple_users(self):
        user1 = FakeMember(id=1, guild_id=100)
        user2 = FakeMember(id=2, guild_id=100)
        self.db.attempt_transaction(user1, 1.0, 'Starting balance.')
        self.db.attempt_transaction(user2, 2.0, 'Starting balance.')
        self.assertEqual(self.db.stale_balance(user1), 1.0)
        self.assertEqual(self.db.stale_balance(user2), 2.0)

    def test_mutliple_guilds(self):
        user1 = FakeMember(id=1, guild_id=100)
        user2 = FakeMember(id=1, guild_id=200)
        self.db.attempt_transaction(user1, 1.0, 'Starting balance.')
        self.db.attempt_transaction(user2, 2.0, 'Starting balance.')
        self.assertEqual(self.db.stale_balance(user1), 1.0)
        self.assertEqual(self.db.stale_balance(user2), 2.0)
