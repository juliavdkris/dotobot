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

# -------------------------> Main

def setup(bot):
	log.info('Replies module has been activated')
	bot.add_cog(Replies(bot))

def teardown(bot):
	log.info('Replies module has been deactivated')

class Replies(commands.Cog, description='Module that replies to you in chat'):
	def __init__(self, bot):
		self.bot = bot
		self.config = self.load_config()
		self.f_flag = True

	def load_config(self):
		log.debug('config/replies.json has been loaded')
		with open('storage/config/replies.json', 'r', encoding='utf-8') as file:
			return json.load(file)
	
	async def update(self):
		self.config = self.load_config()
		self.f_flag = True
		log.info(f'Replies ran an update')

	def mod_abuse_detector(self, content):
		mod_flag, abuse_flag = False, False
		for mod in self.config['peace_items'][0]:
			if mod in content:
				mod_flag = True
		for abuse in self.config['peace_items'][1]:
			if abuse in content:
				abuse_flag = True
		return abuse_flag and mod_flag

	async def peace_in_our_time(self, content: str, msg: discord.Message, previousMessages = {}):
		if self.mod_abuse_detector(content):
			await msg.channel.send(choice(self.config['peace_reactions']))
			await msg.delete()
			return True
		previous = previousMessages[msg.author.id] if msg.author.id in previousMessages else None
		if previous:
			if self.mod_abuse_detector(content + ' ' + previous.content.lower()):
				await msg.channel.send(choice(self.config['peace_reactions']))
				await msg.delete()
				await previous.delete()
				del previousMessages[msg.author.id]
				return True
		previousMessages[msg.author.id] = msg
		return False

	@commands.Cog.listener()
	async def on_message(self, msg):
		if msg.author.id != self.bot.user.id:
			content, channel = msg.content.lower(), msg.channel

			# If hatespeach is detected, no replies are to be sent
			if await self.peace_in_our_time(content, msg):
				return

			# Reply with F to pay respects
			if content == 'f' and self.f_flag:
				self.f_flag = False
				await channel.send('F')
				await asyncio.sleep(15)
				self.f_flag = True

			# Rock and stone
			elif content == 'v':
				await channel.send(choice(self.config['salute_reactions']))

			# Press X to doubt
			elif content == 'x':
				with open('storage/static/doubt.png', 'br') as fp:
					await channel.send(file=discord.File(fp, 'doubt.png'))

			# Invite people to voice
			elif 'kom voice' in content:
				with open('storage/static/kom_voice.png', 'br') as fp:
					await channel.send(file=discord.File(fp, 'kom_voice.png'))

			# git push -f origin master
			elif 'shipit' in content.replace(' ', ''):
				await channel.send("https://cdn.discordapp.com/emojis/727923735239196753.gif?v=1")

			# Check for 420
			try:
				REGEX = r'(?:^|[\[ -@]|[\[-`]|[{-~]])(' + '|'.join(self.config['weed_items']) + r')(?:$|[\[ -@]|[\[-`]|[{-~]])'  # Just match anything not a letter to be honest
				if m := re.search(REGEX, content):
					for emoji in self.config['weed_reactions']:
						await msg.add_reaction(emoji)
					log.info(f'Found the following for weed: {m.group(1)}')
			except:
				pass
			
			# Check for 69
			try:
				REGEX = r'(?:^|[\[ -@]|[\[-`]|[{-~]])(' + '|'.join(self.config['funny_items']) + r')(?:$|[\[ -@]|[\[-`]|[{-~]])'  # Just match anything not a letter to be honest
				if m := re.search(REGEX, content):
					for emoji in self.config['funny_reactions']:
						await msg.add_reaction(emoji)
					log.info(f'Found the following for nice: {m.group(1)}')
			except:
				pass

	@commands.command(brief='What', description='What', usage='')
	async def what(self, ctx):
		with open('storage/static/what.png', 'br') as fp:
			await ctx.send(file=discord.File(fp, 'what.png'))
