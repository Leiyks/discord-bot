from typing import Dict
import discord
from discord.embeds import Embed
from discord.ext import commands
from discord.ext.commands import Context, hybrid_command

from importlib import metadata

from discord import SelectOption, Interaction, ButtonStyle
from discord.ui import View, select, Select, Button
from discord_bot.utils.communication import send
from importlib import metadata

from discord_bot.main import client, Client

MODULE_EMOJIS: Dict[str, str] = {"Gambling": "🎲", "Help": "🫴"}


class HelpView(View):
    """
    Handle the interactivity of the help command.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_item(
            Button(
                style=ButtonStyle.link,
                label="Github",
                url="https://github.com/Leiyks/discord-bot",
                emoji="<:github:1117230368215543828>",
            )
        )

    @select(
        placeholder="Pick a module !",
        options=[
            SelectOption(label=cog, emoji=MODULE_EMOJIS[cog], description=client.cogs[cog].__doc__)
            for cog in list(client.cogs.keys())
        ],
    )  # type: ignore
    async def help_module(self, interaction: Interaction, select: Select):
        """Display help message for a specific module of the bot."""
        await interaction.response.defer()

        value: str = select.values[0]

        embed: Embed = discord.Embed(
            title=f"{MODULE_EMOJIS[value]} {value} Commands",
            color=discord.Color.teal(),
            description="\n".join(
                [f"`{command.name}`: {command.help}" for command in client.cogs[value].get_commands()]
            ),
        )

        await interaction.followup.send(embed=embed, ephemeral=True)


class Help(commands.Cog):
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
