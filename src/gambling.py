import random
from discord.ext import commands


class Gambling(commands.Cog):
    @commands.command(
        help="You can pass any number of choices to the command !",
        brief="Choose a random value among all the given choices.",
    )
    async def choice(self, ctx, *args):
        if not args:
            await ctx.reply("```You need to give at least one choice !```")
            return
        choice = random.choice(args)
        await ctx.reply(f"```I choose '{choice}' ^^ !```")

    @commands.command(brief="Give the result of a coinflip.")
    async def coinflip(self, ctx):
        choice = random.choice(["head", "tail"])
        await ctx.reply(f"```It's {choice} !```")

    @commands.command(help="You must pass two number to the command !", brief="Choose a random number in a range.")
    async def rnd(self, ctx, min, max):
        if not min or not max:
            await ctx.reply("```You need to give two parameters !```")
        try:
            min = int(min)
            max = int(max)
        except Exception:
            await ctx.reply("```You must give two numbers !```")
        if min >= max:
            await ctx.reply("```First number must be lower that the second !```")
        else:
            choice = random.randint(min, max)
            await ctx.reply(f"```You got '{choice}' !```")


async def setup(bot):
    await bot.add_cog(Gambling())
