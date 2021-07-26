# -------------------------> Dependencies

# Setup python logging
import logging
log = logging.getLogger(__name__)

# Import libraries
import discord
from discord import Colour
from discord.ext import commands
import json
from os import path
from os.path import basename
from random import choice
import re
from typing import Dict, List, Tuple, Union

# -------------------------> Main

def setup(bot: commands.Bot) -> None:
	bot.add_cog(Quotes(bot))
	log.info(f'Module has been activated: {basename(__file__)}')

def teardown(bot: commands.Bot) -> None:
	log.info(f'Module has been de-activated: {basename(__file__)}')

class Quotes(commands.Cog, name='Quote', description='Quote your friends out of context'):
	def __init__(self, bot: commands.Bot):
		self.bot = bot
		self.config = self.load_config()

	# Updates config
	async def update(self):
		self.config = self.load_config()
		log.info(f'Quotes ran an update')

	# Loads config files
	def load_config(self):
		log.debug(f'config/quotes.json has been loaded')
		with open('storage/config/quotes.json', 'r', encoding='utf-8') as file:
			return json.load(file)

	# Load quote database
	def load_quotes(self, guild_id: str) -> Dict[str, Dict[str, Union[str, int, List[int] ]]]:
		log.debug(f'db/quotes/{guild_id}.json has been loaded')
		with open(f'storage/db/quotes/{guild_id}.json', 'r', encoding='utf-8') as file:
			return json.load(file)

	# Parses string into different groups
	def split_quote(self, quote: str) -> Tuple[str,str]:
		REGEX = r'["“](.*)["”] ?- ?(.*)'
		match = re.search(REGEX, quote)
		return match.group(1), match.group(2)

	async def quote(self, ctx: commands.Context, args:str) -> None:
		guild_key = str(ctx.guild.id)
		quotes = self.load_quotes(guild_key)

		try:
			args = args.split()[1]
			quote_key = str(int(args))
			if quote_key not in quotes:
				raise Exception('key was not present in the dictionary')
		except:
			quote_key = choice(list(quotes.keys()))

		quote = quotes[quote_key]
		await ctx.send(f'> {quote_key}: \"{quote["quote"]}\" - {quote["author"]}')

	# Groups quotes into blocks
	async def mass_quote(self, ctx: commands.Context, quotes: list):
		quotes, msg = sorted(quotes, key=lambda i: i['id']), ''
		if len(quotes) == 0:
			return await ctx.send(embed = discord.Embed(title="No quotes could be found", description="Try a different search term or submit your own using !q add", color=Colour.from_rgb(255,0,0)))

		starting_id = quotes[0]['id']
		quoteables = []

		for quote in quotes:
			sub_msg = f"{quote['id']}: \"{quote['quote']}\" - {quote['author']}\n"
			if len(msg) + len(sub_msg) >= 975:
				quoteables.append({"msg": msg, "start": starting_id, "prev": previous_id})
				msg, starting_id = '', quote['id']
			msg, previous_id = msg + sub_msg, quote['id']

		quoteables.append({"msg": msg, "start": starting_id, "prev": previous_id})
		await self.mass_quote_embed(ctx, quoteables)

	# Displays quotes en-mass
	async def mass_quote_embed(self, ctx: commands.Context, quote_blocks: List[Dict[str, Union[int, str]]]) -> None:
		colours = [Colour.from_rgb(255,0,0), Colour.orange(), Colour.gold(), Colour.green(), Colour.blue(), Colour.dark_blue(), Colour.purple()]
		embed = discord.Embed(title="Quotes", colour = colours[0])

		for index, value in enumerate(quote_blocks):
			if index % 6 == 0 and index != 0:
				embed.set_footer(text=f"Powered by {self.bot.user.name}")
				await ctx.send(embed=embed)
				embed = discord.Embed(title="Quotes", colour = colours[(index // 6) % len(colours)])
			embed.add_field(name=f"Quotes {value['start']} : {value['prev']}", value=value['msg'], inline=False)
		embed.set_footer(text=f"Powered by {self.bot.user.name}")

		await ctx.send(embed=embed)

	# Command group !quote
	@commands.group(aliases=['quote'], brief='Subgroup for quote functionality', description='Subgroup for quote functionality. Use !help q')
	async def q(self, ctx: commands.Context) -> None:
		if not path.isfile('storage/db/quotes/' + str(ctx.guild.id) + '.json'):
			with open('storage/db/quotes/' + str(ctx.guild.id) + '.json', 'w+', encoding='utf-8') as file:
				json.dump({}, file, indent=4)
		if ctx.invoked_subcommand is None:
			log.info(f'User {ctx.author.name} has passed an invalid quote subcommand: "{ctx.message.content}"')
			await self.quote(ctx, ctx.message.content)

	# Adds a quote to the database
	@q.command(brief='Add a quote', description='Add a quote to the database', usage='"[quote]" - [author]')
	async def add(self, ctx: commands.Context, *, args=None) -> None:
		guild_id = str(ctx.guild.id)
		quote, author = self.split_quote(args)

		with open(f'storage/db/quotes/{guild_id}.json', 'r+', encoding='utf-8') as file:
			quotes = json.load(file)
			if len(quotes) == 0:
				nextid = 0
			else:
				nextid = max(map(lambda x: int(x), quotes.keys())) + 1
			quotes[str(nextid)] = {'quote': quote, 'author': author, 'remove_votes': [], 'remove_vetos': [], 'id': nextid}
			file.seek(0)
			json.dump(quotes, file, indent=4)
			file.truncate()

		log.info(f"A quote has been added; {nextid}: \"{quote}\" - {author}")
		await ctx.send(f'Quote added. Assigned ID: {nextid}')

	# Deletes a quote from the database
	@q.command(aliases=['del', 'delete'], brief='Remove a quote', description='Remove a quote from the database by id.', usage='[quote id]')
	@commands.has_permissions(administrator=True)
	async def remove(self, ctx: commands.Context, *, args=None) -> None:
		quote_key, guild_id, succes = str(int(args)), str(ctx.guild.id), False

		with open(f'storage/db/quotes/{guild_id}.json', 'r+', encoding='utf-8') as file:
			quotes = json.load(file)
			if quote_key in quotes:
				quote = quotes.pop(quote_key)
				succes = True
			file.seek(0)
			json.dump(quotes, file, indent=4)
			file.truncate()

		if succes:
			log.info('Quote {quote} has been removed')
			await ctx.send(f'Quote removed\n> \"{quote["quote"]}\" - {quote["author"]}')
		else:
			log.warning(f'Quote failed to be removed from database due to unknown key: {quote_key}')
			await ctx.send(f'Could not find {quote_key} in the database')

	# Changes a quote in the database
	@q.command(aliases=['change'], brief='Edit a quote', description='Either replace a quote completely, only the author, or just the quote.', usage='[quote id] (author/quote) "[quote]" - [author]')  # assuming this server already has a database for them.
	@commands.has_permissions(administrator=True)
	async def edit(self, ctx: commands.Context, *args) -> None:  # the arg parser can do some weird stuff with quotation marks TODO wdym?!?!
		try:
			index = str(int(args[0]))  # check for impostor aka strings
		except:
			log.warning(f'Quote edit could not find a quote in the database with key: {args[0]}')  # we are returning from here.
			await ctx.send(f'Could not find {args[0]} in the database')
			return
		request, guild_id = args[1], str(ctx.guild.id)

		with open(f'storage/db/quotes/{guild_id}.json', 'r+', encoding='utf-8') as file:  # starting the file lock
			quotes = json.load(file)
			if index not in quotes:  # if the quote is not present we still want to be able to edit this specific index, will screw with the max function in q add
				quotes[index] = {'quote': '', 'author': '', 'remove_votes': [], 'remove_vetos': [], 'id': int(index)}
			if request == 'author':
				quotes[index]['author'] = ' '.join(args[2:])
			elif request == 'quote':
				quotes[index]['quote'] = ' '.join(args[2:])
			else:
				quote, author = self.split_quote(' '.join(ctx.message.content.split()[3:]))
				quotes[index]['quote'], quotes[index]['author'] = quote, author

			file.seek(0)
			json.dump(quotes, file, indent=4)
			file.truncate()
		await ctx.send(f'> {index}: \"{quotes[index]["quote"]}\" - {quotes[index]["author"]}')

	# Searches the quote database
	@q.command(brief='Search quote database', description='Search the quote database for a specific string.', usage='(quote/author) [query]')
	async def search(self, ctx: commands.Context, *, args):
		quotes, search_result = self.load_quotes(str(ctx.guild.id)), []
		search_request = args.split()[0].lower() if args.split()[0].lower() in ['quote', 'author'] else None
		log.debug(f'Searching with parameters: {args}')
		
		if search_request:
			log.debug(f'Searching through {search_request}s')
			search_key = ' '.join(args.split()[1:]).lower()
			for quote in quotes:
				if search_key in quotes[quote][search_request].lower():
					search_result.append(quotes[quote])
		else:
			log.debug('Searching through entire quote object')
			search_key = args.lower()
			for quote in quotes:
				if search_key in quotes[quote]['quote'].lower() + quotes[quote]['author'].lower():
					search_result.append(quotes[quote])

		await self.mass_quote(ctx, search_result)

	# Dumps all quotes
	@q.command(brief='Return all quotes', description='Return all quotes', usage='')
	async def all(self, ctx: commands.Context) -> None:
		quotes = self.load_quotes(str(ctx.guild.id))
		await self.mass_quote(ctx, list(quotes.values()))

	# Return the last few quotes
	@q.command(brief='Return the last few quotes', description='Return the last x quotes', usage='(amount)')
	async def last(self, ctx: commands.Context, arg: int = 10):
		quotes = self.load_quotes(str(ctx.guild.id))
		quotes = sorted(list(quotes.values()), key=lambda i: i['id'])
		
		try:
			arg = int(arg)
		except:
			arg = 10

		await self.mass_quote(ctx, quotes[-arg:])

	# Displays quote statistics
	@q.command(brief='Quote database statistics', description='Quote database statistics or ask for data on a specific quote', usage='[quote id]')
	async def stats(self, ctx: commands.Context, arg=None) -> None:
		quotes = self.load_quotes(str(ctx.guild.id))
		
		if arg == None:
			await ctx.send(f'Displaying database wide statistics\nAmount of quotes: {len(quotes)}\nEmpty quotes: `{", ".join([str(number) for number in range(0,max(map(lambda x: int(x), quotes.keys()))) if str(number) not in quotes])}`')
			return

		try:
			arg = str(int(arg))
			quote = quotes[arg]
			await ctx.send(f"```Quote: \"{quote['quote']}\"\nAuthor: {quote['author']}\nVotes: {len(quote['remove_votes'])}\nVetos: {len(quote['remove_vetos'])}```")
		except:
			await ctx.send('Sorry for the inconvenience, something went wrong.')
			log.warning(f'Could either not convert argument or its not present in the database. Key: {arg}')

	# Vote to delete a quote
	@q.command(brief='Vote to delete a quote', description='Vote to delete a quote', usage='[quote id]')
	async def vote(self, ctx: commands.Context, quote_id=None) -> None:
		guild_id, author_id, deleted = str(ctx.guild.id), ctx.author.id, False

		try:
			quote_id = str(int(quote_id))
		except:
			log.warning('Vote could not convert arg to an int. Key: {quote_id}')
			return

		with open(f'storage/db/quotes/{guild_id}.json', 'r+', encoding='utf-8') as file:
			quotes = json.load(file)
			if author_id not in quotes[quote_id]['remove_votes']:
				quotes[quote_id]['remove_votes'].append(author_id)
				if author_id in quotes[quote_id]['remove_vetos']:
					quotes[quote_id]['remove_vetos'].remove(author_id)
			if len(quotes[quote_id]['remove_votes']) - len(quotes[quote_id]['remove_vetos']) >= self.config['needed_votes']:
				del quotes[quote_id]
			file.seek(0)
			json.dump(quotes, file, indent=4)
			file.truncate()

		await ctx.send('Vote has been registered')  # purely based on the fact that we didn't crash :)
		if deleted:
			await ctx.send(f"Quote has been removed\n> {quotes[quote_id]['id']}: \"{quotes[quote_id]['quote']}\" - {quotes[quote_id]['author']}")

	# Veto to delete a quote
	@q.command(brief='Veto the deletion of a quote', description='Veto the deletion of a quote.', usage='[quote id]')
	async def veto(self, ctx: commands.Context, quote_id: str = None) -> None:
		guild_id, author_id = str(ctx.guild.id), ctx.author.id

		try:
			quote_id = str(int(quote_id))
		except:
			log.warning('Veto could not convert arg to an int. Key: {quote_id}')
			return

		with open(f'storage/db/quotes/{guild_id}.json', 'r+', encoding='utf-8') as file:
			quotes = json.load(file)
			if author_id not in quotes[quote_id]['remove_vetos']:
				quotes[quote_id]['remove_vetos'].append(author_id)
				if author_id in quotes[quote_id]['remove_votes']:
					quotes[quote_id]['remove_votes'].remove(author_id)
			file.seek(0)
			json.dump(quotes, file, indent=4)
			file.truncate()

		await ctx.send('Veto has been registered')
