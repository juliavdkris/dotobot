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


class Miscellaneous(commands.Cog, name='Misc', description='Novelty functionality'):
	def __init__(self, bot):
		self.bot = bot

	@commands.command(brief='Ping the bot', description='Ping the bot', usage='')
	async def ping(self, ctx):
		log.info(f'Recieved ping command from user {ctx.author.name}')
		await ctx.send('Pong!')

	@commands.command(brief='Dump bot related data', description='Allows the duping of the `log` the `roles` or the local quote database, defaults to quotes', usage='log')
	@commands.has_permissions(administrator=True)
	async def dump(self, ctx, *, arg=''):
		if 'log' in arg:
			with open('storage/discord.log', 'br') as f:
				await ctx.send(file=discord.File(f, 'discord.log'))
				return
		elif 'roles' in arg:
			with open('storage/db/roles.json', 'br') as f:
				await ctx.send(file=discord.File(f, 'roles.json'))
				return
		else:
			with open(f'storage/db/quotes/{ctx.guild.id}.json', 'br') as f:
				await ctx.send(file=discord.File(f, 'quotes.json'))
				return

	@commands.command(brief='Delete x messages', description='Delete x messages with a max of 95', usage='5')
	@commands.has_permissions(administrator=True)
	async def delete(self, ctx, amount: int = 97):
		approval = ['yes', 'ja', 'ye', 'yea', 'yeah', 'y']
		if amount > 97:  # there is a hardcap at 100
			amount = 97
		amount += 1  # we have to delete the command call, the response and the approval as well.
		messagelist = []
		async for message in ctx.channel.history(limit=amount):
			messagelist.append(message)
		messagelist.append(await ctx.send(f'Are you sure you want to delete {amount - 1} messages?'))
		msg = await self.bot.wait_for('message', check=lambda message: message.author == ctx.author, timeout=20)
		if msg.content.split(' ')[0].lower() not in approval:
			return
		messagelist.append(msg)
		await ctx.channel.delete_messages(messagelist)

	@commands.command(brief='Set bot activity', description='Set bot playing, listening, or watching status ', usage='watching netflix')
	@commands.has_permissions(administrator=True)
	async def activity(self, ctx, *arg):
		if arg[0] == 'listening':
			await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=ctx.message.content[20:]))
		elif arg[0] == 'watching':
			await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=ctx.message.content[19:]))
		else:
			await self.bot.change_presence(activity=discord.Game(name=ctx.message.content[10:]))
