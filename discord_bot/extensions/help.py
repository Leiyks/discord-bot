from importlib import metadata

import discord
from discord.embeds import Embed
from discord.ext.commands import Cog, Context, hybrid_command

from discord_bot.main import MODULE_EMOJIS, Client, client
from discord_bot.utils.communication import send
from discord_bot.views.help import HelpView


class Help(Cog):
    """
    Display custom interactive help message.
    """

    @hybrid_command()  # type: ignore
    async def help(self, context: Context):
        """Display main help message that can be interacted with."""
        version: str = metadata.version("discord-bot")
        prefix: str = str(client.command_prefix)

        embed: Embed = (
            discord.Embed(title="Help Section", color=discord.Color.teal())
            .add_field(
                name="Availables Modules",
                inline=False,
                value="\n".join([f"{MODULE_EMOJIS[cog]} {cog}" for cog in client.cogs.keys()]),
            )
            .add_field(
                name="Notes",
                inline=False,
                value=f"- Every commands can also be used with the {prefix} prefix. Example: `{prefix}help`.",
            )
            .add_field(
                name="About",
                value=(
                    "This bot is developed and maintained by Leiyks, based on the `discord.py` library.\n"
                    "Please visit the `Github project page` below to submit ideas or bugs."
                ),
            )
            .set_footer(text=f"Bot running version: {version}")
        )

        view = HelpView()
        await send(context, embed=embed, view=view)


async def setup(client: Client):
    await client.add_cog(Help())
