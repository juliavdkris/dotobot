import discord
from discord.ext import commands

from os import getenv
from dotenv import load_dotenv



load_dotenv()
bot = commands.Bot(command_prefix=getenv('PREFIX'))


@bot.command()
async def ping(ctx):
	await ctx.send('pong')


print('Bot is running!')
bot.run(getenv('DISCORD_TOKEN'))