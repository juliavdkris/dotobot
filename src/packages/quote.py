# -------------------------> Dependencies

# Setup python logging
import logging
log = logging.getLogger(__name__)

# Import libraries
import discord
from discord.ext import commands
import json
from random import choice
import re
import os.path

# -------------------------> Main


def setup(bot):
	if not os.path.isfile('storage/quotes_config.json'):
		log.critical(f'FILE NOT FOUND, could not find the quotes_config file, setting up a template')
		with open('storage/quotes_config.json', 'w+', encoding='utf-8') as file:
			json.dump({'needed_votes': 0}, file, sort_keys=True, indent=4)
	if not os.path.isfile('storage/quotes.json'):
		log.critical(f'FILE NOT FOUND, could not find the quotes file, setting up a template')
		with open('storage/quotes.json', 'w+', encoding='utf-8') as file:
			json.dump({}, file, sort_keys=True, indent=4)
	log.info('Quotes module has been activated')
	bot.add_cog(Quotes(bot))


def teardown(bot):
	log.info('Quotes module has been deactivated')


class Quotes(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.config = self.load_config()

	def load_config(self):
		log.debug(f'quotes_config.json has been loaded')
		with open('storage/quotes_config.json', 'r', encoding='utf-8') as file:
			return json.load(file)

	def store_quotes(self, quotes):
		log.debug(f'quotes.json has been saved')
		with open('storage/quotes.json', 'w', encoding='utf-8') as file:
			json.dump(quotes, file, sort_keys=True, indent=4)
		return

	def load_quotes(self):
		log.debug(f'quotes.json has been loaded')
		with open('storage/quotes.json', 'r', encoding='utf-8') as file:
			return json.load(file)

	def split_quote(self, quote):
		REGEX = r'["“](.*)["”] ?- ?(.*)'
		m = re.search(REGEX, quote)
		return (m.group(1), m.group(2))

	def data_base_present(self, quotes, guild_key):
		if guild_key not in quotes or list(quotes[guild_key].keys()) == 0:
			log.warning(f'Guild was not found in the database or the database was empty. Key: {guild_key}')
			return False
		return True

	async def quote(self, ctx, args):
		quotes = self.load_quotes()
		guild_key = str(ctx.guild.id)
		if not self.data_base_present(quotes, guild_key):
			await ctx.send('This server has no quote database or it is empty')
			return
		try:
			args = args.split()[1]  # grab the key since we get here with a !q 123
			quote_key = str(int(args))  # check for impostor
			if quote_key not in quotes[guild_key]:
				raise Exception('key was not present in the dictionary')
		except:
			key_list = list(quotes[guild_key].keys())
			key_list.pop(
			    key_list.index('next_id')
			)  # weird hack and should be solved differently, conflicts with the choice wherein choice would pick this option.
			quote_key = choice(
			    key_list
			)  # possible solution is to hide all the quotes behind a 'quote' key but I think the conflict won't arise too much
		quote = quotes[guild_key][quote_key]  # and otherwise we're gonna have to rewrite /shrug
		await ctx.send(f'> {quote_key}: \"{quote["quote"]}\" - {quote["author"]}')
		return

	async def load_guild_quotes(self, ctx):
		quotes, guild_key = self.load_quotes(), str(ctx.guild.id)
		if not self.data_base_present(quotes, guild_key):
			return
		quotes = quotes[guild_key]
		del quotes['next_id']
		return quotes

	async def mass_quote(self, ctx, quotes):
		quotes = sorted(quotes, key=lambda i: i['id'])
		quote_brackets, qmsg = '```', '```'
		if len(quotes) == 0:
			await ctx.send('No entries match the search')
		for quote in quotes:
			qmsg += f"{quote['id']}: \"{quote['quote']}\" - {quote['author']}\n"
			if len(qmsg) >= 1800:
				await ctx.send(qmsg + quote_brackets)
				qmsg = quote_brackets
		await ctx.send(qmsg + quote_brackets)

	async def update(self):
		self.config = self.load_config()
		log.info(f'Quotes ran an update')

	@commands.group(aliases=['quote'])
	async def q(self, ctx):
		if ctx.invoked_subcommand is None:
			log.info(f'QUOTE User {ctx.author.name} has passed an invalid quote subcommand: {ctx.message.content}')
			await self.quote(ctx, ctx.message.content)
		else:
			log.info(f'QUOTE User {ctx.author.name} has called command:{ctx.invoked_subcommand}')

	@q.command()
	async def add(self, ctx, *, args=None):
		quotes, guild_key = self.load_quotes(), str(ctx.guild.id)
		if guild_key not in quotes:  # custom check since it should add a quote
			log.info(f'QUOTE Database created for {ctx.guild.name}')
			quotes[guild_key] = {'next_id': 0}
		quote, author = self.split_quote(args)

		quotes[guild_key][str(quotes[guild_key]['next_id'])] = {
		    'quote': quote,
		    'author': author,
		    'remove_votes': [],
		    'remove_vetos': [],
		    'id': quotes[guild_key]['next_id']
		}
		log.info(f"QUOTE has been added; {quotes[guild_key]['next_id']}: \"{quote}\" - {author}")
		await ctx.send(f'Quote added. Assigned ID: {quotes[guild_key]["next_id"]}')
		quotes[guild_key]['next_id'] += 1
		self.store_quotes(quotes)

	@q.command(aliases=['del', 'delete'])
	async def remove(self, ctx, *, args=None):
		quote_key, quotes, guild_key = str(int(args)), self.load_quotes(), str(ctx.guild.id)
		if quote_key in quotes[guild_key]:
			quote = quotes[guild_key].pop(quote_key)
			log.info('QUOTE {quote} has been removed')
			await ctx.send(f'Quote removed\n> \"{quote["quote"]}\" - {quote["author"]}')
		else:
			log.warning(f'QUOTE remove key could not be found in database. Key: {quote_key}')
			await ctx.send(f'Could not find {quote_key} in the database')
		self.store_quotes(quotes)

	@q.command(aliases=['change'])
	async def edit(self, ctx, *args):  # the arg parser can do some weird stuff with quotation marks
		quotes, guild_key = self.load_quotes(), str(ctx.guild.id)
		if not self.data_base_present(quotes, guild_key) or len(args) == 0:
			return
		log.info(f'QUOTE edit with following parameters: {args}')

		index = ''
		try:
			index = str(int(args[0]))  # check for impostor aka strings
		except:
			log.warning(f'QUOTE edit could not find a valid quote_key. Key: {args[0]}')  # we are returning from here.
			await ctx.send('The requested quote key could not be read')
			return

		request = args[1]
		if request == 'author' or request == 'auteur':
			quotes[guild_key][index]['author'] = ' '.join(args[2:])
		elif request == 'quote':
			quotes[guild_key][index]['quote'] = ' '.join(args[2:])
		else:
			print(ctx.message.content)
			quote, author = self.split_quote(' '.join(ctx.message.content.split()[3:]))
			quotes[guild_key][index]['quote'], quotes[guild_key][index]['author'] = quote, author

		await ctx.send(f'> {index}: \"{quotes[guild_key][index]["quote"]}\" - {quotes[guild_key][index]["author"]}')
		self.store_quotes(quotes)

	@q.command()
	async def search(self, ctx, *, args):
		quotes, found_quotes = await self.load_guild_quotes(ctx), []

		log.info(f'QUOTE search with following parameters: {args}')
		search_request = args.split()[0].lower() if args.split()[0].lower() in ['quote', 'author'] else None
		if search_request:
			log.info(f'searching through {search_request}s')
			search_key = ' '.join(args.split()[1:]).lower()
			for quote in quotes:
				if search_key in quotes[quote][search_request].lower():
					found_quotes.append(quotes[quote])
		else:
			log.info('searching through entire quote object')
			search_key = args.lower()
			for quote in quotes:
				if search_key in quotes[quote]['quote'].lower() + quotes[quote]['author'].lower():
					found_quotes.append(quotes[quote])
		await self.mass_quote(ctx, found_quotes)

	@q.command()
	async def all(self, ctx):
		quotes = await self.load_guild_quotes(ctx)
		await self.mass_quote(ctx, list(quotes.values()))

	@q.command()
	async def last(self, ctx, arg=0):
		quotes = await self.load_guild_quotes(ctx)
		quotes = list(quotes.values())
		if not arg:
			arg = 10
		try:
			arg = int(arg)
		except:
			await ctx.send('Could not read supplied integer')
			log.warning(f"QUOTE last could not read {arg}")
			return
		await self.mass_quote(ctx, quotes[-arg:])

	@q.command()
	async def stats(self, ctx, arg=None):
		quotes = await self.load_guild_quotes(ctx)
		try:
			arg = str(int(arg))
			quote = quotes[arg]
			await ctx.send(
			    f"```Quote: \"{quote['quote']}\"\nAuthor: {quote['author']}\nVotes: {len(quote['remove_votes'])}\nVetos: {len(quote['remove_vetos'])}```"
			)
		except:
			await ctx.send('Sorry for the inconvenience, something went wrong.')
			log.warning(f'Could either not convert argument or its not present in the database. Key: {arg}')

	@q.command()
	async def vote(self, ctx, quote_id=None):
		quotes, guild_key, author_id = self.load_quotes(), str(ctx.guild.id), ctx.author.id
		if not self.data_base_present(quotes, guild_key):
			return
		try:
			quote_id = str(int(quote_id))
		except:
			log.warning('Vote could not convert arg to an int. Key: {quote_id}')
			return
		if author_id not in quotes[guild_key][quote_id]['remove_votes']:
			quotes[guild_key][quote_id]['remove_votes'].append(author_id)
			if author_id in quotes[guild_key][quote_id]['remove_vetos']:
				quotes[guild_key][quote_id]['remove_vetos'].remove(author_id)
		await ctx.send('Vote has been registered')
		if len(quotes[guild_key][quote_id]['remove_votes']) - len(quotes[guild_key][quote_id]['remove_vetos']
		                                                         ) >= self.config['needed_votes']:
			await ctx.send(
			    f"Quote has been removed\n> {quotes[guild_key][quote_id]['id']}: \"{quotes[guild_key][quote_id]['quote']}\" - {quotes[guild_key][quote_id]['author']}"
			)
			del quotes[guild_key][quote_id]
		self.store_quotes(quotes)

	@q.command()
	async def veto(self, ctx, quote_id=None):
		quotes, guild_key, author_id = self.load_quotes(), str(ctx.guild.id), ctx.author.id
		if not self.data_base_present(quotes, guild_key):
			return
		try:
			quote_id = str(int(quote_id))
		except:
			log.warning('Veto could not convert arg to an int. Key: {quote_id}')
			return
		if author_id not in quotes[guild_key][quote_id]['remove_vetos']:
			quotes[guild_key][quote_id]['remove_vetos'].append(author_id)
			if author_id in quotes[guild_key][quote_id]['remove_votes']:
				quotes[guild_key][quote_id]['remove_votes'].remove(author_id)
		await ctx.send('Veto has been registered')
		self.store_quotes(quotes)

	@q.command()
	async def test(self, ctx):
		await ctx.send('test complete')