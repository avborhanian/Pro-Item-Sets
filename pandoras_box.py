import json
from riot_api import get_acs_info
import riot_api
import time
import datetime
from contextlib import closing
import build_parser
import lolitemsets


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
        programming_json = json.loads(programming.read())
        if "programming_block" not in programming_json:
            return
        p_blocks = programming_json["programming_block"]
        for p in p_blocks:
            print "Trying out " + str(p)
            # For each series in that week, we basically grab that series' xml page and
            # Start getting the match data
            block = get_acs_info(esports_api + "programming/" + p + ".json?expand_matches=1")
            block_tree = json.loads(block.read())
            if "leagueId" in block_tree:
                league_id =  block_tree["leagueId"]
                if league_id.isdigit is False or len(league_id) == 0:
                    print 'League ID isn\'t a digit'
                    continue
            else:
                continue
            region_id = 0
            try:
                region_id = int(block_tree["leagueId"])
            except:
                continue
            print 'Got a real id! Region id is ' + str(region_id)

            if 'week' not in block_tree:
                continue
            league_week = block_tree['week']
            # You have to do these checks because
            # Riot includes unrelated stuff like PTL
            if 'matches' in block_tree:
                block_tree = block_tree['matches'][0]
                # At this point, we basically get the team names
                # Because the Blue and Red Side are incorrect on
                # The other pages, so what's the point of getting
                # Repetitive info.
                teams = []
                if 'contestants' not in block_tree:
                    break
                contestants = block_tree['contestants']
                for contestant in contestants:
                    teams.append(contestants[contestant])
                # Sometimes, this relevant data is still missing
                # Skip ittttt if so.
                added_match = False
                if 'gamesInfo' in block_tree:
                    games = block_tree['gamesInfo']
                    print 'We are working on some games!'
                    for game in games:
                        print game
                        game_info = get_acs_info(esports_api + "/game/" + games[game]['id'] + ".json")
                        game_tree = json.loads(game_info.read())
                        acs_url = game_tree['legsUrl']
                        game_number = game_tree['gameNumber']
                        winner_id = int(game_tree['winnerId'])
                        players = game_tree['players']
                        # Cant do anything without this.
                        # Means we don't get LPL games. RIP
                        if acs_url is not None and type(acs_url) is not bool:
                            added_match = True
                            add_match(db, acs_url, teams, game_number, winner_id, players, p)
                        else:
                            print "No ACS URL"
                            break
                    if added_match is True:
                        add_match_details(db, int(p), teams[0], teams[1], league_week, region_id)
                        for i in range(0, 2):
                            add_team(db, teams[i]['id'], teams[i]['name'],  teams[i]['logoURL'])
                else:
                    print 'gamesInfo not in block_tree'
                    continue    
            else:
                print 'matches not in block_tree'
                continue
 
'''
def new_api_magic(db):
    schedule = json.loads(riot_api.get_acs_info('http://api.lolesports.com/api/v1/scheduleItems?leagueId=9'))
    tournaments = schedule['highlanderTournaments'][0]
    tournamentId = tournaments['id']
    barckets = tournaments['brackets']
    for bracketId, bracket in brackets:
        for matchId, match in bracket:
            if match['state'] == 'resolved':
                games = mtach['games']
                for highlanderGameId, game in games:
                    matchDetails = riot_api.get_acs_info('http://api.lolesports.com/api/v2/\
                        highlanderMatchDetails?tournamentId=?&matchId=?' % tournamentId, matchId)
                    gameId = game['gameId']
                    gameRealm = game['gameRealm']
                    gameDetailsId = game['id']
                    matchHistory = json.loads(riot_api.get_acs_info('matchhistory..' % gameRealm, gameId, gameHash)).read())
                    participantIds = matchHistory['participantIdentities']
                    participants = matchHistory['participants']
                    parDict = {}
                    for participant in participantIds:
                        parDict[participant['player']['summonerName']['name']] = participant['participantId']
                    for player in game['players']:
                        add_player_info(db, )
'''

def add_match_details(db, series_id, team_one, team_two, week, region_id):
    db.execute('INSERT INTO match_details (series_id, region_id, team_one_id,'
               ' team_two_id, league_week) VALUES (?, ?, ?, ?, ?)', 
                [series_id, region_id, team_one['id'], team_two['id'], week])


def add_player_info(db, player_id, name, photo_url):
    cur = db.execute('select player_id from playerinfo where player_id = ' + str(player_id))
    check = cur.fetchone()
    if check is None:
        db.execute('insert into playerinfo (player_id, name, photo_url) '
                    'values (?, ?, ?)', [player_id, name, photo_url])

def add_match_participant(db, match_id, player_id, participant_id,
                            team_id, kills, deaths, assists, champion,
                            spell_id_one, spell_id_two, item_set):
    db.execute('insert into match_participant (match_id, player_id,'
                'participant_id, team_id, kills, deaths, assists, champion,'
                'spell_id_one, spell_id_two, item_set)'
                ' values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', [match_id, player_id,
                participant_id, team_id, kills, deaths, assists, champion,
                spell_id_one, spell_id_two, item_set])
    
def add_team(db, team_id, name, url):
    cur = db.execute('select team_name from teams where team_id = ' + str(team_id))
    check = cur.fetchone()
    if check is None:
        db.execute('insert into teams (team_id, team_name, logo_url)'
                    ' values (?, ?, ?)', [int(team_id), name, url])



'''
    This game just takes that information, and adds it to our database.
    That way, we never have to talk to ACS/Swagger API again
''' 
def add_match(db, url, teams, game_number, winner_id, players, series_id):            
    timeline_url = riot_api.get_timeline_url(url)
    md = json.loads(riot_api.get_acs_info(url).read())
    id = md['gameId']
    date = datetime.datetime.fromtimestamp(md['gameCreation']/1000)
    is_json = json.loads(riot_api.get_acs_info(timeline_url).read())['frames']
    item_sets = build_parser.get_build_steps(is_json)
    participants = md['participants']
    p_ids = {str(p['stats']['goldEarned']) + " " + str(p['championId']):p['participantId'] for p in participants}
    for player in players:
        p = players[player]
        index = str(p['totalGold']) + " " + str(p['championId'])
        add_player_info(db, p['id'], p['name'], p['photoURL'])
        add_match_participant(db, int(id), p['id'], p_ids[index],
                                p['teamId'], p['kills'], p['deaths'], p['assists'],
                                p['championId'], p['spell0'], p['spell1'],
                                json.dumps(item_sets[p_ids[index]]))
    participantIds = json.dumps(md['participantIdentities'])
    participants = json.dumps(participants)
    db.execute('insert into matches (match_id, time_stamp, game_number,'
               'series_id, winning_team_id) values (?, ?, ?, ?, ?)',
             [id, date.isoformat(), int(game_number), series_id, winner_id])
    db.commit()

if __name__ == "__main__":
    do_magic(lolitemsets.connect_db(), time.strftime("2015-09-07"))