import random
from discord.ext.commands import hybrid_command, Context, Cog

from discord import Color, Embed

import discord
from discord_bot.main import Client, MODULE_EMOJIS
from discord_bot.utils.communication import send


class Gambling(Cog):
    """
    Commands collection of gambling commands.
    """

    @hybrid_command()  # type: ignore
    async def coinflip(self, context: Context):
        """
        Flip a coin and tell if it tails or heads.
        """
        embed: Embed = discord.Embed(
            title=f"{MODULE_EMOJIS['Gambling']} Gambling - Coinflip",
            color=discord.Color.teal(),
            description=f"Flipping a coin 🪙 ...\n\nIt's `{random.choice(['Head', 'Tail'])}` !",
        )

        await send(context, embed=embed)

    @hybrid_command()  # type: ignore
    async def random(self, context: Context, min: int, max: int):
        """
        Give a random number between the two numbers given as parameters.
        """
        message: str
        color: Color

        if min >= max:
            message = "The first number should be `inferior` to the second one !"
            color = discord.Color.dark_red()
        else:
            message = f"The picked number is `{random.randint(min, max)}` !"
            color = discord.Color.teal()

        embed: Embed = discord.Embed(
            title=f"{MODULE_EMOJIS['Gambling']} Gambling - Random",
            color=color,
            description=f"Picking a random number between `{min}` and `{max}` ...\n\n{message}",
        )

        await send(context, embed=embed)


async def setup(client: Client):
    await client.add_cog(Gambling())
