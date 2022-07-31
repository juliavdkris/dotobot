import logging as log
from os import getenv, listdir

import discord
from discord.ext import commands
from discord import ExtensionAlreadyLoaded
from dotenv import load_dotenv

# -------------------------> Globals

load_dotenv()
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=getenv('PREFIX'), intents=intents)

# -------------------------> Logging

log.basicConfig(
    level=log.INFO,
    format='%(asctime)s [%(levelname)8s] @ %(name)-18s: %(message)s',
    datefmt='%d/%m/%y %H:%M:%S',
    filename='storage/discord.log',
    filemode='w',
    encoding='utf-8'
)

# Hide info logs that the discord module sents
log.getLogger('discord').setLevel('WARNING')

# Logs command calls
@bot.before_invoke
async def logging(ctx: commands.Context):
	if not ctx.invoked_subcommand:
		commandlog = log.getLogger('command.invoke')
		if log.root.level != log.DEBUG:
			commandlog.info(f"{ctx.author.name.ljust(16,' ')} | called: {str(ctx.command)}")
		else:
			commandlog.debug(f"{ctx.author.name.ljust(16,' ')} | called: {str(ctx.command).ljust(12,' ')} | with: {ctx.message.content}")

# -------------------------> Main

if __name__ == '__main__':

	# Start all extensions
	for ext in ['packages.' + file[:-3] for file in listdir('src/packages') if file[-3:] == '.py']:
		try:
			bot.load_extension(ext)

		except ExtensionAlreadyLoaded as err:
			log.warning(err)

		except Exception as err:
			log.warning(err)

	bot.run(getenv('TOKEN'))
