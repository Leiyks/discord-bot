import random
from discord.ext.commands import hybrid_command, Context, Cog

from discord_bot.main import Client


class Gambling(Cog):
    """
    This is the module doc
    """

    @hybrid_command()  # type: ignore
    async def coinflip(self, context: Context):
        """
        Coinflip help message
        """
        choice = random.choice(["head", "tail"])
        await context.reply(f"```It's {choice} !```")

    @hybrid_command()  # type: ignore
    async def random(self, context: Context, min: int, max: int):
        """
        Random help message
        """
        if min >= max:
            await context.reply("```First number must be lower that the second !```")
            return

        choice = random.randint(min, max)
        await context.reply(f"```You got '{choice}' !```")


async def setup(client: Client):
    await client.add_cog(Gambling())
