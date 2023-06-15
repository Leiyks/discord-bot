import asyncio
import os
from datetime import timedelta
from typing import List, Optional

from discord import Color, Embed, Member, VoiceClient, VoiceState, opus
from discord.ext.commands import Cog, Context, hybrid_command

from discord_bot.main import MODULE_EMOJIS, Client, client
from discord_bot.utils.communication import send
from discord_bot.utils.youtube import YoutubeSource

OPUS_LIBRARY_PATH: str = os.environ["OPUS_LIBRARY_PATH"]
INACTIVITY_TIMEOUT: int = 600
INACTIVITY_WAIT_INTERVAL: int = 30


class Music(Cog):
    """
    Control the musics played by the bot.
    """

    music_queue: List[YoutubeSource] = []
    voice_channel: Optional[VoiceClient] = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        opus.load_opus(OPUS_LIBRARY_PATH)

    ### BASIC RESPONSES ###

    def get_embed(self, context: Context, title: str, content: str, is_error: bool = False) -> Embed:
        """
        Send an embed response with proper format. (asynchronous)

        Args:
            context (Context): Context of the command.
            title (str): Command title.
            content (str): response content.
            is_error (bool): if the response is an error.
        """
        title = f"{MODULE_EMOJIS['Music']} Music - {title}"
        color: Color = Color.teal() if not is_error else Color.dark_red()
        description: str = f"{context.author.mention} {content}"
        return Embed(title=title, color=color, description=description)

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

    async def send_add_response(self, context: Context, songs: List[YoutubeSource]):
        """
        Send an embed response for the `add` command.

        Args:
            context (Context): Context of the command.
            songs (List[YoutubeSource]): List of songs added.
        """
        track_names: str = ""
        track_durations: str = ""

        for index, song in enumerate(songs):
            track_name: str = f"`#{index + 1}` - `{song.title}`\n"
            if len(track_name) >= 45:
                track_name = track_name[:41] + "...`\n"
            track_names += track_name
            track_durations += f"`{timedelta(seconds=song.duration)}`\n"

        plurial: str = "s" if len(songs) > 1 else ""
        embed: Embed = (
            self.get_embed(context, "Add", f"`Added` {len(songs)} song{plurial} to the queue !")
            .add_field(name=f"Track{plurial} Queued:", inline=True, value=track_names)
            .add_field(name=f"Duration{plurial}:", inline=True, value=track_durations)
            .set_thumbnail(url=songs[0].thumbnail)
        )

        await send(context, embed=embed)

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
        assert client.user is not None

        if member.id != client.user.id or before.channel or not after.channel:
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
        assert context.interaction is not None
        await context.interaction.response.defer()

        if not self.voice_channel:
            await self.send_response(context, "Disconnect", "The bot is not connected to a channel ...", True)
            return

        await self.voice_channel.disconnect()
        await self.send_response(context, "Disconnect", "`Disconnected` the bot !")

    def play_music(self):
        """
        Get the next music in the queue and play it.
        """
        assert self.voice_channel is not None

        if not self.music_queue:
            return

        source: YoutubeSource = self.music_queue.pop(0)
        self.voice_channel.play(
            source, after=lambda e: self.play_music() if not e else print(f"Error while playing song: {e}")
        )

    @hybrid_command()  # type: ignore
    async def play(self, context: Context, query: Optional[str]):
        """
        Play a song or a playlist, can be used with keyword and URLs.
        """
        assert context.interaction is not None
        await context.interaction.response.defer()

        await self.connect(context)
        if not self.voice_channel:
            return

        if not query:
            if not self.voice_channel.is_playing() and self.music_queue:
                self.voice_channel.resume()
                await self.send_response(context, "Play", "`Resumed` the music !")
            else:
                await self.send_response(context, "Play", "The music is already playing ...")
            return

        await context.invoke(client.get_command("add"), query=query)  # type: ignore

        if not self.voice_channel.is_playing() and not self.voice_channel.is_paused():
            self.play_music()

    @hybrid_command()  # type: ignore
    async def add(self, context: Context, query: str):
        """
        Add a song or a playlist to the queue, can be used with keyword and URLs.
        """
        assert context.interaction is not None
        if not context.interaction.response.is_done():
            await context.interaction.response.defer()

        songs: List[YoutubeSource] = await YoutubeSource.search(query)

        if not songs:
            await self.send_response(context, "Add", "Could not find the song(s) ... Try other keywords / URLs.", True)
            return

        self.music_queue.extend(songs)
        await self.send_add_response(context, songs)

    @hybrid_command()  # type: ignore
    async def pause(self, context: Context):
        """
        Put the current song in pause.
        """
        assert context.interaction is not None
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
        assert context.interaction is not None
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
        assert context.interaction is not None
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
        assert context.interaction is not None
        await context.interaction.response.defer()

        if not self.voice_channel or not self.voice_channel.is_connected():
            await self.send_response(context, "Clear", "The bot is currently not connected ...", True)
            return

        if self.voice_channel.is_playing():
            self.voice_channel.stop()

        self.music_queue = []
        await self.send_response(context, "Clear", "`Cleared` the queue !")


async def setup(client: Client):
    await client.add_cog(Music())
