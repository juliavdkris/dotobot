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

from os import getenv
import os.path
import json
from dotenv import load_dotenv
load_dotenv()

# -------------------------> Globals

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=getenv('PREFIX'), intents=intents)
extensions, deactivated_extensions = [], []

# -------------------------> Client


# Triggers on login and provides info
@bot.event
async def on_ready():
	log.info(f'Logged in as {bot.user}')


# Triggers on message and reacts accordingly
@bot.event
async def on_message(msg):
	if msg.author.id != bot.user.id:
		log.debug(f'Message from {msg.author}: {msg.content}')
		await bot.process_commands(msg)


@bot.command()
@commands.has_permissions(administrator=True)
async def update(ctx):
	updateable_cogs = ['Homicide', 'Replies', 'Quotes']
	for cogname in updateable_cogs:
		if cogname in bot.cogs:
			await bot.cogs[cogname].update()
	load_config()
	for extension in extensions:
		try:
			bot.load_extension(extension)
		except:
			log.info(f'Module {extension} has already been loaded / does not exist')
	for extension in deactivated_extensions:
		try:
			bot.unload_extension(extension)
		except:
			log.info(f'Module {extension} has already been unloaded')

	await ctx.send('Everything has been updated')


@bot.command()
@commands.has_permissions(administrator=True)
async def stop(ctx, *args):
	for arg in args:
		if (ext := 'packages.' + arg) in extensions:
			bot.unload_extension(ext)
			deactivated_extensions.append(ext)
			extensions.remove(ext)
			await ctx.send(f'Module `{ext}` has been deactivated')
		else:
			await ctx.send(f'Module `{ext}` not present in the active modules')
	save_config()


@bot.command()
@commands.has_permissions(administrator=True)
async def start(ctx, *args):
	for arg in args:
		ext = 'packages.' + arg

		try:
			bot.load_extension(ext)
			await ctx.send(f'Module `{ext}` has been activated')
		except ExtensionNotFound:
			await ctx.send(f'Module `{ext}` not found.')
		except ExtensionAlreadyLoaded:
			await ctx.send(f'Module `{ext}` already active')

		if ext in deactivated_extensions:
			extensions.append(ext)
			deactivated_extensions.remove(ext)
	save_config()


@bot.command()
async def restart(ctx, *args):
	if not args or args[0] == 'all':
		for extension in extensions:
			bot.reload_extension(extension)
		await ctx.send('All modules have been reloaded')
	else:
		for arg in args:
			if (ext := 'packages.' + arg) in extensions:
				bot.reload_extension(ext)
				await ctx.send(f'Module: `{ext}` has been reloaded')


# -------------------------> Helper functions


def load_config():
	global extensions, deactivated_extensions
	log.debug(f'config/main.json has been loaded')
	with open('storage/config/main.json', 'r', encoding='utf-8') as file:
		config = json.load(file)
		extensions, deactivated_extensions = config['active_extensions'], config['unactive_extensions']


def save_config():
	log.debug(f'storage/config/main.json has been saved')
	with open('storage/config/main.json', 'w', encoding='utf-8') as file:
		json.dump({'active_extensions': extensions, 'unactive_extensions': deactivated_extensions}, file, sort_keys=True, indent=4)


# -------------------------> Main
if __name__ == '__main__':
	load_config()
	for extension in extensions:
		bot.load_extension(extension)
	bot.run(getenv('TOKEN'))
