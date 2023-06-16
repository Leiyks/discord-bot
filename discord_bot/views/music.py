from discord import ButtonStyle, Interaction
from discord.ext.commands import Context
from discord.ui import Button, View, button

from discord_bot.extensions import music


class PlayView(View):
    """
    Handle the interactivity of the help command.
    """

    music_cog: "music.Music"
    context: Context

    def __init__(self, music: "music.Music", context: Context, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.music_cog = music
        self.context = context

    @button(style=ButtonStyle.red, row=0, label="⏹")
    async def previous(self, interaction: Interaction, button: Button):
        await interaction.response.defer()
        await self.music_cog.clear(self.context)

    @button(style=ButtonStyle.grey, row=0, label="⏸")
    async def pause(self, interaction: Interaction, button: Button):
        if self.music_cog.voice_channel is None:
            await interaction.response.defer()
            return

        if self.music_cog.voice_channel.is_paused():
            await self.music_cog.resume(self.context)
        else:
            await self.music_cog.pause(self.context)

        await interaction.response.edit_message(view=self)

    @button(style=ButtonStyle.grey, row=0, label="⏭")
    async def next(self, interaction: Interaction, button: Button):
        await interaction.response.defer()
        await self.music_cog.skip(self.context)
