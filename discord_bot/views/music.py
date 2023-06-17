from typing import List, Optional

from discord import ButtonStyle, Embed, Interaction, SelectOption
from discord.ext.commands import Context
from discord.ui import Button, Select, View, button

from discord_bot.extensions import music
from discord_bot.utils.youtube import YoutubeSource


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


class QueueView(View):
    """
    Handle the interactivity of the help command.
    """

    class QueueSelect(Select):
        music_cog: "music.Music"
        context: Context

        def __init__(self, music_cog: "music.Music", context: Context):
            self.music_cog = music_cog
            self.context = context

            options = [SelectOption(label=song.title, emoji="🎵") for song, _ in self.music_cog.music_queue]
            super().__init__(placeholder="Pick a track to remove !", options=options)

        async def callback(self, interaction: Interaction):
            # Remove option from select
            for option in self.options:
                if option.value in self.values:
                    self.options.remove(option)

            # Remove song from queue
            for song in self.music_cog.music_queue:
                if song[0].title in self.values:
                    self.music_cog.music_queue.remove(song)

            songs: List[YoutubeSource] = [song for song, _ in self.music_cog.music_queue]
            view: Optional[View] = None if not self.options else self.view
            embed: Embed

            if not self.options:
                embed = self.music_cog.get_embed(self.context, "Queue", "The queue is empty ...")
            else:
                embed = self.music_cog.get_songs_embed(self.context, songs, "Queue", f"`Display` songs in the queue !")

            await interaction.response.edit_message(embed=embed, view=view)

    def __init__(self, music: "music.Music", context: Context, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_item(self.QueueSelect(music, context))
