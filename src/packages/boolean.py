# -------------------------> Dependencies

# Setup python logging
import logging
log = logging.getLogger(__name__)

# Import libraries
import discord
from discord.ext import commands

from itertools import product
from copy import deepcopy

# -------------------------> Main


def setup(bot):
	log.info('Boolean module has been activated')
	bot.add_cog(Boolean(bot))


def teardown(bot):
	log.info('Boolean module has been deactivated')


class Boolean(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.functions = {}

	# Recursively inserts nested functions
	def insert_funcs(self, func):
		for target in func['nfnc']:
			nfnc = self.insert_funcs(self.functions[target])  # Recurse into nested functions

			# Update function properties
			func['bvar'] += nfnc['bvar']
			func['stmt'] = func['stmt'].replace(f'${target}', f'({nfnc["stmt"]})')

		func['bvar'] = sorted(set(func['bvar']))  # Sort and filter boolean variables
		func['nfnc'] = []  # Clear nested function set
		return func

	# Define bool command group
	@commands.group()
	async def b(self, ctx):
		if ctx.invoked_subcommand is None:
			log.warning(f'User {ctx.author.name} has passed an invalid boolean subcommand')
			await ctx.send('Invalid boolean subcommand')

	# Clears all expressions
	@b.command()
	async def clear(self, ctx):
		log.info(f'Recieved \'!b clear\' command from user \'{ctx.author.name}\'')

		self.functions = {}

		log.debug(f'Succesfully cleared all functions')

	# Set a bool variable to a expression parsed into a statement
	@b.command()
	async def set(self, ctx, name: str, *, expr: str):
		log.info(f'Recieved \'!b set\' command from user \'{ctx.author.name}\'')

		alphabet = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
		variable = False
		multiply = False

		# Prepare properties
		name = name[0]  # The function identifier
		expr = ''.join(expr.split())  # The unparsed expression
		bvar = set()  # All occuring boolean variables
		nfnc = set()  # All occuring nested functions
		stmt = ' '  # The parsed statement

		# Parse expression
		for c in expr:
			if c not in alphabet + '$!*^+()':  # Check for character validity
				log.error(f'User {ctx.author.name} provided an invalid expresson containing illegal char \'{c}\'')
				await ctx.send(f'Invalid expression provided: Found illegal char \'{c}\'')
				return

			if multiply and c not in '*+^)':  # Insert and-statments in appropriate locations
				stmt += 'and '

			if c in alphabet:  # Add variables to variable set
				if variable:
					nfnc.add(c)
					stmt += f'${c} '
				else:  # Add nested functions to function set
					bvar.add(c)
					stmt += f'{c} '

			else:  # Replace operators with python compatible keywords/operators
				if c == '*':
					stmt += 'and '
				elif c == '^':
					stmt += '^ '
				elif c == '!':
					stmt += 'not '
				elif c == '+':
					stmt += 'or '
				elif c in '()':
					stmt += f'{c} '

			variable = c == '$'  # Update flags according to current character
			multiply = c not in '$!*^+('

		# Store results
		self.functions[name] = {'name': name, 'expr': expr, 'stmt': stmt, 'bvar': sorted(bvar), 'nfnc': sorted(nfnc)}

		func = self.functions[name]
		log.debug(f'Succesfully set \'{func["name"]}\' to statement: \'{func["stmt"]}\' using expression: \'{func["expr"]}\'. Collected variables: {", ".join(func["bvar"])} and nested functions: {", ".join(func["nfnc"])}')

	# Display the properties of a bool variable
	@b.command()
	async def view(self, ctx, target: str):
		log.info(f'Recieved \'!b view\' command from user \'{ctx.author.name}\'')
		if target == 'all':

			# Construct message
			msg = 'Displaying **all** functions\n```'
			for name, func in self.functions.items():
				msg += f'{name} -> {func["expr"]}\n'

			# Display information
			await ctx.send(msg + '```')

		else:
			if target not in self.functions:  # Check the existence of provided target
				log.error(f'User {ctx.author.name} provided a non-existent variable for \'!b view\'')
				await ctx.send('Non-existent variable provided')
				return

			# Insert functions if requested
			func = deepcopy(self.functions[target])
			if 'insert' in ctx.message.content.split():
				try:
					func = self.insert_funcs(func)
				except RecursionError:
					log.error(f'User \'{ctx.author.name}\' provided self-reffering expressions for \'!b view\'')
					await ctx.send(f'Found self-referring expressions')
					return
				except KeyError:
					log.error(f'User \'{ctx.author.name}\' provided functions containing non-existant nested functions for \'!b view\'')
					await ctx.send(f'Function contains non-existant nested functions')
					return

			# Display information
			await ctx.send(f'Displaying information at **{target}**\n``` Expression -> {func["expr"]}\n Statement  ->{func["stmt"]}\n Variables  -> {", ".join(func["bvar"])}\n Functions  -> {", ".join(func["nfnc"])}```')

		log.debug(f'Successfully displayed information at \'{target}\'')

	# Display the truth table of any number of expressions
	@b.command()
	async def table(self, ctx, *, targets: str):
		log.info(f'Recieved \'!b table\' command from user \'{ctx.author.name}\'')

		functions = {}
		superset = []
		subsets = []

		# Insert functions and find the superset
		for target in targets.split():
			func = deepcopy(self.functions[target])

			# Insert functions
			try:
				func = self.insert_funcs(func)
			except RecursionError:
				log.error(f'User \'{ctx.author.name}\' provided self-reffering expressions for \'!b table\'')
				await ctx.send(f'Found self-referring expressions')
				return
			except KeyError:
				log.error(f'User \'{ctx.author.name}\' provided functions containing non-existant nested functions for \'!b table\'')
				await ctx.send(f'Function contains non-existant nested functions')
				return

			# Sort boolean variables into sub and supersets
			if len(func['bvar']) > len(superset):
				subsets.append(superset)
				superset = func['bvar']
			elif len(func['bvar']) == len(superset):
				if func['bvar'] != superset:
					log.error(f'User \'{ctx.author.name}\' provided targets containing conflicting variables for \'!b table\'')
					await ctx.send('Targets contained mismatched variables')
					return
			else:
				subsets.append(func['bvar'])

			functions[target] = func

		# Check for subset validity
		for subset in subsets:
			if not set(subset).issubset(set(superset)):
				log.error(f'User \'{ctx.author.name}\' provided targets containing conflicting variables for \'!b table\'')
				await ctx.send('Targets contained mismatched variables')
				return

		# Display information
		msg = f'Displaying truthtable at **{targets}**```{" ".join(superset)} │ {targets}\n{"─"*len(superset)*2}┼{"─"*len(targets)*2}'
		for perm in product((0, 1), repeat=len(superset)):
			msg += f'\n{" ".join(list(map(lambda x: str(x), perm)))} │'  # Append permutation to msg
			for target in targets.split():

				# Insert permutation values into boolean variables
				func = deepcopy(functions[target])
				for var in func['bvar']:
					func['stmt'] = func['stmt'].replace(f' {var} ', f' {perm[superset.index(var)]} ')

				# Append results to msg
				msg += ' 1' if eval(func['stmt']) else ' 0'

		await ctx.send(msg + '```')

		log.debug(f'Successfully displayed table at \'{targets}\'')

	# Display the k-map of target expressions
	@b.command()
	async def kmap(self, ctx, target: str):
		log.info(f'Recieved \'!b kmap\' command from user \'{ctx.author.name}\'')

		# Check for command validity
		if target not in self.functions:  # Check the existence of provided name
			log.error(f'User {ctx.author.name} provided a non-existent variable for \'!b kmap\'')
			await ctx.send('Non-existent variable provided')
			return

		# Insert functions
		try:
			func = self.insert_funcs(deepcopy(self.functions[target]))
		except RecursionError:
			log.error(f'User \'{ctx.author.name}\' provided self-reffering expressions for \'!b kmap\'')
			await ctx.send(f'Found self-referring expressions')
			return
		except KeyError:
			log.error(f'User \'{ctx.author.name}\' provided functions containing non-existant nested functions for \'!b kmap\'')
			await ctx.send(f'Function contains non-existant nested functions')
			return

		# Calculate results
		out = []
		for perm in product((0, 1), repeat=len(func['bvar'])):
			stmt = deepcopy(func['stmt'])
			for i, var in enumerate(func['bvar']):
				stmt = stmt.replace(f' {var} ', f' {perm[i]} ')
			out.append('1' if eval(stmt) else '0')

		if len(out) == 16:
			await ctx.send(
			    f'```               {func["bvar"][2]}\n            ───────\n     {out[0]} │ {out[1]} │ {out[3]} │ {out[2]}\n    ───┼───┼───┼───\n     {out[4]} │ {out[5]} │ {out[7]} │ {out[6]}  │\n    ───┼───┼───┼─── │ {func["bvar"][1]}\n  │  {out[12]} │ {out[13]} │ {out[15]} │ {out[14]}  │\n{func["bvar"][0]} │ ───┼───┼───┼───\n  │  {out[8]} │ {out[9]} │ {out[11]} │ {out[10]}\n        ───────\n           {func["bvar"][3]}```'
			)
		elif len(out) == 8:
			await ctx.send(f'```               {func["bvar"][1]}\n            ───────\n     {out[0]} │ {out[1]} │ {out[3]} │ {out[2]}\n    ───┼───┼───┼───\n{func["bvar"][0]} │  {out[4]} │ {out[5]} │ {out[7]} │ {out[6]}\n        ───────\n           {func["bvar"][2]}```')
		elif len(out) == 4:
			await ctx.send(f'```         {func["bvar"][1]}\n        ───\n     {out[0]} │ {out[1]}\n    ───┼───\n{func["bvar"][0]} │  {out[2]} │ {out[3]}```')
		elif len(out) == 2:
			await ctx.send(f'```     {func["bvar"][0]}\n    ───\n {out[0]} │ {out[1]}```')
		else:
			await ctx.send('Your expression has too many variables! I can only display k-maps with 4 or less variables')

		log.debug(f'Successfully displayed k-map at \'{target}\'')
