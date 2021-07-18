# -------------------------> Dependencies

# Setup python logging
import logging
log = logging.getLogger(__name__)

# Import libraries
import discord
from discord.ext import commands
from steam.webapi import WebAPI
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
        self.steam_api = WebAPI(key=getenv('STEAM_KEY')) # maybe throw this in config

    def load_config(self):
        log.debug('config/users.json has been loaded')
        with open('storage/config/users.json', 'r', encoding='utf-8') as file:
            return json.load(file)

    @commands.command(brief='Invite people to play a game', description='Scans Steam inventories for people to play games with', usage='[game]')
    async def letsplay(self, ctx: commands.Context, *, game_name: str):
        log.info(f'Received letsplay command from user {ctx.author.name}')

        
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
            processor=lambda x: x['name'].lower(),
            score_cutoff=75
        )

        # If no matches found
        if target_game == None:
            similar = process.extractOne(
                query={ 'name': game_name },
                choices=games,
                processor=lambda x: x['name'].lower()
            )[0]['name']

            await ctx.send(f'No such games found in your library! Did you mean {similar}?')

        # Else ping others
        else:
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

                if target_game[0]['appid'] in [game['appid'] for game in games]:
                    message += f"<@!{discord_id}> "
            
            await ctx.send(message)



