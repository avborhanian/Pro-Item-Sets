#My imports yall
from flask import Flask, render_template, g, jsonify
import sqlite3
from contextlib import closing
import os
import riot_api
import datetime
import time
import pandoras_box
import build_parser
import json

# Config
PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))
DATABASE = os.path.join(PROJECT_ROOT, 'tmp', 'lcsifyer.db')
DEBUG = True
LAST_UPDATED = datetime.datetime.utcfromtimestamp(0)

# The following creates the application AND appies the config info above
app = Flask(__name__)
app.config.from_object(__name__)

def connect_db():
    return sqlite3.connect(app.config['DATABASE'])

# This sets up our databASe.
def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        update_items(db)
        update_champions(db)
        update_summoners(db)
        db.commit()

def update_summoners(db):
    summoners = riot_api.get_summoners()
    for summoner in summoners:
        s = summoners[summoner]
        db.execute('insert into summoners (id, name, img_url) values (?, ?, ?)',
            [s['key'], s['name'], s['image']['full']])

def update_items(db):
    items = riot_api.get_items()
    for item in items:
        item_data = items[item]
        gold = item_data['gold']
        db.execute('insert into items (id, name, img_url, base_cost, full_cost) values (?, ?, ?, ?, ?)',
             [item, item_data['name'], item_data['image']['full'], gold['base'], gold['total']])    

def update_champions(db):
    champions = riot_api.get_champions()
    for champ in champions:
        id = int(champions[champ]['key'])
        img_url = champions[champ]['image']['full']
        db.execute('insert into champions (id, img_url) values (?, ?)', [id, img_url])

# I'm calling it PANDora's Box for a reASon. Riot don't look pleASe man.
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

# Default view. This just displays all the matches FROM the pASt 10 ish series.
@app.route("/")
def show_recent_matches():
    cur = g.db.execute('SELECT t1.team_name, t2.team_name, matches.match_id,'
                    ' matches.game_number, matches.time_stamp, '
                    ' MAX (CASE WHEN mp.participant_id = 1 AND mp.champion = c.id THEN c.img_url else null end) AS champ1,'
                    ' MAX (CASE WHEN mp.participant_id = 2 AND mp.champion = c.id THEN c.img_url else null end) AS champ2,'
                    ' MAX (CASE WHEN mp.participant_id = 3 AND mp.champion = c.id THEN c.img_url else null end) AS champ3,'
                    ' MAX (CASE WHEN mp.participant_id = 4 AND mp.champion = c.id THEN c.img_url else null end) AS champ4,'
                    ' MAX (CASE WHEN mp.participant_id = 5 AND mp.champion = c.id THEN c.img_url else null end) AS champ5,'
                    ' MAX (CASE WHEN mp.participant_id = 6 AND mp.champion = c.id THEN c.img_url else null end) AS champ6,'
                    ' MAX (CASE WHEN mp.participant_id = 7 AND mp.champion = c.id THEN c.img_url else null end) AS champ7,'
                    ' MAX (CASE WHEN mp.participant_id = 8 AND mp.champion = c.id THEN c.img_url else null end) AS champ8,'
                    ' MAX (CASE WHEN mp.participant_id = 9 AND mp.champion = c.id THEN c.img_url else null end) AS champ9,'
                    ' MAX (CASE WHEN mp.participant_id = 10 AND mp.champion = c.id THEN c.img_url else null end) AS champ10'
                    ' FROM teams AS t1, teams AS t2, match_details, matches, '
                    ' champions AS c, match_participant AS mp '
                    ' WHERE t1.team_id = match_details.team_one_id'
                    ' AND t2.team_id = match_details.team_two_id '
                    ' AND mp.match_id = matches.match_id'
                    ' AND mp.champion = c.id'
                    ' AND match_details.series_id = matches.series_id'
                    ' group by matches.match_id'
                    ' order by time_stamp desc')
    m = [dict(team_one = row[0], team_two = row[1], match_id = row[2],
                 game_number = row[3], time_stamp = row[4],
                 champions = [row[i] for i in range(5, 15)]) for row in cur.fetchall()]
    return render_template('matches.html', matches = m)
# Returns a single match page.
# I chose to just keep the summoner_spells in code because
# I didn't think it made sense to make a web call for something
# this small
@app.route("/match/<match_id>")
def show_match_page(match_id):
    cur = g.db.execute("""SELECT mp.participant_id, p.name, mp.kills, mp.deaths,
                        mp.assists, c.img_url, t.team_name, s1.img_url, s2.img_url, mp.item_set FROM 
                        match_participant AS mp, summoners AS s1, summoners AS s2, 
                        playerinfo AS p, champions AS c, teams as t
                        WHERE mp.match_id =  ? AND 
                        s1.id = mp.spell_id_one AND
                        s2.id = mp.spell_id_two AND
                        p.player_id = mp.player_id AND 
                        c.id = mp.champion AND t.team_id = mp.team_id
                        ORDER BY mp.participant_id""", [int(match_id)])
    m = [dict(participant_id = row[0], name = row[1], kills = row[2],
            deaths = row[3], assists = row[4], img_url = row[5], 
            team_name = row[6], spell1 = row[7], spell2 = row[8],
            item_set = json.loads(row[9]), safe_set = row[9]) for row in cur.fetchall()]
    print json.dumps(m)
    version = riot_api.get_version()
    return render_template('match.html', match = m, version = version)
    
# This shows all the matches for a single league.
@app.route("/league/<int:league_id>")
def show_league_matches(league_id):
    cur = g.db.execute('SELECT matches.match_id, t1.team_name, t2.team_name, matches.game_number,'
                    ' MAX (CASE WHEN mp.participant_id = 1 AND mp.champion = c.id THEN c.img_url else null end) AS champ1,'
                    ' MAX (CASE WHEN mp.participant_id = 2 AND mp.champion = c.id THEN c.img_url else null end) AS champ2,'
                    ' MAX (CASE WHEN mp.participant_id = 3 AND mp.champion = c.id THEN c.img_url else null end) AS champ3,'
                    ' MAX (CASE WHEN mp.participant_id = 4 AND mp.champion = c.id THEN c.img_url else null end) AS champ4,'
                    ' MAX (CASE WHEN mp.participant_id = 5 AND mp.champion = c.id THEN c.img_url else null end) AS champ5,'
                    ' MAX (CASE WHEN mp.participant_id = 6 AND mp.champion = c.id THEN c.img_url else null end) AS champ6,'
                    ' MAX (CASE WHEN mp.participant_id = 7 AND mp.champion = c.id THEN c.img_url else null end) AS champ7,'
                    ' MAX (CASE WHEN mp.participant_id = 8 AND mp.champion = c.id THEN c.img_url else null end) AS champ8,'
                    ' MAX (CASE WHEN mp.participant_id = 9 AND mp.champion = c.id THEN c.img_url else null end) AS champ9,'
                    ' MAX (CASE WHEN mp.participant_id = 10 AND mp.champion = c.id THEN c.img_url else null end) AS champ10'
                    ' FROM teams AS t1, teams AS t2, match_details, matches, '
                    ' champions AS c, match_participant AS mp '
                    ' WHERE t1.team_id = match_details.team_one_id'
                    ' AND t2.team_id = match_details.team_two_id '
                    ' AND mp.match_id = matches.match_id'
                    ' AND mp.champion = c.id'
                    ' AND match_details.series_id = matches.series_id'
                    ' AND match_details.region_id = ' + str(league_id) + 
                    ' group by matches.match_id'
                    ' order by time_stamp desc')
    version = riot_api.get_version()
    matches = [dict(match_id = row[0], team_one = row[1], team_two = row[2], 
                game_number = row[3], 
                champions = [row[i] for i in range(4, 14)]) 
                for row in cur.fetchall()]
    return render_template('matches.html', matches = matches, version = version)
    
# Just a prettier page for people that
# Try to put in bad urls
@app.errorhandler(404)
@app.errorhandler(500)
def exception_handler(error):
    return render_template('error.html')
    
# This is solely for checking the databASe contents.
@app.route("/checkitems")
def show_champions():
    cur = g.db.execute('SELECT name, img_url FROM items order by id desc')
    entries = [dict(name=row[0], lore=row[1]) for row in cur.fetchall()]
    return render_template('champions.html', entries=entries)


if __name__ == "__main__":
    LAST_UPDATED = datetime.datetime.utcfromtimestamp(0)
    app.run()