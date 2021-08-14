import asyncio
import json
import logging
from copy import deepcopy
from os.path import basename

import discord
from discord import Colour
from discord.ext import commands

# -------------------------> Globals

# Setup environment
log = logging.getLogger(__name__)

# -------------------------> Functions

# Setup extension
def setup(bot: commands.Bot) -> None:
	bot.add_cog(Homicide(bot))
	log.info(f'Extension has been activated: {basename(__file__)}')

# Teardown extension
def teardown(bot: commands.Bot) -> None:
	log.info(f'Extension has been deactivated: {basename(__file__)}')

# -------------------------> Cogs

# Homicide cog
class Homicide(commands.Cog, name='Tempban', description='Tempban users via vote or command'):
	def __init__(self, bot: commands.Bot):
		self.bot = bot
		self.config = self.load_config()

	# Dumps config into memory
	def load_config(self) -> None:
		log.debug(f'config/homicide.json has been loaded')
		with open('storage/config/homicide.json', 'r', encoding='utf-8') as file:
			return json.load(file)

	# Returns user info when user joins the guild
	def on_join_helper(self, guild_id: int, member_id: int) -> None:
		with open('storage/db/roles.json', 'r+', encoding='utf-8') as file:
			roles = json.load(file)
			if not guild_id in roles or not member_id in roles[guild_id]:  # if we don't know this user skip the function
				return (False, {})
			result = (True, deepcopy(roles[guild_id][member_id]))  # might have to copy / deepcopy here
			del roles[guild_id][member_id]
			file.seek(0)
			json.dump(roles, file, sort_keys=True, indent=4)
			file.truncate()
			return result

	# Stores user info when user gets kicked
	def homicide_helper(self, guild_id: int, target_user: discord.Member) -> None:
		with open('storage/db/roles.json', 'r+', encoding='utf-8') as file:
			rdb = json.load(file)
			if not guild_id in rdb:
				log.debug(f'Added {guild_id} server id to the role database')
				rdb[guild_id] = {}
			rdb[guild_id][str(target_user.id)] = {'nick': target_user.nick, 'roles': [role.id for role in target_user.roles][1:]}
			file.seek(0)
			json.dump(rdb, file, sort_keys=True, indent=4)
			file.truncate()

	# Kicks user for a certain amount of time
	async def homicide(self, ctx: commands.Context, target_user: discord.Member):
		if target_user.bot:  # we should not be able to kick bots like this.
			return
		self.homicide_helper(str(ctx.guild.id), target_user)  # should prevent the race conditions

		try:
			await target_user.send(await ctx.guild.text_channels[0].create_invite(max_uses=1))  # send invite to the user
			log.info(f'Sent an invite for {ctx.guild.name} to {target_user.name}')
		except:
			log.warning(f'Could not send an invite for {ctx.guild.name} to {target_user.name}')
			await ctx.send(f'{target_user.name} has not been sent an invite!')

		await ctx.send("***Y E E T***")
		await ctx.guild.ban(target_user, delete_message_days=0)
		log.info(f'User {target_user.name} has been banned via homicide')
		await asyncio.sleep(self.config['server_timeout'])
		await ctx.guild.unban(target_user)
		log.info(f'User {target_user.name} has been unbanned via homicide')

	async def reaction_listener_helper(self, msg: discord.Message, caller_id: int, needed_votes: int) -> bool:
		msg = await msg.channel.fetch_message(msg.id)
		yay_voters = [int(user.id) for user in await msg.reactions[0].users().flatten()]  # not sure if this line and the one above can be compressed
		if msg.reactions[0].count + (-1 if caller_id in yay_voters else 0) >= msg.reactions[1].count + needed_votes:
			log.debug('reaction listener returned true')
			return True
		return False

	# Awaits and tracks reactions to messages to track votes
	async def reaction_listener(self, ctx: commands.Context, msg: discord.Message, caller_id: int, needed_votes: int) -> bool:
		log.info(f'A vote was called and needs {needed_votes} votes more in favour')
		await msg.add_reaction('✅')
		await msg.add_reaction('⛔')
		old_embed = msg.embeds[0]
		try:  # wait for functions crash when they reach their timeout.
			while True:
				await self.bot.wait_for('reaction_add', check=lambda reaction, user: reaction.emoji == '✅' and msg.id == reaction.message.id, timeout=self.config['vote_timer'])
				if await self.reaction_listener_helper(msg, caller_id, needed_votes):
					await msg.edit(embed=discord.Embed(title=old_embed.title, footer=old_embed.footer, colour=old_embed.colour, description='Vote resulted in yay ✅'))
					return True
		except:
			if await self.reaction_listener_helper(msg, caller_id, needed_votes):
				await msg.edit(embed=discord.Embed(title=old_embed.title, footer=old_embed.footer, colour=old_embed.colour, description='Vote resulted in yay ✅'))
				return True
			await msg.edit(embed=discord.Embed(title=old_embed.title, footer=old_embed.footer, colour=old_embed.colour, description='Vote resulted in nay ⛔'))
			return False

	# Reassigns roles to newly joined members
	@commands.Cog.listener()
	async def on_member_join(self, member: discord.Member) -> None:
		log.info(f'User {member.name} has joined: {member.guild.name}')
		guild = member.guild  # setting up some basics
		result = self.on_join_helper(str(guild.id), str(member.id))
		if not result[0]:
			return
		user = result[1]
		await member.edit(nick=user['nick'])  # change the usersnick
		user_roles = [guild.get_role(role_id) for role_id in user['roles']]  # fetch all roll objects
		for role in user_roles:
			if role != None:
				log.debug(f'User {member.name} has been re-assigned role: {role.name}')
				await member.add_roles(role)
		log.info(f'User {member.name} has been reassigned their roles')

	async def update(self) -> None:
		self.config = self.load_config()
		log.info(f'Homicide ran an update')

	# Instantly kicks someone
	@commands.command(brief='Insta kick someone', description='Insta kick one or multiple people as an administrator by tagging them.', usage='@bad-person')
	@commands.has_role('admin')
	async def murder(self, ctx: commands.Context, *users: discord.Member) -> None:  # murder now supports multiple arguments
		log.debug(f"MURDER: {ctx.author.name} has called murder on the following: {', '.join([member.name for member in users])}")
		tasks = []
		for user in users:
			tasks.append(asyncio.create_task(self.homicide(ctx, user)))
		asyncio.gather(*tasks)

	# Instantly kick yourself
	@commands.command(brief='Temp ban yourself', description='Temp ban yourself. To save face one might commit the ritual of seppuku', usage='')
	async def suicide(self, ctx) -> None:
		log.debug('SUICIDE: {ctx.author.name} Has committed suicide')
		await ctx.send(f"Dearly beloved\nWe are gathered here today to celebrate the passing of the great samurai: {ctx.author.name}\nMay his loyalty be something we could all live up to!\nお前はもう死んでいる")
		await self.homicide(ctx, ctx.author)

	# Call a vote to kick someone
	@commands.command(brief='Vote to tempban someone.', description='Vote to tempban someone or multiple people by tagging them.', usage='@bad-person \ @bad-role')
	async def lynch(self, ctx: commands.Context) -> None:  # and if murder does then so shall lynch
		users = [role.members for role in ctx.message.role_mentions]
		users.append(ctx.message.mentions)
		users = list(set(sum(users, [])))
		if len(users) == 0:
			msg = await ctx.send(embed=discord.Embed(title='⛔ Need an argument', colour=Colour.from_rgb(0,0,0)))
			await msg.edit(delete_after = 15)
			return

		log.debug(f"LYNCH: {ctx.author.name} has called a lynch on: {' & '.join([member.name for member in users])}")
		embed = discord.Embed(title=f"{ctx.author.name} has called a lynch on: {' & '.join([member.name for member in users])}", colour=Colour.from_rgb(255,0,0), description='Yay or nae?', footer=f"Powered by {self.bot.user.name}")
		msg = await ctx.send(embed=embed)
		if await self.reaction_listener(ctx, msg, ctx.author.id, self.config['lynch_votes']):
			tasks = []
			for user in users:
				tasks.append(asyncio.create_task(self.homicide(ctx, user)))
			asyncio.gather(*tasks)

	# Call a vote to mute someone
	@commands.command(brief='Vote to mute someone for a timeout', description='Vote to mute someone for a timeout.', usage='@loud-person')
	async def silence(self, ctx: commands.Context, *users: discord.Member) -> None:
		user = users[0]
		embed = discord.Embed(title=f"people really wanna shut up {user.name}", colour=Colour.from_rgb(255,0,0), description='Yay or nae?', footer=f"Powered by {self.bot.user.name}")
		msg = await ctx.send(embed=embed)
		if await self.reaction_listener(ctx, msg, ctx.author.id, self.config['mute_votes']):
			log.info(f"SILENCE: {ctx.author.name} has called a lynch on: {user.name} which passed")
			await ctx.send('Now playing: The sound of silence')
			await user.edit(mute=True)
			await asyncio.sleep(self.config['mute_timeout'])
			await user.edit(mute=False)
