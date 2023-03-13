import asyncio
from collections.abc import Sequence
import json
import http.client
import logging
import random
from typing import Any
import urllib.parse

import discord
from discord import app_commands
import discord.ext.commands
import racket

from monty import money_db
from monty.cogs.text_options import BEG_OPTIONS

_log = logging.getLogger(__name__)


def choose_with_distribution(choices: Sequence[Any]) -> Any:
    weights = [len(choices) - i for i in range(len(choices))]
    return random.choices(choices, weights=weights)[0]


class MontyCog(discord.ext.commands.Cog):
    """Collection of miscellaneous commands."""

    def __init__(self, bot: racket.RacketBot):
        self.bot = bot
        self.money = money_db.MoneyDatabase()

    @app_commands.command()
    async def celery_man(self, interaction: discord.Interaction):
        """Computer bring up Celery Man."""
        await interaction.response.send_message(
            'https://thumbs.gfycat.com/DampHandyGoosefish-small.gif')

    @app_commands.command()
    async def anon(self, interaction: discord.Interaction,
                   message: app_commands.Range[str, 1, 2000]):
        """Send a message anonymously.
        
        Args:
            message: The message you want to send anonymously.
        """
        await interaction.response.send_message(
            'Ok, I\'ll send that message on your behalf.', ephemeral=True)

        await interaction.channel.send(f'{message}', allowed_mentions=None)

    @racket.context_menu()
    async def mock(self, interaction: discord.Interaction,
                   message: discord.Message):
        """mAkE fUn Of WhAt ThEy SaId."""
        content = message.content
        mocked = []

        upper = False
        for c in content:
            if not c.isalpha():
                mocked.append(c)
                continue

            if upper:
                mocked.append(c.upper())
            else:
                mocked.append(c.lower())
            upper = not upper

        await interaction.response.send_message(''.join(mocked))

    @app_commands.command()
    async def ud(self, interaction: discord.Interaction, term: str):
        """Fetches a definition from urban dictionary."""
        conn = http.client.HTTPSConnection('api.urbandictionary.com')
        encoded_term = urllib.parse.quote(term, safe='')
        conn.request('GET', f'/v0/define?term={encoded_term}')
        res = conn.getresponse()

        data_bytes = res.read()
        if len(data_bytes) == 0:
            await interaction.response.send_message('Failed to get a definition'
                                                   )
            return
        data = json.loads(data_bytes.decode('utf-8'))
        the_list = data['list']
        first_result = the_list[0]

        word = first_result['word']
        permalink = first_result['permalink']
        definition = first_result['definition'].replace(r'\r\n', '\n')
        e = discord.Embed(description=f'[{word}]({permalink})\n\n' + definition)
        await interaction.response.send_message(embed=e)

    @app_commands.command()
    async def beg(self, interaction: discord.Interaction):
        """Looking for handouts?"""
        amount = random.choices([1, 2, 10, 100, 4.2069],
                                weights=[100, 50, 10, 1, 1])[0]
        self.money.attempt_transaction(interaction.user, amount, 'begging')
        await interaction.response.send_message(
            f'You have been given `{amount}` credits.\n' +
            choose_with_distribution(BEG_OPTIONS))
