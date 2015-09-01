import json
from riot_api import get_acs_info
import riot_api
import xml.etree.ElementTree
import time
import datetime
from contextlib import closing
import build_parser

# Come on riot don't look please
def do_magic(connect_db, date):
    '''
        So the only way to get this kind of data (unless you manually write it)
        is by using two unofficial official riot apis: Swagger API and ACS
        Swagger is super cool, and is the esports API. THis is how we find all the games
        
        ACS is basically teh equivalent of the official Riot API, but sadly has
        access to the pro game match histories that we normally can't see.
    '''
    esports_api = "http://na.lolesports.com/api/"
    with closing(connect_db) as db:
        # So what we do is grab a week from the Riot site.
        programming = get_acs_info(esports_api + "/programmingWeek/" + date + "/1.json")
        p_blocks = json.loads(programming.read())["programming_block"]
        for p in p_blocks:
            # For each series in that week, we basically grab that series' xml page and
            # Start getting the match data
            block = get_acs_info(esports_api + "programming/" + p + ".xml?expand_matches=1").read()
            block_tree = xml.etree.ElementTree.fromstring(block)
            print block
            league_id = block_tree.find('leagueId').text
            if league_id.isdigit() is False:
                continue
            l_id = int(league_id)
            
            # You have to do these checks because
            # Riot includes unrelated stuff like PTL
            if block_tree.find('matches') is not None:
                block_tree = block_tree.find('matches')
                if block_tree.find('item') is not None:
                    # At this point, we basically get the team names
                    # Because the Blue and Red Side are incorrect on
                    # The other pages, so what's the point of getting
                    # Repetitive info.
                    block_tree = block_tree.find('item')
                    teams = []
                    contestants = block_tree.find('contestants')
                    for contestant in contestants:
                        teams.append(contestant.find('name').text)
                    # Sometimes, this relevant data is still missing
                    # Skip ittttt if so.
                    if block_tree.find('gamesInfo') is not None:
                        games = block_tree.find('gamesInfo')
                        for game in games:
                            game_info = get_acs_info(esports_api + "/game/" + game.find('id').text + ".xml")
                            game_tree = xml.etree.ElementTree.fromstring(game_info.read())
                            acs_url = game_tree.find('legsUrl')
                            game_number = game_tree.find('gameNumber').text
                            # Cant do anything without this.
                            # Means we don't get LPL games. RIP
                            if acs_url.text is not None:
                                add_match(db, acs_url.text, teams, game_number, l_id)
                            else:
                                continue
                    else:
                        continue
                else:
                    continue
            else:
                continue
 
'''
    This game just takes that information, and adds it to our database.
    That way, we never have to talk to ACS/Swagger API again
''' 
def add_match(db, url, teams, game_number, region):            
    timeline_url = riot_api.get_timeline_url(url)
    md = json.loads(riot_api.get_acs_info(url).read())
    id = md['gameId']
    date = datetime.datetime.fromtimestamp(md['gameCreation']/1000)
    is_json = json.loads(riot_api.get_acs_info(timeline_url).read())['frames']
    item_sets = json.dumps(build_parser.get_build_steps(is_json))
    participants = md['participants']
    for player in participants:
        info = {}
        if 'masteries' in player:
            del player['masteries']
        if 'runes' in player:
            del player['runes']
        if 'timeline' in player:
            del player['timeline']
        if 'highestAchievedSeasonTier' in player:
            del player['highestAchievedSeasonTier']
        info['win'] = player['stats']['win']
        info['item0'] = player['stats']['item0']
        info['item1'] = player['stats']['item1']
        info['item2'] = player['stats']['item2']
        info['item3'] = player['stats']['item3']
        info['item4'] = player['stats']['item4']
        info['item5'] = player['stats']['item5']
        info['item6'] = player['stats']['item6']
        info['kills'] = player['stats']['kills']
        info['deaths'] = player['stats']['deaths']
        info['assists'] = player['stats']['assists']
        del player['stats']
        player['stats'] = info  
    participantIds = json.dumps(md['participantIdentities'])
    participants = json.dumps(participants)
    db.execute('insert into matches (id, time_stamp, item_sets, participants, participantIds, game_number, teams, region_id) values (?, ?, ?, ?, ?, ?, ?,?)',
             [id, date.isoformat(), item_sets, participants, participantIds, int(game_number), json.dumps(teams), region])
    db.commit()