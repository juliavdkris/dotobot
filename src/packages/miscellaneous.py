# -------------------------> Dependencies

# Setup python logging
import logging
log = logging.getLogger(__name__)

# Import libraries
import discord
from discord.ext import commands

# -------------------------> Client


def setup(bot):
	bot.add_cog(Miscellaneous(bot))


class Miscellaneous(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command()
	async def ping(self, ctx):
		log.info(f'Recieved ping command from user {ctx.author.name}')
		await ctx.send('Pong!')

	@commands.command()
	async def dump(self, ctx, *, arg=''):
		if 'log' in arg:
			with open('discord.log', 'br') as f:
				await ctx.send(file=discord.File(f, 'discord.log'))
				return
		elif 'roles' in arg:
			with open('storage/roles.json', 'br') as f:
				await ctx.send(file=discord.File(f, 'roles.json'))
				return
		else:
			with open('storage/quotes.json', 'br') as f:
				await ctx.send(file=discord.File(f, 'quotes.json'))
				return