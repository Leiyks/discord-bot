from typing import Any, Dict, List, Optional

from discord import FFmpegPCMAudio, PCMVolumeTransformer
from yt_dlp import YoutubeDL, utils

from discord_bot.main import client


class YoutubeSourceInfo:
    youtube_options: Dict = {
        "default_search": "auto",
        "format": "bestaudio*/best",
        "ignoreerrors": True,
        "noplaylist": True,
        "outtmpl": "/tmp/%(title)s [%(id)s].%(ext)s",
        "quiet": True,
        "ratelimit": 5000000,
        "skip_download": True,
        "writeinfojson": True,
        "lazy_playlist": True,
        "match_filter": utils.match_filter_func("url!*=/shorts/"),
    }

    youtube: YoutubeDL = YoutubeDL({**youtube_options, **{"extract_flat": True}})

    data: Dict
    title: str
    url: str

    def __init__(self, data: Dict):
        self.data = data
        self.title = data["title"]
        self.url = data["url"]
        self.duration = data["duration"]
        self.thumbnail = data["thumbnails"][-1]["url"]

    async def prepare(self) -> Optional["YoutubeSource"]:
        return await YoutubeSource.prepare(self.url)

    @classmethod
    async def search(cls, query: str, search: bool = False) -> List["YoutubeSourceInfo"]:
        """
        Search for a youtube video by returning the first 10 found options.

        Args:
            query (str): The query or URL to search for.

        Returns:
            List[YoutubeSource]: A list of YoutubeSource objects.
        """
        if search:
            query = f"ytsearch10:{query}"
        elif not query.startswith("https://www.youtube.com/"):
            query = f"ytsearch:{query}"

        data: Any = await client.loop.run_in_executor(None, lambda: cls.youtube.extract_info(query, download=False))

        if data is None:
            return []

        if "entries" in data:
            data = data["entries"]

        if type(data) != list:
            data = [data]

        return [cls(data=entry) for entry in data if entry is not None]


class YoutubeSource(PCMVolumeTransformer):
    youtube_options: Dict = {
        "default_search": "auto",
        "format": "bestaudio*/best",
        "ignoreerrors": True,
        "noplaylist": True,
        "outtmpl": "/tmp/%(title)s [%(id)s].%(ext)s",
        "quiet": True,
        "ratelimit": 5000000,
        "skip_download": True,
        "writeinfojson": True,
        "match_filter": utils.match_filter_func("url!*=/shorts/"),
    }

    ffmpeg_options: Dict = {
        "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
        "options": "-vn",
    }

    youtube: YoutubeDL = YoutubeDL(youtube_options)

    def __init__(self, source, volume: float = 0.5, *args, **kwargs):
        super().__init__(source, volume, *args, **kwargs)

    @classmethod
    async def prepare(cls, url: str) -> Optional["YoutubeSource"]:
        data: Any = await client.loop.run_in_executor(None, lambda: cls.youtube.extract_info(url, download=False))

        if data is None or "url" not in data:
            return None

        source: FFmpegPCMAudio = FFmpegPCMAudio(data["url"], **cls.ffmpeg_options)
        return cls(source)
