# -------------------------> Dependencies

# Setup python logging
import logging
log = logging.getLogger(__name__)

# Import libraries
import discord
from discord.ext import commands
import json
import asyncio
import os.path
from os import path, makedirs
from copy import deepcopy

# -------------------------> Main


def setup(bot):
	log.info('Homicide module has been activated')
	bot.add_cog(Homicide(bot))


def teardown(bot):
	log.info('Homicide module has been deactivated')


class Homicide(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.config = self.load_config()

	def load_config(self):
		log.debug(f'config/homicide.json has been loaded')
		with open('storage/config/homicide.json', 'r', encoding='utf-8') as file:
			return json.load(file)

	def on_join_helper(self, guild_id, member_id):
		with open('storage/db/roles.json', 'r+', encoding='utf-8') as file:
			roles = json.load(file)
			if not guild_id in roles and not member_id in roles[guild_id]:  # if we don't know this user skip the function
				return (False, {})
			result = (True, deepcopy(roles[guild_id][member_id]))  # might have to copy / deepcopy here
			del roles[guild_id][member_id]
			file.seek(0)
			json.dump(roles, file, sort_keys=True, indent=4)
			file.truncate()
			return result

	def homicide_helper(self, guild_id, target_user):
		with open('storage/db/roles.json', 'r+', encoding='utf-8') as file:
			rdb = json.load(file)
			if not guild_id in rdb:
				log.info(f'Added {guild_id} server id to the role database')  # TODO maybe actually do this via the server so we can see their name /shrug
				rdb[guild_id] = {}
			rdb[guild_id][str(target_user.id)] = {'nick': target_user.nick, 'roles': [role.id for role in target_user.roles][1:]}
			file.seek(0)
			json.dump(rdb, file, sort_keys=True, indent=4)
			file.truncate()

	async def homicide(self, ctx, target_user):
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

	async def reaction_listener_helper(self, msg, caller_id, needed_votes):
		msg = await msg.channel.fetch_message(msg.id)
		yay_voters = [int(user.id) for user in await msg.reactions[0].users().flatten()]  # not sure if this line and the one above can be compressed
		if msg.reactions[0].count + (-1 if caller_id in yay_voters else 0) >= msg.reactions[1].count + needed_votes:
			log.debug('reaction listener returned true')
			return True
		return False

	async def reaction_listener(self, ctx, msg, caller_id, needed_votes):
		log.info(f'A vote was called and needs {needed_votes} votes more in favour')
		await msg.add_reaction('✅')
		await msg.add_reaction('⛔')
		try:  # wait for functions crash when they reach their timeout.
			while True:
				await self.bot.wait_for('reaction_add', check=lambda reaction, user: reaction.emoji == '✅' and msg.id == reaction.message.id, timeout=self.config['vote_timer'])
				if await self.reaction_listener_helper(msg, caller_id, needed_votes):
					return True
		except:
			if await self.reaction_listener_helper(msg, caller_id, needed_votes):
				return True
			await ctx.send('Vote resulted in nay ⛔')
			return False

	@commands.Cog.listener()
	async def on_member_join(self, member):
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

	async def update(self):
		self.config = self.load_config()
		log.info(f'Homicide ran an update')

	@commands.command()
	@commands.has_role('admin')
	async def murder(self, ctx, *users: discord.Member):  # murder now supports multiple arguments
		log.info(f"MURDER: {ctx.author.name} has called murder on the following: {', '.join([member.name for member in users])}")
		tasks = []
		for user in users:
			tasks.append(asyncio.create_task(self.homicide(ctx, user)))
		asyncio.gather(*tasks)

	@commands.command()
	async def suicide(self, ctx):
		log.info('SUICIDE: {ctx.author.name} Has committed suicide')
		await ctx.send(f"Dearly beloved\nWe are gathered here today to celebrate the passing of the great samurai: {ctx.author.name}\nMay his loyalty be something we could all live up to!\nお前はもう死んでいる")
		await self.homicide(ctx, ctx.author)

	@commands.command()
	async def lynch(self, ctx, *users: discord.Member):  # and if murder does then so shall lynch
		log.info(f"LYNCH: {ctx.author.name} has called a lynch on: {' & '.join([member.name for member in users])}")
		msg = await ctx.send(f"{ctx.author.name} has called a lynch on {' & '.join([member.name for member in users])}\nYay or nae?")  # TODO joining 1 element in the array does what?
		if await self.reaction_listener(ctx, msg, ctx.author.id, self.config['lynch_votes']):
			tasks = []
			for user in users:
				tasks.append(asyncio.create_task(self.homicide(ctx, user)))
			asyncio.gather(*tasks)

	@commands.command()
	async def genocide(self, ctx, *role: discord.Role):  # when the tensions get high
		role = role[0]
		log.info(f"GENOCIDE: {ctx.author.name} has called a genocide on: {role.name}")
		if role == ctx.guild.roles[0]:
			await ctx.send("I mean, I don't judge but someone will.")
			return
		msg = await ctx.send(f"{ctx.author.name} has called a genocide on all of the {role.name}\nYay or nae?")
		if await self.reaction_listener(ctx, msg, ctx.author.id, max(self.config['lynch_votes'], (len(role.members) - 1)) // 2):
			tasks = []
			for user in role.members:
				tasks.append(asyncio.create_task(self.homicide(ctx, user)))
			asyncio.gather(*tasks)

	@commands.command()
	async def silence(self, ctx, *users: discord.Member):
		user = users[0]
		msg = await ctx.send(f'Damn people really wanna shut up {user.name}.\nYour say.')
		if await self.reaction_listener(ctx, msg, ctx.author.id, self.config['mute_votes']):
			log.info(f"LYNCH: {ctx.author.name} has called a lynch on: {user.name} which passed")
			await ctx.send('Now playing: The sound of silence')
			await user.edit(mute=True)
			await asyncio.sleep(self.config['mute_timeout'])
			await user.edit(mute=False)
