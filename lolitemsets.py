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
    
def get_dropdown_menu():
    cur = g.db.execute(""" SELECT id, name from leagues""")
    leagues = [dict(id = row[0], name=row[1]) for row in cur.fetchall()]
    cur = g.db.execute(""" SELECT player_id, name from playerinfo""")
    players = [dict(id = row[0], name=row[1]) for row in cur.fetchall()]
    cur = g.db.execute(""" SELECT team_id, team_name from teams""")
    teams = [dict(id = row[0], name=row[1]) for row in cur.fetchall()]
    return dict(League = leagues, Player = players, Team = teams)

@app.before_request
def before_request():
    g.db = connect_db()
    
@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

@app.route("/player/<int:player_id>/")
@app.route("/player/<int:player_id>")
def get_player_matches(player_id):
    query = " AND match_participant.match_id = matches.match_id AND match_participant.player_id = %s" % str(player_id)
    m = get_list_of_matches(query)
    return render_template('matches.html', matches = m, dropdown = get_dropdown_menu())

@app.route("/team/<int:team_id>/")
@app.route("/team/<int:team_id>")
def get_team_matches(team_id):
    query = " AND (match_details.team_one_id = %s OR match_details.team_two_id = %s) " % (str(team_id), str(team_id));
    m = get_list_of_matches(query)
    return render_template('matches.html', matches = m, dropdown = get_dropdown_menu())

# This shows all the matches for a single league.
@app.route("/league/<int:league_id>")
@app.route("/league/<int:league_id>/")
def show_league_matches(league_id):
    query = " and match_details.region_id = %s " % str(league_id)
    m = get_list_of_matches(query)
    version = riot_api.get_version()
    return render_template('matches.html', matches = m, version = version, dropdown = get_dropdown_menu())

# Default view. This just displays all the matches FROM the pASt 10 ish series.
@app.route("/")
def show_recent_matches():
    m = get_list_of_matches()
    return render_template('matches.html', matches = m, dropdown = get_dropdown_menu())

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
    version = riot_api.get_version()
    return render_template('match.html', match = m, version = version, dropdown = get_dropdown_menu())
    
# Just a prettier page for people that
# Try to put in bad urls
@app.errorhandler(404)
@app.errorhandler(500)
def exception_handler(error):
    return render_template('error.html', dropdown = get_dropdown_menu()), 404
    
# This is solely for checking the databASe contents.
@app.route("/checkitems")
def show_champions():
    cur = g.db.execute('SELECT name, img_url FROM items order by id desc')
    entries = [dict(name=row[0], lore=row[1]) for row in cur.fetchall()]
    return render_template('champions.html', entries=entries, dropdown = get_dropdown_menu())

def get_list_of_matches(unique_qualifier="  "):
    string = ("""SELECT t1.team_name, t2.team_name, matches.match_id,
                     matches.game_number, matches.time_stamp, 
                     MAX (CASE WHEN mp.participant_id = 1 AND mp.champion = c.id THEN c.img_url else null end) AS champ1,
                     MAX (CASE WHEN mp.participant_id = 2 AND mp.champion = c.id THEN c.img_url else null end) AS champ2,
                     MAX (CASE WHEN mp.participant_id = 3 AND mp.champion = c.id THEN c.img_url else null end) AS champ3,
                     MAX (CASE WHEN mp.participant_id = 4 AND mp.champion = c.id THEN c.img_url else null end) AS champ4,
                     MAX (CASE WHEN mp.participant_id = 5 AND mp.champion = c.id THEN c.img_url else null end) AS champ5,
                     MAX (CASE WHEN mp.participant_id = 6 AND mp.champion = c.id THEN c.img_url else null end) AS champ6,
                     MAX (CASE WHEN mp.participant_id = 7 AND mp.champion = c.id THEN c.img_url else null end) AS champ7,
                     MAX (CASE WHEN mp.participant_id = 8 AND mp.champion = c.id THEN c.img_url else null end) AS champ8,
                     MAX (CASE WHEN mp.participant_id = 9 AND mp.champion = c.id THEN c.img_url else null end) AS champ9,
                     MAX (CASE WHEN mp.participant_id = 10 AND mp.champion = c.id THEN c.img_url else null end) AS champ10,
                     MAX (CASE WHEN mp.participant_id = 1 AND mp.team_id = t1.team_id THEN t1.team_name else null END) AS blue_name,
                      t1.logo_url, t2.logo_url 
                     FROM teams AS t1, teams AS t2, match_details, matches, 
                     champions AS c, match_participant AS mp 
                     INNER JOIN (SELECT DISTINCT match_details.series_id, matches.time_stamp  
                     from matches, match_details, match_participant where match_details.series_id = matches.series_id 
                     and matches.game_number = 1 %s ORDER BY matches.time_stamp desc LIMIT 10) t ON matches.series_id = t.series_id
                     WHERE t1.team_id = match_details.team_one_id
                     AND t2.team_id = match_details.team_two_id
                     AND mp.match_id = matches.match_id
                     AND mp.champion = c.id
                     AND match_details.series_id = matches.series_id
                     group by matches.match_id
                     order by t.time_stamp desc""" % unique_qualifier)
    cur = g.db.execute(string)
    m = [dict(team_one = dict(name = row[0], logo = row[16]), 
        team_two = dict(name = row[1], logo = row[17]), match_id = row[2],
        game_number = row[3], time_stamp = row[4], 
        champions = [row[i] for i in range(5, 15)], 
        blue_name = (row[1] if row[15] is None else row[15])) 
        for row in cur.fetchall()] 
    return m

if __name__ == "__main__":
    LAST_UPDATED = datetime.datetime.utcfromtimestamp(0)
    app.run()