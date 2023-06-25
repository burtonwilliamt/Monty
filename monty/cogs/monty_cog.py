from collections.abc import Sequence
import datetime
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
from faker import Faker

from monty import money_db
from monty.cogs.text_options import BEG_OPTIONS

_log = logging.getLogger(__name__)
fake_generator = Faker()


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
    async def behold(self, interaction: discord.Interaction, thing_being_looked_at: str):
        """LOOK wonderingly at an emoji or something."""
        message = (f'{thing_being_looked_at.strip()}'
                   '<:bb1:855882629714018334>'
                   '<:bb2:855882629878120488>'
                   '\n'
                   '<:bb3:855882629844172800>'
                   '<:bb4:855882629731975198>'
                   '<:bb5:855882629761204284>'
                   )
        await interaction.response.send_message(message)

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

    @racket.context_menu()
    async def random_emoji(self, interaction: discord.Interaction,
                           message: discord.Message):
        """React to this message with a random animated emoji."""
        if not message.channel.permissions_for(
                interaction.guild.me).add_reactions:
            await interaction.response.send_message(
                'I\'m not able to add reactions here. If you don\'t see me in '
                'the top right I might need to be added to this channel.')
            return
        existing_emojis = [r.emoji for r in message.reactions]
        await message.add_reaction(
            random.choice([
                e for e in interaction.guild.emojis
                if e.animated and e not in existing_emojis
            ]))
        await interaction.response.send_message('Reacted.',
                                                ephemeral=True,
                                                delete_after=1.0)

    @app_commands.command()
    async def leaderboard(self, interaction: discord.Interaction):
        """Find out who the 1% really are."""
        leaderboard = self.money.stale_guild_balances(interaction.guild.id)
        pairs = [[await interaction.guild.fetch_member(user_id), value]
                 for user_id, value in leaderboard.items()]
        if len(pairs) == 0:
            await interaction.response.send_message(
                'No leaderboard for this server.')
            return

        pairs.sort(key=lambda p: p[1])
        lines = [
            f'`{i+1}` `{pair[0].display_name}` `{pair[1]}`'
            for i, pair in enumerate(pairs)
        ]
        await interaction.response.send_message('\n'.join(lines))

    @app_commands.command()
    async def fake_person(self, interaction: discord.Interaction):
        """Generate a fake persona."""
        e = discord.Embed()
        first = fake_generator.first_name()
        last = fake_generator.last_name()
        e.add_field(name='Name', value=first + ' ' + last)
        bday = fake_generator.date_of_birth(minimum_age=18, maximum_age=90)
        today = datetime.date.today()
        age = today.year - bday.year - ((today.month, today.day) < (bday.month, bday.day))
        e.add_field(name='DOB', value=f'{bday}({age})')
        e.add_field(name='SSN', value=fake_generator.ssn())
        e.add_field(name='Adddress', value=fake_generator.address())
        e.add_field(name='Phone Number', value=fake_generator.phone_number())
        domain = fake_generator.free_email_domain()
        email = f'{random.choice([first, first[0]])}{random.choice(("", "."))}{last}{random.choice((random.randint(0, 100), ""))}@{domain}'
        e.add_field(name='Email', value=email.lower())
        e.add_field(name='Job', value=fake_generator.job())
        e.add_field(name='Employeer', value=fake_generator.company())
        e.add_field(name='License Plate', value=fake_generator.license_plate())
        e.add_field(name='Current Location', value=fake_generator.local_latlng()[0:3])
        await interaction.response.send_message(embed=e)
