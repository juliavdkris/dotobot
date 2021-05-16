# Setup python logging
import logging
log = logging.getLogger(__name__)

import discord
from discord.ext import commands

import threading
lock = threading.RLock()

vc_suffix = '-VC'

def setup(bot):
	log.info('VoicePing module has been activated')
	bot.add_cog(VoicePing(bot))


def teardown(bot):
	log.info('VoicePing module has been deactivated')


class VoicePing(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	# remove all VC roles for which no VC exists.
	async def clean_up(self, guild):
		roles = {role.name: role for role in guild.roles}
		vc_channels = [vc.name for vc in guild.voice_channels]
		for role_name in roles:
			if role_name.replace(vc_suffix,'') not in vc_channels and vc_suffix in role_name:
				await roles[role_name].delete(reason=f'Role {role_name} out of date and deleted')

	# only vc_channels have a bitrate attribute
	def is_vc(self, channel):
		try:
			x = channel.bitrate
		except:
			return False
		return True

	# returns the role if it exists otherwise, create the role.
	async def compute_role_if_absent(self, roleName, guild: discord.Guild, suffix=None):
		roles = {role.name: role for role in guild.roles}
		if suffix:
			roleName = roleName+suffix
		if roleName in roles:
			role = roles[roleName]
			if not role.mentionable:  # clean up unmention-able roles we accidentally created
				await role.edit(mentionable=True)
			return roles[roleName]
		else:
			return await guild.create_role(name=roleName, mentionable=True)


	# figure out if joining or leaving.
	@commands.Cog.listener()
	async def on_voice_state_update(self, member, before, after):
		guild = member.guild

		if after.channel:
			with lock:
				role = await self.compute_role_if_absent(after.channel.name, guild, vc_suffix)
			await member.add_roles(role)

		if before.channel and before.channel != after.channel:
			with lock:
				role = await self.compute_role_if_absent(before.channel.name, guild, vc_suffix)
			await member.remove_roles(role)

		with lock:
			await self.clean_up(guild)


	# figure out if vc or text, if vc look for a role and update.
	@commands.Cog.listener()
	async def on_guild_channel_update(self, before, after):
		guild = after.guild
		if not self.is_vc(after):
			return
		roles = {role.name.replace(vc_suffix,''): role for role in guild.roles}
		for role_name in roles:
			if role_name == before.name:
				role = roles[role_name]
				break
		with lock:
			await role.edit(name=(after.name+vc_suffix))

	# delete the role if it exists
	@commands.Cog.listener()
	async def on_guild_channel_delete(self, channel):
		guild = channel.guild
		if not self.is_vc(channel):
			return
		with lock:
			await self.clean_up(guild)