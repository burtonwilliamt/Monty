import racket

from monty.cogs import MontyCog
from settings import GUILD_IDS, BOT_TOKEN


def main():
    racket.run_cog(MontyCog, guilds=GUILD_IDS, token=BOT_TOKEN)


if __name__ == '__main__':
    main()