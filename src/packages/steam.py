# -------------------------> Dependencies

# Setup python logging
import logging
log = logging.getLogger(__name__)

# Import libraries
from copy import deepcopy
from discord.ext import commands
import json
from os.path import basename
import re
from steam import steamid
from steam.webapi import WebAPI

from os import getenv
from dotenv import load_dotenv
load_dotenv()

# -------------------------> Main

def setup(bot: commands.Bot) -> None:
	bot.add_cog(Steam(bot))
	log.info(f'Module has been activated: {basename(__file__)}')

def teardown(bot: commands.Bot) -> None:
	log.info(f'Module has been de-activated: {basename(__file__)}')

# Uses a two-row algorithm to calculate the levenshtein distance between two strings
def levenshtein(a: str, b: str) -> int:
    prev = [i for i in range(len(b) + 1)]
    curr = [0 for _ in range(len(b) + 1)]

    for i in range(len(a)):
        curr[0] = i + 1
        for j in range(len(b)):
            del_cost = prev[j + 1] + 1
            ins_cost = curr[j] + 1
            sub_cost = prev[j]
            if a[i] != b[j]:
                sub_cost += 1

            curr[j + 1] = min(del_cost, ins_cost, sub_cost)

        for j in range(len(curr)):
            prev[j] = curr[j]

    return 100 - 100 * prev[len(b)] // max(len(a), len(b))

# Picks a single game from a list of games, using fuzzy matching
def choose_one(query: dict, collection: list) -> dict:
    query = query.lower()
    best_match = None
    best_ratio = None

    for item in collection:
        ratio = levenshtein(query, item['alias'].lower())
        if best_ratio == None or ratio > best_ratio:
            best_ratio = ratio
            best_match = item

    return { 'match': best_match, 'ratio': best_ratio }



class Steam(commands.Cog, name='Steam', description='Interface with steam'):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.users = self.load_config()
        self.steam_api = WebAPI(key=getenv('STEAM_KEY'))

    # Updates config
    async def update(self) -> None:
        self.config = self.load_config()
        log.info(f'Steam ran an update')

    # Dumps config into self.users
    def load_config(self):
        log.debug('Loading data from config/users.json...')
        with open('storage/config/users.json', 'r', encoding='utf-8') as file:
            return json.load(file)

    # Dumps self.users into config
    def dump_config(self):
        log.debug('Dumping data in config/users.json...')
        with open('storage/config/users.json', 'w', encoding='utf-8') as file:
            json.dump(self.users, file, indent=4)

    # Matches userinput to find a game in steamlibrary and pings other users that have that game
    @commands.command(brief='Invite people to play a game', description='Scans Steam inventories for people to play games with', usage='[game]')
    async def letsplay(self, ctx: commands.Context, *, game_name: str) -> None:
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
        result = self.steam_api.call(
            'IPlayerService.GetOwnedGames',
            steamid=self.users[str(ctx.author.id)]['steam_id'],
            include_appinfo=True,
            include_played_free_games=True,
            appids_filter=False,
            include_free_sub=False,
            skip_unvetted_apps=False
        )['response']['games']

        # Creates aliases of every game to include searches like 'drg' or 'csgo'
        games = []
        for game in result:
            # Create game
            games.append({
                'name': game['name'],
                'appid': game['appid'],
                'alias': game['name']
            })

            # Create alias (this isnt suuuuper failproof)
            games.append({
                'name': game['name'],
                'appid': game['appid'],
                'alias': ''.join([word[0] for word in re.findall(r"[\w]+", game['name'])])
            })

        # Match input to games
        target_game = choose_one(game_name, games)

        # If no matches found
        if target_game['ratio'] < 85:
            await ctx.send(f'No such games found in your library! Did you mean {target_game["match"]["name"]}?')

        # Else ping others
        else:
            members = [str(member.id) for member in ctx.channel.members]
            message = f'We\'re playing {target_game["match"]["name"]}. Get your ass over here\n'
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

                if target_game['match']['appid'] in [game['appid'] for game in games] and discord_id in members:
                    message += f'<@!{discord_id}fuckoff>'
            
            await ctx.send(message)
