#My imports yall
from flask import Flask, render_template, g, jsonify
import sqlite3
from contextlib import closing
import os
import riot_api
import datetime
import pandoras_box
import build_parser
import json

# Config
PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))
DATABASE = os.path.join(PROJECT_ROOT, 'tmp', 'lcsifyer.db')
DEBUG = False
LAST_UPDATED = datetime.datetime.utcfromtimestamp(0)

# The following creates the application and appies the config info above
app = Flask(__name__)
app.config.from_object(__name__)

def connect_db():
    return sqlite3.connect(app.config['DATABASE'])

# This sets up our database.
def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        items = riot_api.get_items()
        for item in items:
            item_data = items[item]
            gold = item_data['gold']
            db.execute('insert into items (id, name, img_url, base_cost, full_cost) values (?, ?, ?, ?, ?)',
                 [item, item_data['name'], item_data['image']['full'], gold['base'], gold['total']])
        champions = riot_api.get_champions()
        for champ in champions:
            id = int(champions[champ]['key'])
            img_url = champions[champ]['image']['full']
            db.execute('insert into champions (id, img_url) values (?, ?)', [id, img_url])
        db.commit()

# I'm calling it Pandora's Box for a reason. Riot don't look please man.
def add_match():
    pandoras_box.do_magic(connect_db(), "2015-08-31")
    pandoras_box.do_magic(connect_db(), "2015-08-24")
    pandoras_box.do_magic(connect_db(), "2015-08-17")
    pandoras_box.do_magic(connect_db(), "2015-08-10")
    pandoras_box.do_magic(connect_db(), "2015-08-3")
       
@app.before_request
def before_request():
    g.db = connect_db()
    
@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

# Default view. This just displays all the matches from the past.... ever.
@app.route("/")
def show_recent_matches():
    cur = g.db.execute('select id, teams, participants, game_number from matches order by time_stamp desc')
    matches = [dict(match_id = row[0], teams = json.loads(row[1]), participants = json.loads(row[2]), game_number = row[3] ) for row in cur.fetchall()]
    for match in matches:
        champs_used = []
        for participant in match['participants']:
            champs_used.append(str(participant['championId']))
        cur = g.db.execute("select id, img_url from champions where id in (" + ",".join(champs_used) + ")")
        dbres = cur.fetchall()
        champ_images = []
        for champ in champs_used:
            for row in dbres:
                if int(row[0]) == int(champ):
                    champ_images.append(row[1])
        match['champions'] = champ_images
    return render_template('matches.html', matches = matches)

# Returns a single match page.
# I chose to just keep the summoner_spells in code because
# I didn't think it made sense to make a web call for something
# this small
@app.route("/match/<match_id>")
def show_match_page(match_id):
    summoner_spells = {11: "SummonerSmite.png", 10: "SummonerRevive.png", 13: "SummonerMana.png", 12: "SummonerTeleport.png", 21: "SummonerBarrier.png", 17: "SummonerOdinGarrison.png", 31: "SummonerPoroThrow.png", 30: "SummonerPoroRecall.png", 1: "SummonerBoost.png", 3: "SummonerExhaust.png", 2: "SummonerClairvoyance.png", 4: "SummonerFlash.png", 7: "SummonerHeal.png", 6: "SummonerHaste.png", 14: "SummonerDot.png"}
    cur = g.db.execute("SELECT participants, participantIds, item_sets FROM matches WHERE id IS " + match_id)
    match = [dict(participants = json.loads(row[0]), participantIds = json.loads(row[1]), item_sets=row[2]) for row in cur.fetchall()][0]
    champs_used = []
    for participant in match['participants']:
        champs_used.append(str(participant['championId']))
    cur = g.db.execute("select id, img_url from champions where id in (" + ",".join(champs_used) + ")")
    dbres = cur.fetchall()
    champ_images = []
    for champ in champs_used:
            for row in dbres:
                if int(row[0]) == int(champ):
                    champ_images.append(row[1])
    match['champions'] = champ_images
    match['jparticipants'] = json.dumps(match['participantIds'])
    match['jchampions'] = json.dumps(champ_images)
    return render_template('match.html', match = match, summoners = summoner_spells)
    
# This shows all the matches for a single league.
@app.route("/league/<int:league_id>")
def show_league_matches(league_id):
    cur = g.db.execute('select id, teams, participants, game_number from matches where region_id is ' + str(league_id) + ' order by time_stamp desc')
    matches = [dict(match_id = row[0], teams = json.loads(row[1]), participants = json.loads(row[2]), game_number = row[3] ) for row in cur.fetchall()]
    for match in matches:
        champs_used = []
        for participant in match['participants']:
            champs_used.append(str(participant['championId']))
        cur = g.db.execute("select id, img_url from champions where id in (" + ",".join(champs_used) + ")")
        dbres = cur.fetchall()
        champ_images = []
        for champ in champs_used:
            for row in dbres:
                if int(row[0]) == int(champ):
                    champ_images.append(row[1])
        match['champions'] = champ_images
    return render_template('matches.html', matches = matches)
    
# Just a prettier page for people that
# Try to put in bad urls
@app.errorhandler(404)
@app.errorhandler(500)
def exception_handler(error):
    return render_template('error.html')
    
# This is solely for checking the database contents.
@app.route("/checkitems")
def show_champions():
    cur = g.db.execute('select name, img_url from items order by id desc')
    entries = [dict(name=row[0], lore=row[1]) for row in cur.fetchall()]
    return render_template('champions.html', entries=entries)


if __name__ == "__main__":
    LAST_UPDATED = datetime.datetime.utcfromtimestamp(0)
    app.run()