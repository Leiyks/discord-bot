import random
import names
from datetime import time
from typing import Optional

import discord
from discord import Color, Embed, Guild, Member
from discord.ext import tasks
from discord.ext.commands import Cog, Context, hybrid_command

from discord_bot.main import MODULE_EMOJIS, Client, client
from discord_bot.utils.communication import send

MAIN_SERVER_ID: int = 472843363478142977
TOM_ID: int = 378640664734466058


class Gambling(Cog):
    """
    Collection of gambling commands.
    """

    def __init__(self):
        self.rename_tom.start()

    async def send_response(self, context: Context, title: str, content: str, is_error: bool = False):
        """
        Send an embed response with proper format. (asynchronous)

        Args:
            context (Context): Context of the command.
            title (str): Command title.
            content (str): response content.
            is_error (bool): if the response is an error.
        """
        title = f"{MODULE_EMOJIS['Gambling']} Gambling - {title}"
        color: Color = discord.Color.teal() if not is_error else discord.Color.dark_red()
        embed: Embed = discord.Embed(title=title, color=color, description=content)
        await send(context, embed=embed)

    @hybrid_command()  # type: ignore
    async def coinflip(self, context: Context):
        """
        Flip a coin and tell if it tails or heads.
        """
        assert context.interaction is not None
        await context.interaction.response.defer()

        content: str = f"Flipping a coin 🪙 ...\n\nIt's `{random.choice(['Head', 'Tail'])}` !"

        await self.send_response(context, "Coinflip", content)

    @hybrid_command()  # type: ignore
    async def random(self, context: Context, min: int, max: int):
        """
        Give a random number between the two numbers given as parameters.
        """
        assert context.interaction is not None
        await context.interaction.response.defer()

        content: str

        if min >= max:
            content = "The first number should be `inferior` to the second one !"
        else:
            content = f"The picked number is `{random.randint(min, max)}` !"

        content = f"Picking a random number between `{min}` and `{max}` ...\n\n{content}"

        await self.send_response(context, "Random", content, min >= max)

    @tasks.loop(time=time(hour=8))
    async def rename_tom(self):
        guild: Optional[Guild] = client.get_guild(MAIN_SERVER_ID)
        if not guild:
            return

        member: Optional[Member] = guild.get_member(TOM_ID)
        if not member:
            return

        await member.edit(nick=names.get_first_name(gender="male"))


async def setup(client: Client):
    await client.add_cog(Gambling())
