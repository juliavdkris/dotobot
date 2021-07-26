# -------------------------> Dependencies

# Setup python logging
import logging
log = logging.getLogger(__name__)

# Import libraries
from copy import copy
import discord
from discord.ext import commands
from discord.ext.commands.errors import ExtensionAlreadyLoaded, ExtensionNotFound, CheckFailure
import json
import logging as log
from pretty_help import PrettyHelp

from os import getenv
from dotenv import load_dotenv
load_dotenv()

# -------------------------> Globals

log.basicConfig(
    level=log.INFO,  # Basic logging and formatting settings
    format='%(asctime)s [%(levelname)8s] @ %(name)-18s: %(message)s',
    datefmt='%d/%m/%y %H:%M:%S',
    filename='storage/discord.log',  # File settings
    filemode='w',
    encoding='utf-8'
)

log.getLogger('discord').setLevel('WARNING')  # Hide info logs that the discord module sents
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=getenv('PREFIX'), intents=intents)
color = discord.Color.from_rgb(255, 0, 0)
extensions, deactivated_extensions = set(), set()

# -------------------------> Helper functions

def load_config() -> None:
	global extensions, deactivated_extensions
	log.debug(f'config/main.json has been loaded')
	with open('storage/config/main.json', 'r', encoding='utf-8') as file:
		config = json.load(file)
		extensions, deactivated_extensions = set(config['active_extensions']), set(config['unactive_extensions'])


def save_config() -> None:
	log.debug(f'storage/config/main.json has been saved')
	with open('storage/config/main.json', 'w', encoding='utf-8') as file:
		json.dump({'active_extensions': list(extensions), 'unactive_extensions': list(deactivated_extensions)}, file, sort_keys=True, indent=4)


def developerOnly():
    def predicate(ctx):  # Checks if the ID is from someone who should have run-time access
        return ctx.author.id in [355730172286205954, 228518187778572288, 282961927657750528]  # TODO not hardcoded
    return commands.check(predicate)

# -------------------------> events

@bot.before_invoke
async def logging(ctx: commands.Context):
	if not ctx.invoked_subcommand:
		commandlog = log.getLogger('command.invoke')
		if log.root.level != log.DEBUG:
			commandlog.info (f"{ctx.author.name.ljust(16,' ')} | called: {str(ctx.command)}")
		else:
			commandlog.debug(f"{ctx.author.name.ljust(16,' ')} | called: {str(ctx.command).ljust(12,' ')} | with: {ctx.message.content}")

# Triggers on command execution error
@bot.event
async def on_command_error(ctx: commands.Context, error: Exception):
	if isinstance(error, CheckFailure):
		return
	log.error(error)
	raise error

# Triggers on login and provides info
@bot.event
async def on_ready() -> None:
	log.info(f'Logged in as {bot.user}')
	ending_note = f'Powered by {bot.user.name}\nFor command {{help.clean_prefix}}{{help.invoked_with}}'
	bot.help_command = PrettyHelp(ending_note=ending_note, color=color, no_category='System')


# Triggers on message and reacts accordingly
@bot.event
async def on_message(msg: discord.Message) -> None:
	if msg.author.id != bot.user.id:
		msglog = log.getLogger('message.reader')
		msglog.debug(f"{msg.author.name.ljust(16,' ')} | with:  {msg.content}")
		await bot.process_commands(msg)

# -------------------------> Cog configuration commands

@developerOnly()
@bot.command(brief='Update all modules', description='Update all modules according to the config file.', usage='')
async def update(ctx: commands.Context) -> None:
	load_config()
	for ext in extensions:  # Load all modules in config
		if ext not in bot.extensions:
			try:
				bot.load_extension(ext)
			except Exception as e:
				log.warning(e)

	for ext in list(bot.extensions.keys()):  # Unload all modules not mentioned in active config
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

@developerOnly()
@bot.command(brief='Stop specific modules', description='Stop specific modules. Can only stop running modules.', usage='quote')
async def stop(ctx: commands.Context, *args) -> None:
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

@developerOnly()
@bot.command(brief='Start a specific module', description='Start a specific module.', usage='quote')
async def start(ctx: commands.Context, *args) -> None:
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

@developerOnly()
@bot.command(brief='Restart all or specific modules', description='Restart all or specific modules. Module needs to be active', usage='[quote]')
async def restart(ctx: commands.Context, *args) -> None:
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

# -------------------------> Main

if __name__ == '__main__':
	load_config()
	for extension in copy(extensions):
		try:
			bot.load_extension(extension)
		except:
			log.warning(f"Could not be activated: {extension}")
			extensions.remove(extension)
			deactivated_extensions.add(extension)
	save_config()
	bot.run(getenv('TOKEN'))
