import asyncio
import os
from typing import Any, Dict, List, Optional

from discord import Color, Embed, FFmpegPCMAudio, Member, PCMVolumeTransformer, VoiceClient, VoiceState, opus
from discord.ext.commands import Cog, Context, hybrid_command
from yt_dlp import YoutubeDL

from discord_bot.main import MODULE_EMOJIS, Client, client
from discord_bot.utils.communication import send

OPUS_LIBRARY_PATH: str = os.environ["OPUS_LIBRARY_PATH"]
INACTIVITY_TIMEOUT: int = 600
INACTIVITY_WAIT_INTERVAL: int = 30


class YoutubeSource(PCMVolumeTransformer):
    youtube_options: Dict = {
        "format": "best[ext=mp4]",
        "default_search": "auto",
        "ratelimit": 5000000,
        "outtmpl": "/tmp/%(title)s [%(id)s].%(ext)s",
        "ignoreerrors": True,
        "abort_on_available_fragments": True,
        "quiet": True,
    }

    ffmpeg_options: Dict = {
        "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 24",
    }

    youtube: YoutubeDL = YoutubeDL(youtube_options)

    data: Dict
    title: str
    url: str

    def __init__(self, source: FFmpegPCMAudio, data: Dict, volume: float = 0.5, *args, **kwargs):
        super().__init__(source, volume, *args, **kwargs)
        self.data = data
        self.title = data["title"]
        self.url = data["url"]

    @classmethod
    async def search(cls, query: str) -> List["YoutubeSource"]:
        if not query.startswith("https://www.youtube.com/"):
            query = f"ytsearch:{query}"

        data: Any = await client.loop.run_in_executor(None, lambda: cls.youtube.extract_info(query, download=False))

        if data is None:
            return []

        if query.startswith("https://www.youtube.com/playlist"):
            data = data["entries"]
        else:
            data = [data["entries"][0]]

        return [
            cls(FFmpegPCMAudio(entry["url"], **cls.ffmpeg_options), data=entry) for entry in data if entry is not None
        ]


class Music(Cog):
    music_queue: List[YoutubeSource] = []
    voice_channel: Optional[VoiceClient] = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        opus.load_opus(OPUS_LIBRARY_PATH)

    async def send_response(self, context: Context, title: str, content: str, is_error: bool = False):
        """
        Send an embed response with proper format. (asynchronous)

        Args:
            context (Context): Context of the command.
            title (str): Command title.
            content (str): response content.
            is_error (bool): if the response is an error.
        """
        user = context.author.mention
        title = f"{MODULE_EMOJIS['Music']} Music - {title}"
        color: Color = Color.teal() if not is_error else Color.dark_red()
        embed: Embed = Embed(title=title, color=color, description=f"{user} {content}")
        await send(context, embed=embed)

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

    @hybrid_command()  # type: ignore
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

        if self.voice_channel is None or not self.voice_channel.is_connected():
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
        Play a song or a playlist from Youtube. Can be used with keyword or URLs.
        """
        assert context.interaction is not None
        await context.interaction.response.defer()

        await self.connect(context)
        assert self.voice_channel is not None

        if not query:
            if not self.voice_channel.is_playing() and self.music_queue:
                self.voice_channel.resume()
                await self.send_response(context, "Play", "`Resumed` the music !")
            else:
                await self.send_response(context, "Play", "The music is already playing ...")
            return

        songs: List[YoutubeSource] = await YoutubeSource.search(query)

        if not songs:
            await self.send_response(context, "Play", "Could not find the song(s) ... Try other keywords / URLs.", True)
            return

        self.music_queue.extend(songs)
        # TODO: Add embeded response here
        await self.send_response(context, "Play", f"`Added` {len(songs)} songs to the queue !")

        if not self.voice_channel.is_playing() and not self.voice_channel.is_paused():
            self.play_music()

    @hybrid_command()  # type: ignore
    async def add(self, context: Context, query: str):
        """
        Add a song or a playlist from Youtube to the queue. Can be used with keyword or URLs.
        """
        assert context.interaction is not None
        await context.interaction.response.defer()

        songs: List[YoutubeSource] = await YoutubeSource.search(query)

        if not songs:
            await self.send_response(context, "Add", "Could not find the song(s) ... Try other keywords / URLs.", True)
            return

        self.music_queue.extend(songs)
        await self.send_response(context, "Add", f"`Added` {len(songs)} songs to the queue !")

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
        assert context.interaction is not None
        await context.interaction.response.defer()

        if not self.voice_channel or not self.voice_channel.is_connected():
            await self.send_response(context, "Skip", "The bot is currently not connected ...", True)
            return

        await self.send_response(context, "Skip", "`Skipped` the song !")
        self.voice_channel.stop()

    @hybrid_command()  # type: ignore
    async def clear(self, context: Context):
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
