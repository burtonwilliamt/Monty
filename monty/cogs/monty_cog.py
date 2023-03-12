import logging

import discord
from discord import app_commands
import discord.ext.commands
from racket import RacketBot

_log = logging.getLogger(__name__)

class MontyCog(discord.ext.commands.Cog):
    """Collection of sound effects and the commands to use them."""

    def __init__(self, bot: RacketBot):
        self.bot = bot

    @app_commands.command()
    async def celery_man(self, interaction: discord.Interaction):
        """Computer bring up Celery Man."""
        await interaction.response.send_message('https://thumbs.gfycat.com/DampHandyGoosefish-small.gif')