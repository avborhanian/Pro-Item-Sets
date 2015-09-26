import urllib2
import httplib
import json
import time
import ConfigParser
import datetime

config = ConfigParser.RawConfigParser()
config.read('configuration')

SECRET_KEY = config.get("Riot API", "SECRET_KEY")
LAST_UPDATE = datetime.datetime.utcfromtimestamp(0)
THIRTY_MINUTES = 1800
VERSION = ""

def get_version():
    global VERSION
    global LAST_UPDATE
    if (datetime.datetime.now() - LAST_UPDATE).total_seconds() < THIRTY_MINUTES:
        return VERSION
    else:
        LAST_UPDATE = datetime.datetime.now()
        try:
            response = urllib2.urlopen("https://ddragon.leagueoflegends.com/realms/na.json")
            VERSION = json.loads(response.read())
            return VERSION
        except urllib2.HTTPError, e:
            print "ERROR! " + str(e.code)
        except urllib2.URLError, e:
            print "Error! " + str(e.reason())
        except httplib.HTTPException, e:
            print "HTTPException error occurred"
        return None

def get_event_frames(match_json):
    if match_json is not None:
        # This just obtains the frame specific data we want. We can ignore the rest.
        try:
            return match_json['timeline']['frames']
        except:
            return None
    return None

# Gets recent matches from Riot's API   
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
    
def get_summoners():
    return get_from_cdn('/data/en_US/summoner.json')
 
def get_items():
    return get_from_cdn('/data/en_US/item.json')

def get_champions():
    return get_from_cdn('/data/en_US/champion.json')
    
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
        print e
        print "Oops we pissed Riot off, wait 10"
        time.sleep(10)
        return get_acs_info(url)
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

def get_from_cdn(end_url):
    response = None
    version = get_version()
    try:
        response = urllib2.urlopen(version['cdn'] + '/' + version['dd'] + end_url)
        items = json.loads(response.read())["data"]
        return items
    except urllib2.HTTPError, e:
        print "ERROR! " + str(e.code)
    except urllib2.URLError, e:
        print "Error! " + str(e.reason())
    except httplib.HTTPException, e:
        print "HTTPException error occurred"
    return None