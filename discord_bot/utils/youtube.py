from typing import Any, Dict, List

from discord import FFmpegPCMAudio, PCMVolumeTransformer
from yt_dlp import YoutubeDL

from discord_bot.main import client


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
        self.duration = data["duration"]
        self.thumbnail = data["thumbnail"]

    @classmethod
    async def search(cls, query: str) -> List["YoutubeSource"]:
        """
        Search for a youtube video by returning the first 10 found options.

        Args:
            query (str): The query or URL to search for.

        Returns:
            List[YoutubeSource]: A list of YoutubeSource objects.
        """
        data: Any = await client.loop.run_in_executor(
            None, lambda: cls.youtube.extract_info(f"ytsearch10:{query}", download=False)
        )

        if data is None:
            return []

        return [
            cls(FFmpegPCMAudio(entry["url"], **cls.ffmpeg_options), data=entry)
            for entry in data["entries"]
            if entry is not None
        ]

    @classmethod
    async def get_first_match(cls, query: str) -> List["YoutubeSource"]:
        """
        Search for a youtube video or playlist with the given query/URL.
        Return the first match if the query is not a playlist.

        Args:
            query (str): The query or URL to search for.

        Returns:
            List[YoutubeSource]: A list of YoutubeSource objects.
        """
        if not query.startswith("https://www.youtube.com/"):
            query = f"ytsearch:{query}"

        data: Any = await client.loop.run_in_executor(None, lambda: cls.youtube.extract_info(query, download=False))

        if data is None:
            return []

        if "entries" in data:
            data = data["entries"]

        if type(data) != list:
            data = [data]

        return [
            cls(FFmpegPCMAudio(entry["url"], **cls.ffmpeg_options), data=entry) for entry in data if entry is not None
        ]
