from discord.errors import Forbidden
from discord.ext.commands import Context


async def send(context: Context, *args, **kwargs):
    """Function to send a message safely.

    Args:
        context (Context): message context.
        embed (Embed): message embedding.

    Raises:
        discord.HTTPException
            Sending the message failed.
    """
    try:
        await context.send(*args, **kwargs)
    except Forbidden:
        await context.author.send(
            f"Hey, seems like I can't send any message in {context.channel} on {context.guild}\n"
            "May you inform the server team about this issue? :slight_smile:",
            *args,
            **kwargs,
        )
