import os
import discord
from discord.ext.commands import Bot

TOKEN = os.environ.get("TOKEN")

client: Bot = Bot(command_prefix="!", intents=discord.Intents.all())


@client.event
async def on_ready():
    await client.load_extension("src.gambling")


if __name__ == "__main__":
    if not TOKEN:
        raise ValueError("TOKEN environment variable is not set")
    client.run(TOKEN)
