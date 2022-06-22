import logging
from asyncio import sleep
from os.path import basename
from random import randint

import discord
from discord.ext import commands
from dotenv import load_dotenv

# -------------------------> Globals

# Setup environment
log = logging.getLogger(__name__)
load_dotenv()

# -------------------------> Functions

# Setup extension
def setup(bot: commands.Bot) -> None:
	bot.add_cog(Voice(bot))
	log.info(f'Extension has been activated: {basename(__file__)}')

# Teardown extension
def teardown(bot: commands.Bot) -> None:
	log.info(f'Extension has been deactivated: {basename(__file__)}')

# -------------------------> Cogs

# Voice cog
class Voice(commands.Cog, description='Play music in voice'):
	def __init__(self, bot):
		self.bot = bot

	# Plays a sound in voice
	async def voice_helper(self, vc, file):
		try:
			client = await vc.connect()
		except:
			if len([client for client in self.bot.voice_clients if client.channel == vc]) != 0:  # very problematic as this could take over a client just when it is about to disconnect, should be synced in reality
				client = [client for client in self.bot.voice_clients if client.channel == vc][0]
			else:
				await [client for client in self.bot.voice_clients if client.guild == vc.guild][0].disconnect()
				client = await vc.connect()

		client.play(discord.FFmpegPCMAudio(source='storage/static/sounds/' + file))
		while client.is_playing():
			await sleep(2)
		await client.disconnect()

	# Plays crabrave in voice
	async def crabrave(self, text_channel, vc, arg=None):
		path = 'crab_rave.mp3' if randint(0, 20) != 0 else 'under_rave.mp3'
		await text_channel.send(f"{arg} IS GONE :crab: :crab: :crab: :crab: :crab: :crab: :crab:")  # crab rave gif / shortened version of crab rave
		await text_channel.send('https://tenor.com/view/crab-safe-dance-gif-13211112')
		await self.voice_helper(vc, path)

	# Plays sounds in voice depending on messages
	@commands.Cog.listener()
	async def on_message(self, msg):
		if msg.author.id == self.bot.user.id:
			return
		content = msg.content.lower()
		if content.endswith('is gone'):
			await self.crabrave(msg.channel, msg.author.voice.channel, msg.content.upper()[:-7])
		elif 'play despacito' in content:
			await self.voice_helper(msg.author.voice.channel, 'despacito.mp3')
		elif 'play zoutelande' in content or 'speel zoutelande' in content:
			await self.voice_helper(msg.author.voice.channel, 'zoutelande.mp3')
		elif 'tequila' in content:
			await self.voice_helper(msg.author.voice.channel, 'tequila.mp3')
		elif 'sigma' in content:
			await self.voice_helper(msg.author.voice.channel, 'sigma.mp3')

	# Plays crabrave in voice
	@commands.command(brief='Stuff is gone', description='Stuff is gone.', usage='my social life')
	async def gone(self, ctx, arg: str = ''):
		await self.crabrave(ctx, ctx.author.voice.channel, arg)

	# Plays coffin dance in voice
	@commands.command(brief='He dead', description='He dead.', usage='')
	async def dead(self, ctx):
		await self.voice_helper(ctx.author.voice.channel, 'astronomia.mp3')  # coffin dance gif / shortened song
