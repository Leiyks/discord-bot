import os
from discord.ext.commands import Bot
from typing import List

import discord


TOKEN: str = os.environ["TOKEN"]


class Client(Bot):
    _extensions: List[str] = ["extensions.gambling"]

    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())

    async def setup_hook(self):
        for extension in self._extensions:
            await self.load_extension(extension)

        async for guild in self.fetch_guilds():
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)


client = Client()


if __name__ == "__main__":
    Client().run(TOKEN)
