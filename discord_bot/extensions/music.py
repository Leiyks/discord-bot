import asyncio
import os
import ctypes
from datetime import timedelta
from typing import List, Optional, Tuple

from discord import Color, Embed, Member, VoiceClient, VoiceState, opus
from discord.ext.commands import Cog, Context, hybrid_command

from discord_bot.main import MODULE_EMOJIS, Client, client
from discord_bot.utils.communication import send
from discord_bot.utils.youtube import YoutubeSource, YoutubeSourceInfo
from discord_bot.views.music import PlayView, QueueView, SearchView


OPUS_LIBRARY_PATH: str = os.environ.get("OPUS_LIBRARY_PATH", ctypes.util.find_library("opus"))
INACTIVITY_TIMEOUT: int = 600
INACTIVITY_WAIT_INTERVAL: int = 30


class Music(Cog):
    """
    Control the musics played by the bot.
    """

    music_queue: List[Tuple[YoutubeSourceInfo, Context]] = []
    voice_channel: Optional[VoiceClient] = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        opus.load_opus(OPUS_LIBRARY_PATH)

    ### EMBEDS ###

    def get_embed(self, context: Context, title: str, content: str, is_error: bool = False, prefix=True) -> Embed:
        """
        Get a basic embed object with proper format.

        Args:
            context (Context): Context of the command.
            title (str): Command title.
            content (str): response content.
            is_error (bool): if the response is an error.
            prefix (bool): Add prefix that mention user.

        Returns:
            embed (Embed): Embed object.
        """
        title = f"{MODULE_EMOJIS['Music']} Music - {title}"
        color: Color = Color.teal() if not is_error else Color.dark_red()
        description: str = f"{context.author.mention} {content}" if prefix else content
        return Embed(title=title, color=color, description=description)

    def get_songs_embed(
        self, context: Context, songs: List[YoutubeSourceInfo], title: str, content: str, offset: int = 0
    ) -> Embed:
        """
        Get an embed object with a description of all songs.

        Args:
            context (Context): Context of the command.
            songs (List[YoutubeSource]): List of songs.
            title (str): Command title.
            content (str): response content.

        Returns:
            embed (Embed): Embed object.
        """
        track_names: str = ""
        track_durations: str = ""

        for index, song in enumerate(songs):
            padding: str = " " if index + offset + 1 < 10 else ""
            track_name: str = f"`#{index + offset + 1}`{padding} - `{song.title}`\n"

            if len(track_name) >= 45:
                track_name = f"{track_name[:41]}...`\n"

            track_names += track_name
            track_durations += f"`{timedelta(seconds=song.duration)}`\n"

        plurial: str = "s" if len(self.music_queue) > 1 else ""
        embed: Embed

        if not offset:
            embed = self.get_embed(context, title if not offset else "", content if not offset else "")
        else:
            embed = Embed(color=Color.teal())
        return embed.add_field(name=f"Track{plurial}:", inline=True, value=track_names).add_field(
            name=f"Duration{plurial}:", inline=True, value=track_durations
        )

    def get_songs_embeds(
        self, context: Context, songs: List[YoutubeSourceInfo], title: str, content: str
    ) -> List[Embed]:
        """
        Get a list of embed object with a description of all songs.

        Args:
            context (Context): Context of the command.
            songs (List[YoutubeSource]): List of songs.
            title (str): Command title.
            content (str): response content.

        Returns:
            embed (Embed): Embed object.
        """
        return [self.get_songs_embed(context, songs[i : i + 20], title, content, i) for i in range(0, len(songs), 20)]

    ### RESPONSE ###

    async def send_response(self, context: Context, title: str, content: str, is_error: bool = False):
        """
        Send an embed response with proper format. (asynchronous)

        Args:
            context (Context): Context of the command.
            title (str): Command title.
            content (str): response content.
            is_error (bool): if the response is an error.
        """
        embed: Embed = self.get_embed(context, title, content, is_error)
        await send(context, embed=embed)

    async def send_add_response(self, context: Context, songs: List[YoutubeSourceInfo]):
        """
        Send an embed response for the `add` command.

        Args:
            context (Context): Context of the command.
            songs (List[YoutubeSource]): List of songs added.
        """
        plurial: str = "s" if len(songs) > 1 else ""
        embeds: List[Embed] = self.get_songs_embeds(
            context, songs, "Add", f"`Added` {len(songs)} song{plurial} to the queue !"
        )
        await send(context, embeds=embeds)

    async def send_queue_response(self, context: Context):
        """
        Send an embed response for the `add` command.

        Args:
            context (Context): Context of the command.
            songs (List[YoutubeSource]): List of songs added.
        """
        songs: List[YoutubeSourceInfo] = [song for song, _ in self.music_queue[0:20]]
        embeds: List[Embed] = self.get_songs_embeds(context, songs, "Queue", f"`Display` first 20 songs in the queue !")
        view: QueueView = QueueView(self, context)
        await send(context, embeds=embeds, view=view)

    async def send_play_response(self, context: Context, song: YoutubeSourceInfo):
        """
        Send an embed response for the `play` command.

        Args:
            context (Context): Context of the command.
            songs (YoutubeSource): Song playing.
        """
        embed: Embed = (
            self.get_embed(context, "Play", f"`Playing` next song in queue !", prefix=False)
            .add_field(name="Track:", inline=True, value=f"`{song.title}`")
            .add_field(name="Requested By:", inline=True, value=context.author.mention)
            .add_field(name="Duration:", inline=True, value=f"`{timedelta(seconds=song.duration)}`")
            .set_thumbnail(url=song.thumbnail)
        )

        view: PlayView = PlayView(self, context)
        await context.channel.send(embed=embed, view=view)

    async def send_search_response(self, context: Context, query: str, songs: List[YoutubeSourceInfo]):
        """
        Send an embed response for the `search` command.

        Args:
            context (Context): Context of the command.
            songs (List[YoutubeSource]): List of songs added.
        """
        embed: Embed = self.get_songs_embed(context, songs, "Search", f"`Search` results for `{query}` !")
        view: SearchView = SearchView(self, context, songs)
        await send(context, embed=embed, view=view)

    ### LISTENERS ###

    @Cog.listener()
    async def on_voice_state_update(self, member: Member, before: VoiceState, after: VoiceState):
        f"""
        Listener function used to disconnect the bot after a {INACTIVITY_TIMEOUT} min period of inactivity.
        (asynchronous)

        Args:
            member (Member): Member that updated his voice state.
            before (VoiceState): Member's voice state before the update.
            after (VoiceState): Member's voice state after the update.
        """
        if not client.user or member.id != client.user.id:
            return

        if before.channel or not after.channel:
            self.music_queue = []
            return

        assert after.channel.guild is not None
        assert after.channel.guild.voice_client is not None

        time: int = INACTIVITY_WAIT_INTERVAL

        await asyncio.sleep(INACTIVITY_WAIT_INTERVAL)

        while self.voice_channel is not None and self.voice_channel.is_connected():
            await asyncio.sleep(INACTIVITY_WAIT_INTERVAL)

            if not self.voice_channel.is_playing() and not self.music_queue:
                time += INACTIVITY_WAIT_INTERVAL
            else:
                time = 0

            if time == INACTIVITY_TIMEOUT:
                await self.voice_channel.disconnect(force=True)

    ### COMMANDS ###

    async def connect(self, context: Context):
        """
        Make the Bot join the user channel.
        """
        assert context.guild is not None

        member: Optional[Member] = context.guild.get_member(context.author.id)

        if member is None or member.voice is None or member.voice.channel is None:
            await self.send_response(context, "Connect", "You need to be `connected` to a channel !", True)
            return

        channel = member.voice.channel

        if self.voice_channel and self.voice_channel.is_connected() and self.voice_channel.channel == channel:
            return
        elif self.voice_channel is None or not self.voice_channel.is_connected():
            try:
                self.voice_channel = await member.voice.channel.connect()
            except asyncio.TimeoutError:
                await self.send_response(context, "Connect", f"Failed to `connect` to the {channel} channel !", True)
        else:
            await self.voice_channel.move_to(member.voice.channel)

        await self.send_response(context, "Connect", f"`Connected` the Bot to the {channel} channel !")

    @hybrid_command()  # type: ignore
    async def disconnect(self, context: Context):
        """
        Disconnect the Bot from any discord channel of the server.
        """
        if context.interaction and not context.interaction.response.is_done():
            await context.interaction.response.defer()

        if not self.voice_channel:
            await self.send_response(context, "Disconnect", "The bot is not connected to a channel ...", True)
            return

        await self.voice_channel.disconnect()
        await self.send_response(context, "Disconnect", "`Disconnected` the bot !")

    async def play_music(self):
        """
        Get the next music in the queue and play it.
        """
        if not self.music_queue or not self.voice_channel:
            return

        context: Context
        info: YoutubeSourceInfo
        info, context = self.music_queue.pop(0)

        source: Optional[YoutubeSource] = await info.prepare()

        if source:
            client.loop.create_task(self.send_play_response(context, info))
            self.voice_channel.play(
                source,
                after=lambda e: asyncio.run_coroutine_threadsafe(self.play_music(), client.loop)
                if not e
                else print(f"Error: {e}"),
            )
        else:
            asyncio.run_coroutine_threadsafe(self.play_music(), client.loop)

    @hybrid_command()  # type: ignore
    async def play(self, context: Context, query: Optional[str]):
        """
        Play a song or a playlist, can be used with keyword and URLs.
        """
        if context.interaction and not context.interaction.response.is_done():
            await context.interaction.response.defer()

        await self.connect(context)
        if not self.voice_channel:
            return

        if not query:
            if not self.voice_channel.is_playing() and self.music_queue:
                self.voice_channel.resume()
                await self.send_response(context, "Play", "`Resumed` the music !")
            elif self.music_queue:
                await self.send_response(context, "Play", "The queue is empty ...")
            else:
                await self.send_response(context, "Play", "The music is already playing ...")
            return

        await context.invoke(client.get_command("add"), query=query)  # type: ignore

        if not self.voice_channel.is_playing() and not self.voice_channel.is_paused():
            asyncio.run_coroutine_threadsafe(self.play_music(), client.loop)

    @hybrid_command()  # type: ignore
    async def add(self, context: Context, query: str):
        """
        Add a song or a playlist to the queue, can be used with keyword and URLs.
        """
        if context.interaction and not context.interaction.response.is_done():
            await context.interaction.response.defer()

        songs: List[YoutubeSourceInfo] = await YoutubeSourceInfo.search(query)

        if not songs:
            await self.send_response(context, "Add", "Could not find the song(s) ... Try other keywords / URLs.", True)
            return

        self.music_queue.extend([(song, context) for song in songs])
        await self.send_add_response(context, songs)

    @hybrid_command()  # type: ignore
    async def search(self, context: Context, query: str):
        """
        Search for a song and display the 10 first found results.
        """
        if context.interaction and not context.interaction.response.is_done():
            await context.interaction.response.defer()

        songs: List[YoutubeSourceInfo] = await YoutubeSourceInfo.search(query, search=True)

        if not songs:
            await self.send_response(context, "Search", "Could not find any song ... Try other keywords / URLs.", True)
            return

        await self.send_search_response(context, query, songs)

    @hybrid_command()  # type: ignore
    async def pause(self, context: Context):
        """
        Put the current song in pause.
        """
        if context.interaction and not context.interaction.response.is_done():
            await context.interaction.response.defer()

        if not self.voice_channel or self.voice_channel.is_paused():
            await self.send_response(context, "Pause", "The bot is not currently playing a song ...", True)
            return

        self.voice_channel.pause()
        await self.send_response(context, "Pause", "`Paused` the bot !")

    @hybrid_command()  # type: ignore
    async def resume(self, context: Context):
        """
        Resume the current song.
        """
        if context.interaction and not context.interaction.response.is_done():
            await context.interaction.response.defer()

        if not self.voice_channel or self.voice_channel.is_playing():
            await self.send_response(context, "Resume", "The bot is currently playing a song ...", True)
            return

        self.voice_channel.resume()
        await self.send_response(context, "Resume", "`Resumed` the bot !")

    @hybrid_command()  # type: ignore
    async def skip(self, context: Context):
        """
        Skip the current song.
        """
        if context.interaction and not context.interaction.response.is_done():
            await context.interaction.response.defer()

        if not self.voice_channel or not self.voice_channel.is_connected():
            await self.send_response(context, "Skip", "The bot is currently not connected ...", True)
            return

        await self.send_response(context, "Skip", "`Skipped` the song !")
        self.voice_channel.stop()

    @hybrid_command()  # type: ignore
    async def clear(self, context: Context):
        """
        Clear the music queue.
        """
        if context.interaction and not context.interaction.response.is_done():
            await context.interaction.response.defer()

        if not self.voice_channel or not self.voice_channel.is_connected():
            await self.send_response(context, "Clear", "The bot is currently not connected ...", True)
            return

        if self.voice_channel.is_playing():
            self.voice_channel.stop()

        self.music_queue = []
        await self.send_response(context, "Clear", "`Cleared` the queue !")

    @hybrid_command()  # type: ignore
    async def queue(self, context: Context):
        """
        Display the current music queue.
        """
        if context.interaction and not context.interaction.response.is_done():
            await context.interaction.response.defer()

        if not self.voice_channel or not self.voice_channel.is_connected():
            await self.send_response(context, "Queue", "The bot is currently not connected ...", True)
            return

        if not self.music_queue:
            await self.send_response(context, "Queue", "The queue is empty ...")
            return

        await self.send_queue_response(context)


async def setup(client: Client):
    await client.add_cog(Music())
