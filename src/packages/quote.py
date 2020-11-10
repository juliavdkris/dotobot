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
from os import path, makedirs

# -------------------------> Main

def setup(bot):
	if not path.exists('storage/db/quotes'):
		makedirs('storage/db/quotes')
	if not path.isfile('storage/config/quotes.json'):
		log.critical(f'FILE NOT FOUND, could not find the quotes config file, setting up a template')
		with open('storage/config/quotes.json', 'w+', encoding='utf-8') as file:
			json.dump({'needed_votes': 0}, file, sort_keys=True, indent=4)
	log.info('Quotes module has been activated')
	bot.add_cog(Quotes(bot))

def teardown(bot):
	log.info('Quotes module has been deactivated')

class Quotes(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.config = self.load_config()

	def load_config(self):
		log.debug(f'config/quotes.json has been loaded')
		with open('storage/config/quotes.json', 'r', encoding='utf-8') as file:
			return json.load(file)

	def load_quotes(self, guild_id: str):  # returns quotes from the specific server
		log.debug(f'db/quotes/{guild_id}.json has been loaded')
		with open(f'storage/db/quotes/{guild_id}.json', 'r', encoding='utf-8') as file:
			return json.load(file)

	def split_quote(self, quote):
		REGEX = r'["“](.*)["”] ?- ?(.*)'
		m = re.search(REGEX, quote)
		return (m.group(1), m.group(2))

	async def quote(self, ctx, args):
		guild_key = str(ctx.guild.id)
		quotes = self.load_quotes(guild_key)
		try:
			args = args.split()[1]  # grab the key since we get here with a !q 123
			quote_key = str(int(args))  # check for impostor
			if quote_key not in quotes:
				raise Exception('key was not present in the dictionary')
		except:
			quote_key = choice(list(quotes.keys()))
		quote = quotes[quote_key]  # and otherwise we're gonna have to rewrite /shrug
		await ctx.send(f'> {quote_key}: \"{quote["quote"]}\" - {quote["author"]}')
		return

	async def mass_quote(self, ctx, quotes):
		quotes = sorted(quotes, key = lambda i: i['id'])
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

	@commands.group(aliases = ['quote'])
	async def q(self, ctx):
		if not path.isfile('storage/db/quotes/' + str(ctx.guild.id) + '.json'):
			with open('storage/db/quotes/' + str(ctx.guild.id) + '.json', 'w+', encoding='utf-8') as file:
				json.dump({}, file, sort_keys=True, indent=4)
		if ctx.invoked_subcommand is None:
			log.info(f'QUOTE User {ctx.author.name} has passed an invalid quote subcommand: {ctx.message.content}')
			await self.quote(ctx, ctx.message.content)
		else:
			log.info(f'QUOTE User {ctx.author.name} has called command:{ctx.invoked_subcommand}')

	@q.command()
	async def add(self, ctx, *, args = None):
		guild_id = str(ctx.guild.id)
		quote, author = self.split_quote(args)
		with open(f'storage/db/quotes/{guild_id}.json', 'r+', encoding = 'utf-8') as file:
			quotes = json.load(file)
			if len(quotes) == 0:  # custom check since it should add a quote
				nextid = 0
			else:
				nextid = max(map(lambda x: int(x), quotes.keys())) + 1
			quotes[str(nextid)] = {'quote': quote, 'author': author, 'remove_votes': [], 'remove_vetos': [], 'id': nextid}
			file.seek(0)
			json.dump(quotes, file, sort_keys=True, indent=4)
			file.truncate()

		log.info(f"QUOTE has been added; {nextid}: \"{quote}\" - {author}")
		await ctx.send(f'Quote added. Assigned ID: {nextid}')


	@q.command(aliases = ['del', 'delete'])
	@commands.has_permissions(administrator=True)
	async def remove(self, ctx, *, args = None):
		quote_key, guild_id, succes = str(int(args)), str(ctx.guild.id), False
		with open(f'storage/db/quotes/{guild_id}.json', 'r+', encoding = 'utf-8') as file:
			quotes = json.load(file)
			if quote_key in quotes:
				quote = quotes.pop(quote_key)
				succes = True
			file.seek(0)
			json.dump(quotes, file, sort_keys=True, indent=4)
			file.truncate()

		if succes:
			log.info('QUOTE {quote} has been removed')
			await ctx.send(f'Quote removed\n> \"{quote["quote"]}\" - {quote["author"]}')
		else:
			log.warning(f'QUOTE remove key could not be found in database. Key: {quote_key}')
			await ctx.send(f'Could not find {quote_key} in the database')

	@q.command(aliases = ['change'])  # assuming this server already has a database for them.
	@commands.has_permissions(administrator=True)
	async def edit(self, ctx, * args):  # the arg parser can do some weird stuff with quotation marks
		try:
			index = str(int(args[0]))  # check for impostor aka strings
		except:
			log.warning(f'QUOTE edit could not find a valid quote_key. Key: {args[0]}')  # we are returning from here.
			await ctx.send('The requested quote key could not be read')
			return
		request, guild_id = args[1], str(ctx.guild.id)

		with open(f'storage/db/quotes/{guild_id}.json', 'r+', encoding = 'utf-8') as file:  # starting the file lock
			quotes = json.load(file)
			if index not in quotes:  # if the quote is not present we still want to be able to edit this specific index, will screw with the max function in q add
				quotes[index] = {'quote': '', 'author': '', 'remove_votes': [], 'remove_vetos': [], 'id': int(index)}
			if request == 'author' or request == 'auteur':
				quotes[index]['author'] = ' '.join(args[2:])
			elif request == 'quote':
				quotes[index]['quote'] = ' '.join(args[2:])
			else:
				quote, author = self.split_quote(' '.join(ctx.message.content.split()[3:]))
				quotes[index]['quote'], quotes[index]['author'] = quote, author

			file.seek(0)
			json.dump(quotes, file, sort_keys=True, indent=4)
			file.truncate()
		await ctx.send(f'> {index}: \"{quotes[index]["quote"]}\" - {quotes[index]["author"]}')

	@q.command()
	async def search(self, ctx, *, args):
		quotes, found_quotes = self.load_quotes(str(ctx.guild.id)), []

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
		quotes = self.load_quotes(str(ctx.guild.id))
		await self.mass_quote(ctx, list(quotes.values()))

	@q.command()
	async def last(self, ctx, arg = 0):
		quotes = self.load_quotes(str(ctx.guild.id))
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
	async def stats(self, ctx, arg = None):
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

	@q.command()
	async def vote(self, ctx, quote_id = None):
		guild_id, author_id, deleted =  str(ctx.guild.id), ctx.author.id, False
		try:
			quote_id = str(int(quote_id))
		except:
			log.warning('Vote could not convert arg to an int. Key: {quote_id}')
			return

		with open(f'storage/db/quotes/{guild_id}.json', 'r+', encoding = 'utf-8') as file:
			quotes = json.load(file)
			if author_id not in quotes[quote_id]['remove_votes']:
				quotes[quote_id]['remove_votes'].append(author_id)
				if author_id in quotes[quote_id]['remove_vetos']:
					quotes[quote_id]['remove_vetos'].remove(author_id)
			if len(quotes[quote_id]['remove_votes']) - len(quotes[quote_id]['remove_vetos']) >= self.config['needed_votes']:
				del quotes[quote_id]
			file.seek(0)
			json.dump(quotes, file, sort_keys=True, indent=4)
			file.truncate()

		await ctx.send('Vote has been registered')  # purely based on the fact that we didn't crash :)
		if deleted:
			await ctx.send(f"Quote has been removed\n> {quotes[quote_id]['id']}: \"{quotes[quote_id]['quote']}\" - {quotes[quote_id]['author']}")

	@q.command()
	async def veto(self, ctx, quote_id = None):
		guild_id, author_id = str(ctx.guild.id), ctx.author.id
		try:
			quote_id = str(int(quote_id))
		except:
			log.warning('Veto could not convert arg to an int. Key: {quote_id}')
			return

		with open(f'storage/db/quotes/{guild_id}.json', 'r+', encoding = 'utf-8') as file:
			quotes = json.load(file)
			if author_id not in quotes[quote_id]['remove_vetos']:
				quotes[quote_id]['remove_vetos'].append(author_id)
				if author_id in quotes[quote_id]['remove_votes']:
					quotes[quote_id]['remove_votes'].remove(author_id)
			file.seek(0)
			json.dump(quotes, file, sort_keys=True, indent=4)
			file.truncate()

		await ctx.send('Veto has been registered')