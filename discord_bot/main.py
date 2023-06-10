import os
from discord.ext.commands import Bot
from typing import Dict, List

import discord


TOKEN: str = os.environ["TOKEN"]
MODULE_EMOJIS: Dict[str, str] = {"Gambling": "🎲", "Help": "🫴"}


class Client(Bot):
    _extensions: List[str] = ["discord_bot.extensions.gambling", "discord_bot.extensions.help"]

    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())

    async def setup_hook(self):
        self.remove_command("help")

        for extension in self._extensions:
            await self.load_extension(extension)

        async for guild in self.fetch_guilds():
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)


client = Client()


def main():
    client.run(TOKEN)


if __name__ == "__main__":
    main()
