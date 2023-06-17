from discord import ButtonStyle, Color, Interaction, SelectOption
from discord.embeds import Embed
from discord.ui import Button, Select, View, select

from discord_bot.main import MODULE_EMOJIS, client


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
    )
    async def help_module(self, interaction: Interaction, select: Select):
        """
        Display help message for a specific module of the bot.

        Args:
            interaction (Interaction): The interaction of the select menu.
            select (Select): The select object itself.
        """
        await interaction.response.defer()

        value: str = select.values[0]

        embed: Embed = Embed(
            title=f"{MODULE_EMOJIS[value]} {value} Commands",
            color=Color.teal(),
            description="\n".join(
                [f"`{command.name}`: {command.help}" for command in client.cogs[value].get_commands()]
            ),
        )

        await interaction.followup.send(embed=embed, ephemeral=True)
