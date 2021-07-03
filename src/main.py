# -------------------------> Dependencies

# Setup python logging
import logging as log
log.basicConfig(
    level=log.INFO,  # Basic logging and formatting settings
    format='%(asctime)s [%(levelname)s] @ %(name)s: %(message)s',
    datefmt='%d/%m/%y %H:%M:%S',
    filename='storage/discord.log',  # File settings
    filemode='w',
    encoding='utf-8'
)

# Import libraries
import discord
from discord.ext import commands
from pretty_help import PrettyHelp
from discord.ext.commands.errors import ExtensionAlreadyLoaded, ExtensionNotFound

from os import getenv
import json
from dotenv import load_dotenv
load_dotenv()

# -------------------------> Globals

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=getenv('PREFIX'), intents=intents)
color = discord.Color.from_rgb(255, 0, 0)
extensions, deactivated_extensions = set(), set()

# -------------------------> Client


# Triggers on login and provides info
@bot.event
async def on_ready():
	log.info(f'Logged in as {bot.user}')
	ending_note = f'Powered by {bot.user.name}\nFor command {{help.clean_prefix}}{{help.invoked_with}}'
	bot.help_command = PrettyHelp(ending_note=ending_note, color=color, no_category='System')


# Triggers on message and reacts accordingly
@bot.event
async def on_message(msg):
	if msg.author.id != bot.user.id:
		log.debug(f'Message from {msg.author}: {msg.content}')
		await bot.process_commands(msg)


@bot.command(brief='Update all modules', description='Update all modules according to the config file.', usage='')
@commands.has_permissions(administrator=True)
async def update(ctx):
	load_config()
	for ext in extensions:  # load all modules in config
		if ext not in bot.extensions:
			try:
				bot.load_extension(ext)
			except Exception as e:
				log.warning(e)

	for ext in list(bot.extensions.keys()):  # unload all modules not mentioned in active config
		if ext not in extensions:
			try:
				bot.unload_extension(ext)
				deactivated_extensions.add(ext)
			except Exception as e:
				log.warning(e)

	for cog in bot.cogs.values():
		if hasattr(cog, 'update'):
			await cog.update()

	await ctx.send('Everything has been updated')


@bot.command(brief='Stop specific modules', description='Stop specific modules. Can only stop running modules.', usage='quote')
@commands.has_permissions(administrator=True)
async def stop(ctx, *args):
	for arg in args:
		if (ext := 'packages.' + arg) in bot.extensions:
			bot.unload_extension(ext)
			deactivated_extensions.add(ext)
			if ext in extensions:
				extensions.remove(ext)
			await ctx.send(f'Module `{ext}` has been deactivated')
		else:
			await ctx.send(f'Module `{ext}` not present in the active modules')
	save_config()


@bot.command()
async def exe(ctx):
	print(bot.extensions)

@bot.command(brief='Start a specific module', description='Start a specific module.', usage='quote')
@commands.has_permissions(administrator=True)
async def start(ctx, *args):
	for arg in args:
		ext, e = 'packages.' + arg, None
		try:
			bot.load_extension(ext)
			extensions.add(ext)
			await ctx.send(f'Module `{ext}` has been activated')
		except ExtensionNotFound as e:
			log.warning(e)
			await ctx.send(f'Module `{ext}` not found.')
		except ExtensionAlreadyLoaded as e:
			log.warning(e)
			await ctx.send(f'Module `{ext}` already active')
		except Exception as e:
			log.warning(e)
			await ctx.send(f'Something went wrong, please read the logs for more information')

		if ext in deactivated_extensions:
			deactivated_extensions.remove(ext)
	save_config()


@bot.command(brief='Restart all or specific modules', description='Restart all or specific modules. Module needs to be active', usage='[quote]')
async def restart(ctx, *args):
	if not args or args[0] == 'all':
		for extension in list(bot.extensions.keys()):
			bot.reload_extension(extension)
		await ctx.send('All modules have been reloaded')
	else:
		for arg in args:
			if (ext := 'packages.' + arg) in bot.extensions.keys():
				bot.reload_extension(ext)
				await ctx.send(f'Module: `{ext}` has been reloaded')
			else:
				await ctx.send(f'Module: `{ext}` was not active.')


# -------------------------> Helper functions


def load_config():
	global extensions, deactivated_extensions
	log.debug(f'config/main.json has been loaded')
	with open('storage/config/main.json', 'r', encoding='utf-8') as file:
		config = json.load(file)
		extensions, deactivated_extensions = set(config['active_extensions']), set(config['unactive_extensions'])


def save_config():
	log.debug(f'storage/config/main.json has been saved')
	with open('storage/config/main.json', 'w', encoding='utf-8') as file:
		json.dump({'active_extensions': list(extensions), 'unactive_extensions': list(deactivated_extensions)}, file, sort_keys=True, indent=4)


# -------------------------> Main
if __name__ == '__main__':
	load_config()
	for extension in extensions:
		bot.load_extension(extension)
	bot.run(getenv('TOKEN'))
