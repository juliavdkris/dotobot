import logging
from os import listdir
from os.path import basename

import discord
from discord.ext import commands
from discord.ext.commands.errors import CheckFailure, ExtensionAlreadyLoaded, ExtensionNotFound
from pretty_help import PrettyHelp

# -------------------------> Globals

log = logging.getLogger(__name__)
color = discord.Color.from_rgb(255, 0, 0)

# -------------------------> Functions

# Checks if the ID is from someone who should have run-time access
def developerOnly():
	def predicate(ctx):
		return ctx.author.id in [355730172286205954, 228518187778572288, 282961927657750528]  # TODO not hardcoded
	
	return commands.check(predicate)

# Setup extension
def setup(bot: commands.Bot) -> None:
	bot.add_cog(System(bot))
	log.info(f'Extension has been activated: {basename(__file__)}')

# Teardown extension
def teardown(bot: commands.Bot) -> None:
	log.info(f'Extension has been deactivated: {basename(__file__)}')

# -------------------------> Cogs

# System cog
class System(commands.Cog, name='System', description='Internal control functionality'):
	def __init__(self, bot: commands.Bot) -> None:
		self.bot = bot

	# Triggers on login and provides info
	@commands.Cog.listener()
	async def on_ready(self) -> None:
		log.info(f'Logged in as {self.bot.user}')
		ending_note = f'Powered by {self.bot.user.name}\nFor command {{help.clean_prefix}}{{help.invoked_with}}'
		self.bot.help_command = PrettyHelp(ending_note=ending_note, color=color, no_category='System')

	# Triggers on command execution error
	@commands.Cog.listener()
	async def on_command_error(self, ctx: commands.Context, error: Exception):
		if isinstance(error, CheckFailure):
			return

		log.error(error)
		raise error

	# Starts specific or all extensions
	@developerOnly()
	@commands.command(brief='Start specific or extensions', description='Start specific or all extensions', usage='!start (extensions)')
	async def start(self, ctx: commands.Context, *args) -> None:

		# Start each extension
		if not args or args[0] == 'all':
			for ext in ['packages.' + file[:-3] for file in listdir('src/packages') if file[-3:] == '.py']:
				try:
					self.bot.load_extension(ext)

				except ExtensionAlreadyLoaded as err:
					log.warning(err)
					await ctx.send(f'Extension `{ext}` already active')

				except Exception as err:
					log.warning(err)
					await ctx.send(f'`{ext}` could not be activated')
			
			await ctx.send('All extensions have been started')

		# Start each given extension
		else:	
			for ext in ['packages.' + arg for arg in args]:
				try:
					self.bot.load_extension(ext)
					await ctx.send(f'Extension `{ext}` has been activated')

				except ExtensionNotFound as err:
					log.warning(err)
					await ctx.send(f'Extension `{ext}` not found.')

				except ExtensionAlreadyLoaded as err:
					log.warning(err)
					await ctx.send(f'Extension `{ext}` already active')

				except Exception as err:
					log.warning(err)
					await ctx.send(f'`{ext}` could not be activated')
						
	# Stops specific or all extensions
	@developerOnly()
	@commands.command(brief='Stop specific or all extensions', description='Stop specific or all extensions', usage='!stop (extensions)')
	async def stop(self, ctx: commands.Context, *args) -> None:

		# Stop each extension
		if not args or args[0] == 'all':
			for ext in list(self.bot.extensions.keys()):
				if ext == 'packages.system':
					await ctx.send('I wouldn\'t stop `packages.system` if I were you')
				else:
					self.bot.unload_extension(ext)
			
			await ctx.send('Most extensions have been stopped')
		
		# Stop each given extension
		else:
			for arg in args:
				if arg == 'system':
					await ctx.send('I wouldn\'t stop `packages.system` if I were you')

				elif (ext := 'packages.' + arg) in self.bot.extensions:
					self.bot.unload_extension(ext)
					await ctx.send(f'Extension `{ext}` has been deactivated')

				else:
					await ctx.send(f'Extension `{ext}` not present in active extensions')
	
	# Restarts specific or all extensions
	@developerOnly()
	@commands.command(aliases=['reload'], brief='Restart all or specific extensions', description='Restart all or specific extensions. Extensions need to be active', usage='!restart (extensions)')
	async def restart(self, ctx: commands.Context, *args) -> None:

		# Restart each extension
		if not args or args[0] == 'all':
			for ext in list(self.bot.extensions.keys()):
				self.bot.reload_extension(ext)

			await ctx.send('All modules have been reloaded')

		# Restart each given extension
		else:
			for arg in args:
				if (ext := 'packages.' + arg) in self.bot.extensions.keys():
					self.bot.reload_extension(ext)
					await ctx.send(f'Extension `{ext}` has been reloaded')
					
				else:
					await ctx.send(f'Extension `{ext}` wasn\'t active!')

	# Update specific or all cogs
	@developerOnly()
	@commands.command(brief='Update specific or all cogs', description='Update specific or all cogs, without losing their internal state.', usage='!update (cogs)')
	async def update(self, ctx: commands.Context, *args) -> None:

		# Run an update for each cog
		if not args or args[0] == 'all':
			for cog in self.bot.cogs.values():
				if hasattr(cog, 'update'):
					await cog.update()	
	
			await ctx.send('Everything has been updated')
		
		# Run an update for each given cog
		else:
			for arg in args:
				if arg in self.bot.cogs.keys():
					cog = self.bot.get_cog(arg)
					if hasattr(cog, 'update'):
						await cog.update()
				
				else:
					await ctx.send(f'Extension `{arg}` wasn\'t active!')
