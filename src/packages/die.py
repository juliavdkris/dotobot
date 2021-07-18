# -------------------------> Dependencies

# Setup python logging
import logging
log = logging.getLogger(__name__)

# Import libraries
import discord
from discord.ext import commands
import random

# -------------------------> Client

def setup(bot):
	log.info('Die module has been activated')
	bot.add_cog(Die(bot))

def teardown(bot):
	log.info('Die module has been deactivated')

class Die(commands.Cog, name='RNG', description='Simulate dice throws'):
	def __init__(self, bot):
		self.bot = bot
		self.functions = {}

	@commands.command(brief='Roll a D6', description='Returns a dice with 1-6 eyes', usage='')
	async def roll(self,ctx):
		d6 = [
			'+-------+\n|       |\n|   o   |\n|       |\n+-------+',
			'+-------+\n| o     |\n|       |\n|     o |\n+-------+',
			'+-------+\n| o     |\n|   o   |\n|     o |\n+-------+',
			'+-------+\n| o   o |\n|       |\n| o   o |\n+-------+',
			'+-------+\n| o   o |\n|   o   |\n| o   o |\n+-------+',
			'+-------+\n| o   o |\n| o   o |\n| o   o |\n+-------+'
		]	
		output = f'```\n{random.choice(d6)}```'
		await ctx.send(output)

