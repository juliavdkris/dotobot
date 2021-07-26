# -------------------------> Dependencies

# Setup python logging
import logging
log = logging.getLogger(__name__)

# Import libraries
from discord.ext import commands
from os.path import basename
import random

# -------------------------> Main

def setup(bot: commands.Bot) -> None:
	bot.add_cog(Die(bot))
	log.info(f'Module has been activated: {basename(__file__)}')

def teardown(bot: commands.Bot) -> None:
	log.info(f'Module has been de-activated: {basename(__file__)}')

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