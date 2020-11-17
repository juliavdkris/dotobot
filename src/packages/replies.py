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
import asyncio
import os.path

# -------------------------> Main


def setup(bot):
	log.info('Replies module has been activated')
	bot.add_cog(Replies(bot))


def teardown(bot):
	log.info('Replies module has been deactivated')


class Replies(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.config = self.load_config()
		self.f_flag = True

	def load_config(self):
		log.debug(f'config/replies.json has been loaded')
		with open('storage/config/replies.json', 'r', encoding='utf-8') as file:
			return json.load(file)

	async def flag_checker(self, content):
		content = content.split(' ')
		mod_flag, abuse_flag = False, False
		for mod in self.config['peace_items'][0]:
			if mod in content:
				mod_flag = True
		for abuse in self.config['peace_items'][1]:
			if abuse in content:
				abuse_flag = True
		return (abuse_flag + mod_flag)

	async def peace_in_our_time(self, content, msg):
		flag = await self.flag_checker(content)
		if flag == 0:
			return False
		elif flag == 2:
			await msg.delete()
			await msg.channel.send(choice(self.config['peace_reactions']))
			return True
		try:
			log.debug('waiting on multi line parse')
			msg2 = await self.bot.wait_for('message', check=lambda message: message.author == msg.author, timeout=15)
			content += ' ' + msg2.content.lower()
			if await self.flag_checker(content) == 2:
				await msg.delete()
				await msg.channel.send(choice(self.config['peace_reactions']))
				await msg2.delete()
				return True
		except:
			pass
		return False

	async def update(self):
		self.config = self.load_config()
		self.f_flag = True
		log.info(f'Replies ran an update')

	@commands.Cog.listener()
	async def on_message(self, msg):
		if msg.author.id != self.bot.user.id:
			msgcontent, c = msg.content.lower(), msg.channel
			if await self.peace_in_our_time(msgcontent, msg):  # corresponding message was deleted no need for reactions. command can still be executed :/
				return

			if msgcontent == 'f' and self.f_flag:
				self.f_flag = False
				await c.send('F')
				await asyncio.sleep(15)
				self.f_flag = True

			elif 'kom voice' in msgcontent:
				with open('storage/static/kom_voice.png', 'br') as fp:
					await c.send(file=discord.File(fp, 'kom_voice.png'))

			elif 'shipit' in msgcontent.replace(' ', ''):
				await c.send("https://cdn.discordapp.com/emojis/727923735239196753.gif?v=1")

			try:
				REGEX = r'(?:^|[\[ -@]|[\[-`]|[{-~]])(' + '|'.join(self.config['weed_items']) + r')(?:$|[\[ -@]|[\[-`]|[{-~]])'  # Just match anything not a letter to be honest
				if m := re.search(REGEX, msgcontent):
					for emoji in self.config['weed_reactions']:
						await msg.add_reaction(emoji)
					log.info(f'Found the following for weed: {m.group(1)}')
			except:
				pass

			try:
				REGEX = r'(?:^|[\[ -@]|[\[-`]|[{-~]])(' + '|'.join(self.config['funny_items']) + r')(?:$|[\[ -@]|[\[-`]|[{-~]])'  # Just match anything not a letter to be honest
				if m := re.search(REGEX, msgcontent):
					for emoji in self.config['funny_reactions']:
						await msg.add_reaction(emoji)
					log.info(f'Found the following for nice: {m.group(1)}')
			except:
				pass

	@commands.command()
	async def what(self, ctx):
		with open('storage/static/what.png', 'br') as fp:
			await ctx.send(file=discord.File(fp, 'what.png'))
