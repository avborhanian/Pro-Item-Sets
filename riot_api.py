import urllib2
import httplib
import json
import time
import ConfigParser
import datetime

config = ConfigParser.RawConfigParser()
config.read('configuration')

SECRET_KEY = config.get("Riot API", "SECRET_KEY")

# Returns match details of a given match id in Json format.
# Includes Timeline by default.
## TODO make sure match_id is valid. If not, return null.
def get_match(match_id):
    response = None
    try:
        response = urllib2.urlopen("https://na.api.pvp.net/api/lol/na/v2.2/match/" + str(match_id) + "?includeTimeline=true&api_key=" + SECRET_KEY)
    except urllib2.HTTPError, e:
        print "ERROR! " + str(e.code)
    except urllib2.URLError, e:
        print "Error! " + str(e.reason())
    except httplib.HTTPException, e:
        print "HTTPException error occurred"
    if response is not None:
        return json.loads(response.read())
    return None
    
def get_event_frames(match_json):
    if match_json is not None:
        # This just obtains the frame specific data we want. We can ignore the rest.
        try:
            return match_json['timeline']['frames']
        except:
            return None
    return None
   
def get_recent_matches():
    epoch = datetime.datetime.utcfromtimestamp(0)
    now = datetime.datetime.now()
    delta = datetime.timedelta(seconds = now.second, microseconds = now.microsecond)
    truncated = now - delta
    minutedelta = datetime.timedelta(minutes=(truncated.minute - (truncated.minute / 5 * 5 - 5)))
    rounded = truncated - minutedelta
    total_seconds = str(int((rounded - epoch).total_seconds()))
    try:
        response = urllib2.urlopen("https://na.api.pvp.net/api/lol/na/v4.1/game/ids?beginDate=" + total_seconds + "&api_key=" + SECRET_KEY)
        return json.loads(response.read())
    except urllib2.HTTPError, e:
        print "ERROR! " + str(e.code)
    except urllib2.URLError, e:
        print "Error! " + str(e.reason())
    except httplib.HTTPException, e:
        print "HTTPException error occurred"
    return None
    
def get_current_champions():
    response = None
    try:
        response = urllib2.urlopen("http://ddragon.leagueoflegends.com/cdn/5.16.1/data/en_US/champion.json")
        return json.loads(response.read())
    except urllib2.HTTPError, e:
        print "ERROR! " + str(e.code)
    except urllib2.URLError, e:
        print "Error! " + str(e.reason())
    except httplib.HTTPException, e:
        print "HTTPException error occurred"
    return None
        
def get_champ_stats(summoner_id, champ_id):
    response = None
    try:
        response = urllib2.urlopen("https://na.api.pvp.net/api/lol/na/v1.3/stats/by-summoner/" + str(summoner_id) + "/ranked?season=SEASON2015&api_key=" + SECRET_KEY)
        champions = json.loads(response.read())["champions"]
        for champ in champions:
            if champ["id"] == champ_id:
                print champ["stats"]
                break
        return champ["stats"]
    except urllib2.HTTPError, e:
        print "ERROR! " + str(e.code)
    except urllib2.URLError, e:
        print "Error! " + str(e.reason())
    except httplib.HTTPException, e:
        print "HTTPException error occurred"
    return None
    
def get_items():
    response = None
    try:
        response = urllib2.urlopen("http://ddragon.leagueoflegends.com/cdn/5.16.1/data/en_US/item.json")
        items = json.loads(response.read())["data"]
        return items
    except urllib2.HTTPError, e:
        print "ERROR! " + str(e.code)
    except urllib2.URLError, e:
        print "Error! " + str(e.reason())
    except httplib.HTTPException, e:
        print "HTTPException error occurred"
    return None

def get_champions():
    response = None
    try:
        response = urllib2.urlopen("http://ddragon.leagueoflegends.com/cdn/5.16.1/data/en_US/champion.json")
        items = json.loads(response.read())["data"]
        return items
    except urllib2.HTTPError, e:
        print "ERROR! " + str(e.code)
    except urllib2.URLError, e:
        print "Error! " + str(e.reason())
    except httplib.HTTPException, e:
        print "HTTPException error occurred"
    return None
    
# Sorry RITO
def get_acs_info(url):
    response = None
    try:
        req = urllib2.Request(url, headers={'User-Agent' : "Magic Browser"}) 
        con = urllib2.urlopen( req )
        return con
    except urllib2.HTTPError, e:
        if str(e.code) in '429':
            print "Oops we pissed Riot off, wait 10"
            time.sleep(10)
            return get_acs_info(url)
        else:
            print str(e.code)
    except urllib2.URLError, e:
        print "Error! " + str(e.reason())
    except httplib.HTTPException, e:
        print "HTTPException error occurred"
    return None
    
def get_match_detail_url(url):
    index = url.find('details') + 7
    print "Getting Match Detail URL"
    print url
    print index
    new_url = "https://acs.leagueoflegends.com/v1/stats/game/" + url[index:]
    print new_url
    print "Done GETTING URL"
    return new_url
    
def get_timeline_url(url):
    index = url.find('?gameHash')
    new_url = url[:index] + '/timeline' + url[index:]
    return new_url