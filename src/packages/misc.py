import asyncio
import logging
from os.path import basename
from random import choice
from typing import List

import discord
from discord.colour import Colour
from discord.ext import commands

# -------------------------> Main

log = logging.getLogger(__name__)

def setup(bot: commands.Bot) -> None:
	bot.add_cog(Miscellaneous(bot))
	log.info(f'Module has been activated: {basename(__file__)}')

def teardown(bot: commands.Bot) -> None:
	log.info(f'Module has been de-activated: {basename(__file__)}')

async def delete_category(category: discord.CategoryChannel) -> None:
	for channel in category.channels:
		try:
			await channel.delete()
		except:
			log.warning(f'Failed to delete a speeddating VC in {category.guild.name}')
	await category.delete()

def is_member_in_vc(user: discord.Member) -> bool:
	try:
		user.voice
		return True
	except:
		return False

async def move_all(users: List[discord.Member], voice_channel: discord.VoiceChannel) -> None:
	for user in users:
		try:
			await user.move_to(voice_channel)
		except:
			pass

def parse_validVC_mentions_from_ctx(ctx: commands.Context) -> List[discord.Member]:
	users = [role.members for role in ctx.message.role_mentions]
	users.append(ctx.message.mentions)
	users += [[ctx.author]]
	users = list(set(sum(users, [])))
	if len(users) == 1:
		try:
			users = ctx.author.voice.channel.members
		except:
			pass
	users = [user for user in users if is_member_in_vc(user)]
	return users

# https://stackoverflow.com/questions/6648512/scheduling-algorithm-for-a-round-robin-tournament
def roundrobin(users: List) -> List:
	if len(users) % 2 == 1:
		users.append(None)
	rounds = []
	one = users.pop(0)
	for _ in range(len(users)):
		top_row = [one] + users[:len(users)//2]
		bot_row = users[::-1][:1 + len(users)//2]
		rounds.append([(top_row[i], bot_row[i]) for i in range(len(bot_row))])
		users.insert(0,users.pop())
	return rounds

async def speed_date_roullete(rounds: List, channel: discord.TextChannel, category: discord.CategoryChannel, users: List, lounge: discord.VoiceChannel) -> None:
	for turn in rounds:
		currentVC = 1  # lounge is at 0
		for pair in turn:
			if None in pair:
				continue
			for user in pair:
				try:
					await user.move_to(category.voice_channels[currentVC])
				except:
					await channel.send(embed=discord.Embed(title='⛔ Failed to move {user.name} into their speed-date', colour=Colour.from_rgb(0,0,0)))
			currentVC += 1

		await asyncio.sleep(5)
		await move_all(users, lounge)
		await asyncio.sleep(5)

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
		log.debug(f'Received ping command from user {ctx.author.name}')
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

	@commands.command(brief='Call for a speeddating session', description='Call for a speeddating session by tagging members who are in a VC', usage='[@friend, @role] / current vc')
	@commands.has_permissions(administrator=True)
	async def speeddate(self, ctx: commands.Context):
		users = parse_validVC_mentions_from_ctx(ctx)
		if len(users) == 1:
			await ctx.send(embed=discord.Embed(title='⛔ Not enough valid users', colour=Colour.from_rgb(0,0,0), description='Make sure you are either in a voice channel with more than 1 person.\nOr make sure to ping enough people who are currently in a voice channel.'))
		original_voice_state = {user.id: user.voice.channel for user in users}

		# setting up the necessary channels
		category = await ctx.guild.create_category     (name='Speed-dating', overwrites={ctx.guild.default_role: discord.PermissionOverwrite(connect = False)})
		Tchannel = await category. create_text_channel (name='Speed-dating')
		VClounge = await category. create_voice_channel(name='The-Lounge')
		for i in range(len(users)//2):
			await category.create_voice_channel(name=f'Date: {i+1}')

		# trigger speed-dating scheduler
		rounds = roundrobin(list(users))
		print(rounds)
		print(users)
		await speed_date_roullete(rounds, Tchannel, category, users, VClounge)

		# move all users back to their original voice channels and clean-up
		for user in users:
			try:
				await user.move_to(original_voice_state[user.id])
			except AttributeError:
				pass

		await Tchannel.send(f'This channel and all accompanying channels will be deleted in 5 seconds')  # TODO bigger number here
		await asyncio.sleep(5)
		await delete_category(category)
