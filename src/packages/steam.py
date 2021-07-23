# -------------------------> Dependencies

# Setup python logging
import logging
log = logging.getLogger(__name__)

# Import libraries
from steam import steamid
from steam.webapi import WebAPI
from discord.ext import commands
from fuzzywuzzy import process

import json
from os import getenv
from dotenv import load_dotenv
load_dotenv()

# -------------------------> Client

def setup(bot):
    log.info('Steam module has been activated')
    bot.add_cog(Steam(bot))

def teardown(bot):
    log.info('Steam module has been deactivated')

class Steam(commands.Cog, name='Steam', description='Interface with steam'):
    def __init__(self, bot):
        self.bot = bot
        self.users = self.load_config()
        self.steam_api = WebAPI(key=getenv('STEAM_KEY'))

    # Dumps config into self.users
    def load_config(self):
        log.debug('config/users.json has been loaded')
        with open('storage/config/users.json', 'r', encoding='utf-8') as file:
            return json.load(file)

    # Dumps self.users into config
    def update_config(self):
        log.debug('config/users.json has been updated')
        with open('storage/config/users.json', 'w', encoding='utf-8') as file:
            json.dump(self.users, file, indent=4)

    # Matches userinput to find a game in steamlibrary and pings other users that have that game
    @commands.command(brief='Invite people to play a game', description='Scans Steam inventories for people to play games with', usage='[game]')
    async def letsplay(self, ctx: commands.Context, *, game_name: str):
        log.info(f'Received letsplay command from user {ctx.author.name}')

        # Check if user is known
        if str(ctx.author.id) not in self.users.keys():
            await ctx.send('I dont know your steamID yet! What is your steamprofile URL?')
            while True:
                url = await self.bot.wait_for('message', check=lambda msg: msg.author == ctx.author, timeout=180)
                steam_id = steamid.steam64_from_url(url.content)

                if steam_id != None or url.content == 'go away':
                    break
                await ctx.send('That was not a valid url... Please try again or type `go away`')
            
            self.users[str(ctx.author.id)] = { 'steam_id': steam_id }
            self.update_config()
                
        # Fetch caller inventory
        games = self.steam_api.call(
            'IPlayerService.GetOwnedGames',
            steamid=self.users[str(ctx.author.id)]['steam_id'],
            include_appinfo=True,
            include_played_free_games=True,
            appids_filter=False,
            include_free_sub=False,
            skip_unvetted_apps=False
        )['response']['games']

        target_game = process.extractOne(
            query={ 'name': game_name },
            choices=games,
            processor=lambda x: x['name'].lower()
        )

        # If no matches found
        if target_game[1] < 75:
            await ctx.send(f'No such games found in your library! Did you mean {target_game[0]["name"]}?')

        # Else ping others
        else:
            members = [str(member.id) for member in ctx.channel.members]
            message = f'We\'re playing {target_game[0]["name"]}. Get your ass over here\n'
            for discord_id, user in self.users.items():
                games = self.steam_api.call(
                    'IPlayerService.GetOwnedGames',
                    steamid=user['steam_id'],
                    include_appinfo=True,
                    include_played_free_games=True,
                    appids_filter=False,
                    include_free_sub=False,
                    skip_unvetted_apps=False
                )['response']['games']

                if target_game[0]['appid'] in [game['appid'] for game in games] and discord_id in members:
                    message += f"<@!{discord_id}>"
            
            await ctx.send(message)
            