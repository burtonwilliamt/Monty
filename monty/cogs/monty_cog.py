from collections.abc import Sequence
import datetime
import logging
import random
import re
from typing import Any
import zoneinfo

import discord
from discord import app_commands
import discord.ext.commands
import racket
from faker import Faker

from monty import money_db, loot, urban
from monty.cogs.text_options import BEG_OPTIONS

emoji_pattern = re.compile(r'<a?:.*:(\d+)>')

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
    async def behold(self, interaction: discord.Interaction,
                     thing_being_looked_at: str):
        """LOOK wonderingly at an emoji or something."""
        message = (f'{thing_being_looked_at.strip()}'
                   '<:bb1:855882629714018334>'
                   '<:bb2:855882629878120488>'
                   '\n'
                   '<:bb3:855882629844172800>'
                   '<:bb4:855882629731975198>'
                   '<:bb5:855882629761204284>')
        await interaction.response.send_message(message)

    @app_commands.command()
    async def fish_look(self,
                        interaction: discord.Interaction,
                        length: int = 3,
                        thing_being_looked_at: str = ''):
        """Long fish. Configurable neck and thingy.

        Args:
            length: How many neck peices you want. Defaults to 3.
            thing_being_looked_at: A thing to look at. Defaults to nothing.
        """
        message = (f'<:fish1:854133518204665876>'
                   f'{"<:fish2:854133921473495040>" * length}'
                   '<:fish3:854133518083162112>'
                   f'{thing_being_looked_at.strip()}')
        if len(message) > 2000:
            await interaction.response.send_message(
                'Woah. Discord can\'t handle that much fish. Try a smaller number.',
                ephemeral=True)
            return
        await interaction.response.send_message(message)

    @app_commands.command()
    async def urban(self, interaction: discord.Interaction, term: str):
        """Fetches a definition from urban dictionary.

        Args:
            term: The term to search for.
        """
        await urban.send_urban_dictionary_definition(interaction, term)

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
        age = today.year - bday.year - (
            (today.month, today.day) < (bday.month, bday.day))
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
        e.add_field(name='Current Location',
                    value=fake_generator.local_latlng()[0:3])
        await interaction.response.send_message(embed=e)

    @app_commands.command()
    async def inspect_emoji(self, interaction: discord.Interaction, emoji: str):
        """Get details about emoji."""
        #emoji_id = re.compile()
        match = emoji_pattern.match(emoji.strip())
        if match is None:
            await interaction.response.send_message(
                f'Unable to extract emoji id from `{emoji}`.')
            return

        the_emoji = interaction.client.get_emoji(int(match.group(1)))
        if the_emoji is None:
            await interaction.response.send_message(
                f'Unable to find emoji with id `{match.group(1)}`.')
            return

        e = discord.Embed(description=the_emoji.name)
        e.add_field(name='created at', value=the_emoji.created_at, inline=False)
        e.add_field(name='url', value=the_emoji.url, inline=False)
        await interaction.response.send_message(embed=e)

    @app_commands.command()
    async def schedule(self,
                       interaction: discord.Interaction,
                       event_name: str = None,
                       hours: int = 0,
                       minutes: int = 0,
                       seconds: float = 0.0):
        """Schedule an event and auto-translate timezones.
        
        Args:
            event_name: The thing you're inviting people to.
            hours: Hours in the future.
            minutes: Minutes in the future.
            seconds: Seconds in the future.
        """
        now = datetime.datetime.utcnow().astimezone(datetime.timezone.utc)
        the_time = now + datetime.timedelta(
            hours=hours, minutes=minutes, seconds=seconds)
        time_desc = []
        if hours != 0:
            time_desc.append(f'{hours} hours')
        if minutes != 0:
            time_desc.append(f'{minutes} minutes')
        if seconds != 0.0:
            time_desc.append(f'{seconds} seconds')

        if len(time_desc) >= 2:
            time_desc.insert(-1, 'and')
        if len(time_desc) == 0:
            time_desc.append('right fuckin now')

        def str_for_zone(name: str) -> str:
            return f'{the_time.astimezone(zoneinfo.ZoneInfo(name)).strftime("%I:%M %p %Z")}'

        await interaction.response.send_message(
            f'# `{event_name or "get on"}`\n'
            f'<t:{int(the_time.timestamp()//1.0)}:R>\n'
            f'`{str_for_zone("US/Pacific")}`\n'
            f'`{str_for_zone("US/Mountain")}`\n'
            f'`{str_for_zone("US/Central")}`\n'
            f'`{str_for_zone("US/Eastern")}`\n')

    @app_commands.command()
    async def loot(self, interaction: discord.Interaction,
                   box_type: loot.LootBoxType):
        await loot.create_lootbox_opener(interaction, self.money, box_type)
