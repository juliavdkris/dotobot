import logging
from os.path import basename
from random import choice

import discord
from discord.ext import commands

# -------------------------> Main

log = logging.getLogger(__name__)

def setup(bot: commands.Bot) -> None:
	bot.add_cog(Miscellaneous(bot))
	log.info(f'Module has been activated: {basename(__file__)}')

def teardown(bot: commands.Bot) -> None:
	log.info(f'Module has been de-activated: {basename(__file__)}')


class Miscellaneous(commands.Cog, name='Misc', description='Novelty functionality'):
	def __init__(self, bot: commands.Bot):
		self.bot = bot

	@commands.Cog.listener()
	async def on_ready(self) -> None:
		await self.set_activity(choice([
			"Error 418 I'm a teapot.",
			"Malicious bit set to true.",
			"Listening human music.",
			"Watching the whole MCU.",
			"Watching Netlix."]))

	@commands.command(brief='Ping the bot', description='Ping the bot', usage='')
	async def ping(self, ctx: commands.Context) -> None:
		log.info(f'Received ping command from user {ctx.author.name}')
		await ctx.send('Pong!')

	@commands.command(brief='Dump bot related data', description='Allows the duping of the `log` the `roles` or the local quote database, defaults to quotes', usage='log')
	@commands.has_permissions(administrator=True)
	async def dump(self, ctx: commands.Context, *, arg='') -> None:
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
	async def delete(self, ctx: commands.Context, amount: int = 97) -> None:
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
	async def activity(self, ctx: commands.Context, *arg) -> None:
		await self.set_activity(ctx.message.content[10:])

	async def set_activity(self, msg: str) -> None:
		command = msg.split()[0].lower()
		if command == 'listening':
			await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=msg[10:]))
		elif command == 'watching':
			await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=msg[9:]))
		else:
			await self.bot.change_presence(activity=discord.Game(name=msg))
