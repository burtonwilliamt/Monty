import datetime
import pickle
import os
import sqlite3

import discord

_DB_DIR = 'data/'
_DB_NAME = 'money.db'
_TABLE_NAME = 'money_history'


class InsufficientFundsError(Exception):
    """User doesn't have enough funds to perform this action."""


class MoneyDatabase:
    """Stores a log of each person's money."""

    def __init__(self):
        if not os.path.exists(_DB_DIR):
            os.makedirs(_DB_DIR)
        self._con = sqlite3.connect(_DB_DIR + _DB_NAME)
        self._create_table_if_missing()
        # mapping from guild_id -> {user_id -> balance}
        self._balance_cache: dict[int, dict[int,
                                            float]] = self._fetch_balances()

    def _create_table_if_missing(self):
        cur = self._con.cursor()
        res = cur.execute('SELECT name FROM sqlite_master').fetchone()
        if res is not None and _TABLE_NAME in res:
            return
        cur.execute(
            f'CREATE TABLE {_TABLE_NAME}(datetime, user_id, guild_id, old_value_pickle, new_value_pickle, reason)'
        )
        self._con.commit()
        cur.close()

    def _fetch_balances(self):
        cur = self._con.cursor()
        res = cur.execute(f'''
        WITH
            latest_transaction AS (
                SELECT 
                    MAX(datetime) AS datetime,
                    user_id,
                    guild_id
                FROM {_TABLE_NAME}
                GROUP BY user_id, guild_id
            )
            SELECT
                full.datetime,
                full.user_id,
                full.guild_id,
                full.new_value_pickle
            FROM {_TABLE_NAME} AS full
            LEFT JOIN latest_transaction AS latest ON full.datetime = latest.datetime
            WHERE latest.datetime IS NOT NULL
        ''')
        balances: dict[int, dict[int, float]] = {}
        for row in res:
            #datetime = datetime.datetime.fromisoformat(row[0])
            user_id = row[1]
            guild_id = row[2]
            new_value = pickle.loads(row[3])

            if guild_id not in balances:
                balances[guild_id] = {}
            if user_id in balances[guild_id]:
                raise RuntimeError(
                    f'User {user_id} has multiple latest transactions.')

            balances[guild_id][user_id] = new_value

        return balances

    def _balance(self, user: discord.Member) -> float:
        return self._balance_cache.get(user.guild.id, {}).get(user.id, 0.0)

    def stale_balance(self, user: discord.Member) -> float:
        """Fetch a user's (maybe) stale balance."""
        return self._balance(user)

    def stale_guild_balances(self, guild_id: int) -> dict[int, float]:
        return dict(self._balance_cache.get(guild_id, {}))

    def _update_cache(self, user_id: int, guild_id: int, balance: float) -> None:
        if guild_id not in self._balance_cache:
            self._balance_cache[guild_id] = {}
        self._balance_cache[guild_id][user_id] = balance

    def attempt_transaction(self, user: discord.Member, delta: float,
                            reason: str) -> None:
        """Try to perform a transaction for a user.
        
        Raises:
            InsufficientFundsError: if the user doesn't have enough money.
        """
        user_id = user.id
        guild_id = user.guild.id
        current_value = self._balance(user)
        if delta < 0 and (delta + current_value) < 0:
            raise InsufficientFundsError(
                f'{user.display_name} does not have enough funds ({current_value} < {-delta}).'
            )
        new_value = current_value + delta
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        cur = self._con.cursor()

        cur.execute(
            f'INSERT INTO {_TABLE_NAME} VALUES(?, ?, ?, ?, ?, ?)',
            (now, user_id, guild_id, pickle.dumps(current_value, protocol=5),
             pickle.dumps(new_value, protocol=5), reason))
        self._con.commit()
        cur.close()
        self._update_cache(user_id, guild_id, new_value)