import random
from discord.ext.commands import hybrid_command, Context, Cog

from discord_bot.main import Client


class Gambling(Cog):
    """
    Commands collection of gambling commands.
    """

    @hybrid_command()  # type: ignore
    async def coinflip(self, context: Context):
        """
        Flip a coin and tell if it tails or heads.
        """
        choice = random.choice(["head", "tail"])
        await context.reply(f"```It's {choice} !```")

    @hybrid_command()  # type: ignore
    async def random(self, context: Context, min: int, max: int):
        """
        Give a random number between the two numbers given as parameters.
        """
        if min >= max:
            await context.reply("```First number must be lower that the second !```")
            return

        choice = random.randint(min, max)
        await context.reply(f"```You got '{choice}' !```")


async def setup(client: Client):
    await client.add_cog(Gambling())
