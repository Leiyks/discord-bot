from typing import List, Optional

from discord import ButtonStyle, Embed, Interaction, SelectOption
from discord.ext.commands import Context
from discord.ui import Button, Select, View, button

from discord_bot.extensions import music
from discord_bot.main import client
from discord_bot.utils.youtube import YoutubeSource


class PlayView(View):
    """
    Handle the interactivity of the `play` command.
    """

    music_cog: "music.Music"
    context: Context

    def __init__(self, music: "music.Music", context: Context, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.music_cog = music
        self.context = context

    @button(style=ButtonStyle.red, row=0, label="⏹")
    async def clear(self, interaction: Interaction, button: Button):
        """
        Call the `clear` method of the music cog.

        Args:
            interaction (Interaction): The interaction of the button.
            button (Button): The button itself.
        """
        await interaction.response.defer()
        await self.music_cog.clear(self.context)

    @button(style=ButtonStyle.grey, row=0, label="⏸")
    async def pause(self, interaction: Interaction, button: Button):
        """
        Call the `pause/resume` methods of the music cog.

        Args:
            interaction (Interaction): The interaction of the button.
            button (Button): The button itself.
        """
        if self.music_cog.voice_channel is None:
            await interaction.response.defer()
            return

        if self.music_cog.voice_channel.is_paused():
            await self.music_cog.resume(self.context)
            button.label = "⏸"
        else:
            await self.music_cog.pause(self.context)
            button.label = "▶️"

        await interaction.response.edit_message(view=self)

    @button(style=ButtonStyle.grey, row=0, label="⏭")
    async def next(self, interaction: Interaction, button: Button):
        """
        Call the `next` method of the music cog.

        Args:
            interaction (Interaction): The interaction of the button.
            button (Button): The button itself.
        """
        await interaction.response.defer()
        await self.music_cog.skip(self.context)


class QueueView(View):
    """
    Handle the interactivity of the `queue` command.
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
            """
            Callback of the select menu.
            Display all of the songs in the queue and remove the selected ones.

            Args:
                interaction (Interaction): The interaction of the menu.
            """
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


class SearchView(View):
    """
    Handle the interactivity of the `search` command.
    """

    class SearchSelect(Select):
        music_cog: "music.Music"
        context: Context

        def __init__(self, music_cog: "music.Music", context: Context, songs: List[YoutubeSource]):
            self.music_cog = music_cog
            self.context = context
            self.songs = songs

            options = [SelectOption(label=song.title, emoji="🎵") for song in songs]
            super().__init__(placeholder="Pick a song to add !", options=options)

        async def callback(self, interaction: Interaction):
            """
            Callback of the select menu.
            Display all of the songs found for the given query and add the select one to the queue.

            Args:
                interaction (Interaction): The interaction of the menu.
            """
            if interaction.response.is_done():
                await interaction.response.defer()

            song = [(song, self.context) for song in self.songs if song.title in self.values][0]
            self.music_cog.music_queue.append(song)
            await self.music_cog.send_add_response(self.context, [song[0]])

            if not self.music_cog.voice_channel:
                await self.music_cog.connect(self.context)

            assert self.music_cog.voice_channel is not None

            if not self.music_cog.voice_channel.is_playing() and not self.music_cog.voice_channel.is_paused():
                self.music_cog.play_music()

            embed = self.music_cog.get_embed(self.context, "Search", f"chose `{song[0].title}`.")
            await interaction.response.edit_message(embed=embed, view=None)

    def __init__(self, music_cog: "music.Music", context: Context, songs: List[YoutubeSource], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_item(self.SearchSelect(music_cog, context, songs))
