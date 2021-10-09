import logging
import threading
from os.path import basename

import discord
from discord.ext import commands

# -------------------------> Globals

log = logging.getLogger(__name__)
lock = threading.RLock()
vc_suffix = '-VC'

# -------------------------> Functions

# Setup extension
def setup(bot: commands.Bot) -> None:
	bot.add_cog(VoicePing(bot))
	log.info(f'Extension has been activated: {basename(__file__)}')

# Teardown extension
def teardown(bot: commands.Bot) -> None:
	log.info(f'Extension has been deactivated: {basename(__file__)}')

# -------------------------> Cogs

# VoicePing cog
class VoicePing(commands.Cog):
	def __init__(self, bot: commands.Bot):
		self.bot = bot

	# remove all VC roles for which no VC exists.
	async def clean_up(self, guild: discord.Guild) -> None:
		roles = {role.name: role for role in guild.roles}
		vc_channels = [vc.name for vc in guild.voice_channels]
		for role_name in roles:
			if role_name.replace(vc_suffix,'') not in vc_channels and vc_suffix in role_name:
				await roles[role_name].delete(reason=f'Role {role_name} out of date and deleted')
		for role in guild.roles:
			if len(role.members) == 0 and role.name.endswith(vc_suffix):
				await role.delete(reason = f'Role {role.name} has no current users and was cleaned up')

	# only vc_channels have a bitrate attribute
	def is_vc(self, channel: discord.abc.GuildChannel) -> bool:
		try:
			x = channel.bitrate
		except:
			return False
		return True

	# returns the role if it exists otherwise, create the role.
	async def compute_role_if_absent(self, roleName: str, guild: discord.Guild, suffix=None) -> discord.Role:
		roles = {role.name: role for role in guild.roles}
		if suffix:
			roleName = roleName+suffix
		if roleName in roles:
			role = roles[roleName]
			if not role.mentionable:  # clean up unmention-able roles we accidentally created
				await role.edit(mentionable=True)
			return roles[roleName]
		else:
			return await guild.create_role(name=roleName, mentionable=True, reason="Detected a VC which does not have a role.")


	# figure out if joining or leaving.
	@commands.Cog.listener()
	async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState) -> None:
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
	async def on_guild_channel_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel) -> None:
		guild = after.guild
		if not self.is_vc(after):
			return
		roles = {role.name.replace(vc_suffix,''): role for role in guild.roles}
		for role_name in roles:
			if role_name == before.name:
				role = roles[role_name]
				break
		with lock:
			await role.edit(name=(after.name+vc_suffix), reason="Updated VC role in accordance to a channel name change.")

	# delete the role if it exists
	@commands.Cog.listener()
	async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel) -> None:
		guild = channel.guild
		if not self.is_vc(channel):
			return
		with lock:
			await self.clean_up(guild)
