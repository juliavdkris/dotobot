# -------------------------> Dependencies

# Setup python logging
import logging
log = logging.getLogger(__name__)

# Import libraries
import discord
from discord.ext import commands
from os import getenv
from os.path import basename
from asyncio import sleep
from random import randint
from dotenv import load_dotenv
load_dotenv()


def setup(bot: commands.Bot) -> None:
	bot.add_cog(Voice(bot))
	log.info(f'Module has been activated: {basename(__file__)}')

def teardown(bot: commands.Bot) -> None:
	log.info(f'Module has been de-activated: {basename(__file__)}')


class Voice(commands.Cog, description='Play music in voice'):
	def __init__(self, bot):
		self.bot = bot
		self.path = getenv('FFMPEG')

	async def voice_helper(self, vc, file):
		vc = await vc.connect()
		vc.play(discord.FFmpegPCMAudio(executable=self.path, source='storage/static/sounds/' + file))
		while vc.is_playing():
			await sleep(2)
		await vc.disconnect()

	async def crabrave(self, text_channel, vc, arg=None):
		path = 'crab_rave2.mp3' if randint(0, 1) == 0 else 'crab_rave.mp3'
		await text_channel.send(f"{arg} IS GONE :crab: :crab: :crab: :crab: :crab: :crab: :crab:")  # crab rave gif / shortened version of crab rave
		await text_channel.send('https://tenor.com/view/crab-safe-dance-gif-13211112')
		await self.voice_helper(vc, path)

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
			await self.voice_helper(msg.author.voice.channel, 'hola_cabron.mp3')

	@commands.command(brief='Stuff is gone', description='Stuff is gone.', usage='my social life')
	async def gone(self, ctx, arg: str = ''):
		await self.crabrave(ctx, ctx.author.voice.channel, arg)

	@commands.command(brief='He dead', description='He dead.', usage='')
	async def dead(self, ctx):
		await self.voice_helper(ctx.author.voice.channel, 'astronomia.mp3')  # coffin dance gif / shortened song
