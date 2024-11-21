# Dependencies 
import pickle
from logging import raiseExceptions
from flask import Flask, render_template, request, Response, url_for, jsonify, redirect, session
from datetime import datetime, date
import sqlite3
import pandas as pd
import statsapi as mlb
import json
import numpy as np
from database import database
from database import databaseNHL
from flask_basicauth import BasicAuth
from sqlalchemy import text
from itertools import combinations
import math

# Modules
from functions import batting, predict, starters, smartContract, sanitycheck, odds
from functions_c import batting_c, starters_c, predict_c
from schedule import schedule
from schedule import scheduleNHL
from scrapper import winprob
import time
import atexit
import calendar
from passlib.hash import sha256_crypt

from apscheduler.schedulers.background import BackgroundScheduler
import functools
from datetime import timedelta
from flask_mail import Mail
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Message
import requests
from bs4 import BeautifulSoup
import threading
from flask_socketio import SocketIO, emit

import subprocess
import os

# Connect App + DB
app = Flask(__name__)
app.secret_key = "^d@0U%['Plt7w,p"
app.config['SECRET_KEY'] = "^d@0U%['Plt7w,p"

# Password Protect
app.config['BASIC_AUTH_USERNAME'] = 'luca'
app.config['BASIC_AUTH_PASSWORD'] = 'betmlbluca4722'
basic_auth = BasicAuth(app)
app.config['BASIC_AUTH_FORCE'] = False

app.config['MAIL_SERVER']='smtp.mailtrap.io'
app.config['MAIL_PORT'] = 2525
app.config['MAIL_USERNAME'] = 'd6940e1e3a7b9e'
app.config['MAIL_PASSWORD'] = '5a3c33eb014fbe'

# app.config['MAIL_SERVER']='smtp.gmail.com'
# app.config['MAIL_PORT'] = 465

# app.config['MAIL_USERNAME'] = 'Strongwind410@gmail.com'
# app.config['MAIL_PASSWORD'] = "1234567890zZ"
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['SECURITY_PASSWORD_SALT'] = "betmlblucalucamaurelli@proton.me"
app.config['MAIL_DEFAULT_SENDER'] = "Strongwind410@gmail.com'"
app.config['PERMANENT_SESSION_LIFETIME'] = 3600
app.config['site'] = ''

mail = Mail(app)

users = {"username": "luca", "password": "betmlbluca4722"}
socketio = SocketIO(app, cors_allowed_origins='*')
engine = database.connect_to_db()
engine_nhl = databaseNHL.connect_to_db()

def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=app.config['SECURITY_PASSWORD_SALT'])


def confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt=app.config['SECURITY_PASSWORD_SALT'],
            max_age=expiration
        )
    except:
        return False
    return email

def send_email(to, subject, template):
    msg = Message(
        subject,
        recipients=[to],
        html=template,
        sender=app.config['MAIL_DEFAULT_SENDER']
    )
    mail.send(msg)

def login_required(func):
    @functools.wraps(func)
    def secure_function(**kwargs):
        if "username" not in session:
            return redirect(url_for("login"))
        return func(**kwargs)

    return secure_function

@app.route('/confirm/<token>')
def confirm_email(token):
    email = None
    try:
        email = confirm_token(token)
    except:
        return jsonify('The confirmation link is invalid or has expired.')
    
    #engine = database.connect_to_db()
    res = engine.execute(f"SELECT confirmed FROM user_table WHERE username = '{email}';").fetchall()

    if res[0][0] == "1":    
        return jsonify('Account already confirmed. Please login.')
    else:
        session["username"] = email
        session["state"] = 0
        engine.execute(f"UPDATE user_table SET confirmed_on = '{date.today()}', confirmed = '1' WHERE username = '{email}';")
        return redirect(url_for('show_betting'))

@app.route('/switchSite', methods = ["POST"])
def switchSite(): 
    flag = request.form['flag']
    engine_nhl.execute('DELETE FROM home_site;')
    engine_nhl.execute(f"INSERT INTO home_site(site) VALUES('{flag}');")  
    return redirect(url_for('index'))

# Routes
@app.route('/', methods = ["GET", "POST"])
@login_required
def index(): 
    engine_nhl = databaseNHL.connect_to_db()
    site_res = engine_nhl.execute('SELECT * FROM home_site').fetchall()
    if len(site_res) == 0:
        app.config['site'] = 'MLB'
    else:
        app.config['site'] = site_res[0][0]


    if app.config['site'] == 'NHL':
        if session["state"] == 0:
            return redirect(url_for("show_betting"))
        year = date.today().year
        today_schedule = scheduleNHL.get_schedule(engine_nhl)                    
        last_update = pd.read_sql("SELECT * FROM updates", con = engine_nhl).iloc[-1]
        last_date, last_time, last_record = last_update["update_date"], last_update["update_time"], last_update["last_record"]

        return render_template("NHL/index.html", schedule = today_schedule, last_record = last_record, 
                            update_date = last_date)
    else:
        if session["state"] == 0:
            return redirect(url_for("show_betting"))
        
        try: 
            del model_1a
        except: 
            pass
        try: 
            del model_1b
        except: 
            pass
        try: 
            del engine
        except: 
            pass
        try: 
            del X_train
        except:
            pass
        try: 
            del X_test
        except:
            pass

        year = date.today().year
        today_schedule = schedule.get_schedule()    
        engine = database.connect_to_db()
        last_update = pd.read_sql("SELECT * FROM updates", con = engine).iloc[-1]
        last_date, last_time, last_record = last_update["update_date"], last_update["update_time"], last_update["last_record"]
        average = pd.read_sql(f"SELECT * FROM league_average WHERE year = '{year}';", con = engine).to_dict('records')
        date_res = pd.read_sql(f"SELECT * FROM updates ORDER BY update_date DESC LIMIT 1;", con = engine).to_dict('records')
        date_string = date_res[0]['update_date']
        win_count_res = pd.read_sql(f"SELECT COUNT(*) FROM staking_table WHERE result = 'W' AND game_date != '{date_string}';", con = engine).to_dict('records')
        bet_count_res = pd.read_sql(f"SELECT COUNT(*) FROM staking_table WHERE game_date != '{date_string}';", con = engine).to_dict('records')
        auto_stakes = pd.read_sql(f"SELECT * FROM sato_stake_size ORDER BY stake;", con = engine).to_dict('records')
        win_count = win_count_res[0]['count'] + 291
        bet_count = bet_count_res[0]['count'] + 572
        loss_count = bet_count - win_count
        win_percent = round((win_count / bet_count) * 100, 2)

        return render_template("MLB/index.html", schedule = today_schedule, last_record = last_record, 
                            update_date = last_date, update_time = last_time, average = average, win_count = win_count, loss_count = loss_count, win_percent = win_percent, auto_stakes = auto_stakes)

@app.route('/login', methods = ["GET", "POST"])
def login(): 
    if request.method == 'GET':
        return render_template("MLB/login.html")

    user = request.get_json()
    #engine = database.connect_to_db()
    res = engine.execute(f"SELECT username, password, position, confirmed FROM user_table WHERE username = '{user['username']}';").fetchall()

    if res == []:
        return jsonify("User didn't registered")
    
    if res[0][3] == '0':
        return jsonify("NOCON")

    if sha256_crypt.verify(user["password"], res[0][1]) == True:
        session.permanent = True
        app.permanent_session_lifetime = timedelta(hours=1)
        session["username"] = user['username']
        session["site"] = 'MLB'

        if res[0][2] == "0":
            session["state"] = 0
            return jsonify("user")
        elif res[0][2] == "1":
            session["state"] = 1
            return jsonify("admin")
        elif res[0][2] == "2":
            session["state"] = 2
            return jsonify("admin")
    
    return jsonify("Password failed!")

@app.route('/signup', methods = ["POST"])
def signup(): 
    user = request.get_json()   
    today = date.today()

    #engine = database.connect_to_db()
    res = engine.execute(f"SELECT username, confirmed FROM user_table WHERE username = '{user['username']}';").fetchall()

    if res !=[]:
        if res[0][1] == '0':
            return jsonify("NOCON")
        
        if res[0][1] == '1':
            return jsonify("Already regestered")

  
    password = sha256_crypt.encrypt(user["password"])
    engine.execute(f"INSERT INTO user_table(username, password, position, registered_on, confirmed ) VALUES('{user['username']}', '{password}', '0', '{today}', '0');")

    token = generate_confirmation_token(user['username'])
    confirm_url = "https://betmlb.me/confirm/" + token
    #confirm_url = url_for('confirm_email', token=token, _external=True)

    #html = render_template('activate.html', confirm_url=confirm_url)
    # print(html.strip())

    html = "To verify your mail click here. " + confirm_url

    url = "https://send.api.mailtrap.io/api/send"
    email = user['username']

    payload = "{\"from\":{\"email\":\"lucamaurelli@betmlb.me\",\"name\":\"BetMLB\"},\"to\":[{\"email\":\"" + email + "\"}],\"subject\":\"Confirm your mail!\",\"text\":\"" + html + "\",\"category\":\"Integration Test\"}"
    headers = {
    "Authorization": "Bearer fcc5c29e1926dd91538201eaef322987",
    "Content-Type": "application/json"
    }

    response = requests.request("POST", url, headers=headers, data=payload)


    return jsonify("NOCON")

@app.route('/changepassword', methods = ["POST"])
def changepassword(): 
    user = request.get_json()
    #engine = database.connect_to_db()
    res = engine.execute(f"SELECT username, password, position FROM user_table WHERE user = '{user['username']}';").fetchall()
    password = sha256_crypt.encrypt("password")

    return

@app.route('/logout', methods = ["GET"])
def logout(): 
    session.clear()
    return redirect(url_for("login"))

@app.route('/get_game_info', methods = ["POST"])
def get_game_info(): 
    #engine = database.connect_to_db()
    game_id = str(json.loads(request.form['data']))
    rosters = schedule.get_rosters(game_id)

    res = pd.read_sql(f"SELECT * FROM schedule WHERE game_id = '{game_id}'", con = engine).iloc[0]
    data = {'game_id': res['game_id'], 
        'rosters': rosters,
        'matchup': f"{res['away_name']} @ {res['home_name']}", 
        'time': res['game_datetime']
       }   
    data = jsonify(data)
    return data


@app.route('/get_bet_info', methods = ["POST"])
def get_bet_info(): 
    data = {}
    request_data = request.get_json()

    game_id = request_data['gameid']
    site = request_data['site']

    gameinfo = mlb.boxscore_data(game_id)
    #engine = database.connect_to_db()
    away_res = pd.read_sql(f"SELECT * FROM team_table WHERE team_id = '{gameinfo['teamInfo']['away']['id']}'", con = engine).to_dict('records')
    home_res = pd.read_sql(f"SELECT * FROM team_table WHERE team_id = '{gameinfo['teamInfo']['home']['id']}'", con = engine).to_dict('records')
    gamedate = gameinfo['gameId'][:10]

    

    data['away'] = away_res[0]['team_name']
    data['home'] = home_res[0]['team_name']
    data['date'] = gamedate.replace('/', '-')
    data['site_list'] = []

    site_res = pd.read_sql(f"SELECT * FROM site_list", con = engine).to_dict('records')
    for el in site_res:
        data['site_list'].append(el['site'])

    if site == 'NOSITE':
        bet_res = pd.read_sql(f"SELECT * FROM betting_table WHERE betdate = '{data['date']}' AND team1 = '{data['away']}' AND team2 = '{data['home']}';", con = engine).to_dict('records')
    else:
        bet_res = pd.read_sql(f"SELECT * FROM betting_table WHERE betdate = '{data['date']}' AND team1 = '{data['away']}' AND team2 = '{data['home']}' AND site = '{site}';", con = engine).to_dict('records')

    if(len(bet_res) == 0):
        data['state'] = 0
        data['odds'] = ''
        data['place'] = ''
        data['stake'] = 0
        data['wins'] = 0
        data['site'] = ''
    else:
        data['state'] = 1
        data['odds'] = bet_res[0]['odds']
        data['place'] = bet_res[0]['place']
        data['stake'] = bet_res[0]['stake']
        data['wins'] = bet_res[0]['wins']
        data['site'] = bet_res[0]['site']

    return data

@app.route('/get_player_info', methods = ["POST"])
def get_player_info(): 
    #engine = database.connect_to_db()
    game_id = str(json.loads(request.form['data']))
    rosters = schedule.get_rosters(game_id)

    res = pd.read_sql(f"SELECT * FROM schedule WHERE game_id = '{game_id}'", con = engine).iloc[0]
    data = {'game_id': res['game_id'], 
        'rosters': rosters,
        'away': res['away_name'], 
        'home': res['home_name']
       }   
    data = jsonify(data)

    return data

@app.route('/get_graph_info', methods = ["POST"])
def get_graph_info(): 
    #engine = database.connect_to_db()
    data = pd.read_sql(f"SELECT * FROM graph_table ORDER BY id;", con = engine).to_dict('records')
    return data

@app.route('/set_autoBet_state', methods = ["POST"])
def set_autoBet_state(): 
    data = {}
    #engine = database.connect_to_db()
    
    gameid = request.form['gameid']
    value = request.form['value']
    engine.execute(f"UPDATE odds_table SET auto_bet = '{value}' WHERE game_id = '{gameid}';")

    return data

@app.route('/set_autoStake_size', methods = ["POST"])
def set_autoStake_size(): 
    data = {}
    #engine = database.connect_to_db()
    
    stake = request.form['stake']
    engine.execute(f"UPDATE sato_stake_size SET status = '0' WHERE stake != '{stake}';")
    engine.execute(f"UPDATE sato_stake_size SET status = '1' WHERE stake = '{stake}';")

    return data

@app.route('/make_prediction', methods = ["POST"])
def make_prediction():
    if request.method == 'POST': 
        
        # Get Form Data
    
        form_data = json.loads(request.form['data'])

        params = {'away_batters': form_data['away_batters'], 
                  'home_batters': form_data['home_batters'], 
                  'away_starters': form_data['away_starters'], 
                  'home_starters': form_data['home_starters'],
                  }
        
        gameId = form_data['game_id']

        # Fixing Names
        matchup = form_data['matchup'].split(" @ ")
        away_full_name, home_full_name = matchup[0], matchup[1]
        res = mlb.get('teams', params = {'sportId': 1})['teams']

        params['game_id'] = gameId

        team_dict = [{k:v for k,v in el.items() if k in ['name', 'teamName', 'abbreviation']} for el in res]
        team_dict = {el['name']:el['abbreviation'] for el in team_dict}
        params['away_name'] = team_dict[away_full_name]
        params['home_name'] = team_dict[home_full_name]
        params['savestate'] = True
        #engine = database.connect_to_db()

        now = datetime.now()
        date_string = now.strftime('%Y-%m-%d')

        win_count_res = pd.read_sql(f"SELECT COUNT(*) FROM staking_table WHERE result = 'W' AND game_date != '{date_string}';", con = engine).to_dict('records')
        bet_count_res = pd.read_sql(f"SELECT COUNT(*) FROM staking_table WHERE game_date != '{date_string}';", con = engine).to_dict('records')

        win_precent = 0
        risk_coeff = 0
        stake_size = 0

        if bet_count_res[0]['count'] <= 20:
            win_percent = 0
            risk_coeff = 0
        else:
            win_percent = round(((win_count_res[0]['count'] + 291) / (bet_count_res[0]['count'] + 572)) * 100, 2)
            if win_percent > 49.25 and win_percent <= 49.75:
                risk_coeff = 0.1
            elif win_percent <= 49.25:
                risk_coeff = 0.5
            elif win_percent >= 50.25 and win_percent < 50.75:
                risk_coeff = -0.1
            elif win_percent >= 50.75:
                risk_coeff = -0.5
            else:
                risk_coeff = 0
        if bet_count_res[0]['count'] <= 20:
            stake_size = 25000
        else:
            stake_size = 40000 + risk_coeff * 40000
        
        # Make Prediction
        if form_data['model'] == 'a':
            predictions = predict.get_probabilities(params, engine)
            preds_1a = predictions['1a']
            preds_1a = np.round(100 * preds_1a[0], 2)
            away_odd = 0
            home_odd = 0
            away_dec_odd = 0
            home_dec_odd = 0
    
            away_dec_odd = round(1.05 / (preds_1a[0] / 100 ), 2)
            away_odd = odds.decimalToAmerian(away_dec_odd)

            home_dec_odd = round(1.05 / (preds_1a[1] / 100 ), 2)
            home_odd = odds.decimalToAmerian(home_dec_odd)

            preds_1a = {'away_prob': preds_1a[0], 'home_prob': preds_1a[1], 'away_odd': away_odd, 'home_odd': home_odd, 'stake': stake_size}
            
            preds_1b = predictions['1b']
            preds_1b = np.round(100 * preds_1b[0], 2)

            away_dec_odd = round(1.05 / ( preds_1b[0] / 100 ), 2)
            away_odd = odds.decimalToAmerian(away_dec_odd)

            home_dec_odd = round(1.05 / ( preds_1b[1] / 100 ), 2)
            home_odd = odds.decimalToAmerian(home_dec_odd)

            preds_1b = {'away_prob': preds_1b[0], 'home_prob': preds_1b[1], 'away_odd': away_odd, 'home_odd': home_odd, 'stake': stake_size}
            engine.execute(f"INSERT INTO predict_table(game_id, la_away_prob, la_home_prob, lb_away_prob, lb_home_prob, la_away_odd, la_home_odd, lb_away_odd, lb_home_odd) VALUES('{gameId}', '{preds_1a['away_prob']}', '{preds_1a['home_prob']}','{preds_1b['away_prob']}', '{preds_1b['home_prob']}', '{preds_1a['away_odd']}', '{preds_1a['home_odd']}', '{preds_1b['away_odd']}', '{preds_1b['home_odd']}') ON CONFLICT (game_id) DO UPDATE SET la_away_prob = excluded.la_away_prob, la_home_prob = excluded.la_home_prob, lb_away_prob = excluded.lb_away_prob, lb_home_prob = excluded.lb_home_prob, la_away_odd = excluded.la_away_odd, la_home_odd = excluded.la_home_odd, lb_away_odd = excluded.lb_away_odd, lb_home_odd = excluded.lb_home_odd;")
            engine.execute(f"INSERT INTO win_percent(game_id, away_prob_a, home_prob_a, away_prob_b, home_prob_b) VALUES('{gameId}', '{preds_1a['away_prob']}', '{preds_1a['home_prob']}','{preds_1b['away_prob']}', '{preds_1b['home_prob']}') ON CONFLICT (game_id) DO UPDATE SET away_prob_a = excluded.away_prob_a, home_prob_a = excluded.home_prob_a, away_prob_b = excluded.away_prob_b, home_prob_b = excluded.home_prob_b;") 

            prediction = {'model':'a', '1a': preds_1a, '1b': preds_1b}
        elif form_data['model'] == 'c':
            data = {}
            data['params'] = params
            data['stake_size'] = stake_size
            data['gameId'] = gameId
            
            thread = threading.Thread(target=calModelC, args=(data,))
            thread.start()
            preds_1c = {'away_prob': 0, 'home_prob': 0, 'away_odd': 0, 'home_odd': 0, 'stake': stake_size}
            prediction = {'model':'c', '1c': preds_1c}
        prediction = jsonify(prediction)
    
    return prediction

@app.route('/teams', methods = ["GET", "POST"]) 
@login_required
def teams():  
    #engine = database.connect_to_db()

    if request.method == 'GET':
        game_table = pd.read_sql(f"SELECT (team_name)tname, (team_abbr)abbreviation FROM team_table ORDER BY team_name;", con = engine).to_dict('records')
        return render_template("MLB/teams.html", data = game_table)
    if request.method == 'POST':
        team_data = request.get_json()

        data = {}
        data['win_loss'] = {}
        data['pl_win_loss'] = {}
        data['bet_on'] = {}
        data['bet_against'] = {}
        data['HeavyU'] = {}
        data['LightU'] = {}
        data['Even'] = {}
        data['LightF'] = {}
        data['HeavyF'] = {}
        data['price'] = []
        data['players'] = []

        win_loss_res = list(mlb.standings_data().values())
        for league in win_loss_res: 
            for team in league['teams']: 
                if team['name'] == team_data['name']:
                    data['win_loss']['win'] = team['w']
                    data['win_loss']['loss'] = team['l']

        today = date.today()
        today_str = today.strftime("%Y/%m/%d")
        year = today.year
        pl_res = pd.read_sql(f"SELECT odds_table.game_date, odds_table.away, odds_table.home, CASE WHEN away = '{team_data['name']}' THEN away_open WHEN home = '{team_data['name']}' THEN home_open ELSE 0 END as open_price, CASE WHEN away = '{team_data['name']}' THEN away_close WHEN home = '{team_data['name']}' THEN home_close ELSE 0 END as close_price, \
                                CASE WHEN away = '{team_data['name']}' AND winner = '0' THEN 0 WHEN away = '{team_data['name']}' AND winner = '1' THEN 1 WHEN home = '{team_data['name']}' AND winner = '0' THEN 1 WHEN home = '{team_data['name']}' AND winner = '1' THEN 0 ELSE 0 END as win FROM odds_table INNER JOIN game_table ON odds_table.game_id = game_table.game_id WHERE (odds_table.away = '{team_data['name']}' OR odds_table.home = '{team_data['name']}') AND odds_table.game_date != '{today_str}' AND odds_table.game_date LIKE '{year}%%' ORDER BY odds_table.game_date;", con = engine).to_dict('records')

        total = 0
        pl = 0
        yd = 0

        if len(pl_res) == 0:
            data['pl_win_loss']['total'] = total
            data['pl_win_loss']['pl'] = pl
            data['pl_win_loss']['yield'] = yd
        else:
            for game in pl_res:
                if game['open_price'] >= 100:
                    total += 1
                    if game['win'] == 0:
                        pl += game['open_price'] / 100
                    elif game['win'] == 1:
                        pl -= 1
                elif game['open_price'] < 100:
                    total += abs(game['open_price']) / 100
                    if game['win'] == 0:
                        pl += 1
                    elif game['win'] == 1:
                        pl += game['open_price'] / 100

            if total != 0:
                yd = pl / total * 100
            data['pl_win_loss']['total'] = round(total, 2)
            data['pl_win_loss']['pl'] = round(pl, 2)
            data['pl_win_loss']['yield'] = round(yd, 2)

        beton_res = pd.read_sql(f"SELECT 'ON team' AS total, COUNT(*) AS number_of_bets, \
                                    SUM(CASE WHEN status = '2' THEN 1 ELSE 0 END) AS won_count, \
                                    SUM(CASE WHEN status = '1' THEN 1 ELSE 0 END) AS lost_count, \
                                    to_char(ROUND(SUM(stake)::numeric, 2), 'FM999999999.00') AS total_stake, \
                                SUM(CASE \
                                        WHEN status::integer = 1 THEN stake * -1 \
                                        WHEN status::integer = 2 THEN wins \
                                    ELSE 0 \
                                    END) AS total_P_L, \
                                (SUM(CASE \
                                        WHEN status::integer = 1 THEN stake * -1 \
                                        WHEN status::integer = 2 THEN wins \
                                    ELSE 0 \
                                    END) / SUM(stake)) * 100 AS Yield \
                                FROM betting_table \
                                WHERE place = '{team_data['name']}' AND betdate LIKE '{year}%%';", con = engine).to_dict('records')
        
        
        if len(beton_res) == 0 or beton_res[0]['total_stake'] == None:
            data['bet_on']['num_bet'] = 0
            data['bet_on']['win'] = 0
            data['bet_on']['loss'] = 0
            data['bet_on']['stake'] = 0
            data['bet_on']['pl'] = 0
            data['bet_on']['yield'] = 0
        else:
            data['bet_on']['num_bet'] = beton_res[0]['number_of_bets']
            data['bet_on']['win'] = beton_res[0]['won_count']
            data['bet_on']['loss'] = beton_res[0]['lost_count']
            data['bet_on']['stake'] = "${:,.2f}".format(round(float(beton_res[0]['total_stake']), 2))
            data['bet_on']['pl'] = "${:,.2f}".format(round(float(beton_res[0]['total_p_l']), 2))
            data['bet_on']['yield'] = round(beton_res[0]['yield'], 2)

        beton_details_res = pd.read_sql(f"SELECT * FROM betting_table WHERE place = '{team_data['name']}' AND betdate LIKE '{year}%%' ORDER BY betdate DESC;", con = engine).to_dict('records')

        data['bet_on']['details'] = beton_details_res

        betagainst_res = pd.read_sql(f"SELECT 'Against team' AS total, COUNT(*) AS number_of_bets, \
                                    SUM(CASE WHEN status = '2' THEN 1 ELSE 0 END) AS won_count, \
                                    SUM(CASE WHEN status = '1' THEN 1 ELSE 0 END) AS lost_count, \
                                    to_char(ROUND(SUM(stake)::numeric, 2), 'FM999999999.00') AS total_stake, \
                                SUM(CASE \
                                        WHEN status::integer = 1 THEN stake * -1 \
                                        WHEN status::integer = 2 THEN wins \
                                    ELSE 0 \
                                    END) AS total_P_L, \
                                (SUM(CASE \
                                        WHEN status::integer = 1 THEN stake * -1 \
                                        WHEN status::integer = 2 THEN wins \
                                    ELSE 0 \
                                    END) / SUM(stake)) * 100 AS Yield \
                                FROM betting_table \
                                WHERE (team1 = '{team_data['name']}' OR team2 = '{team_data['name']}') AND place != '{team_data['name']}' AND betdate LIKE '{year}%%';", con = engine).to_dict('records')
        if len(betagainst_res) == 0 or betagainst_res[0]['total_stake'] == None:
            data['bet_against']['num_bet'] = 0
            data['bet_against']['win'] = 0
            data['bet_against']['loss'] = 0
            data['bet_against']['stake'] = 0
            data['bet_against']['pl'] = 0
            data['bet_against']['yield'] = 0
        else:
            data['bet_against']['num_bet'] = betagainst_res[0]['number_of_bets']
            data['bet_against']['win'] = betagainst_res[0]['won_count']
            data['bet_against']['loss'] = betagainst_res[0]['lost_count']
            data['bet_against']['stake'] = "${:,.2f}".format(round(float(betagainst_res[0]['total_stake']), 2))
            data['bet_against']['pl'] = "${:,.2f}".format(round(float(betagainst_res[0]['total_p_l']), 2))
            data['bet_against']['yield'] = round(betagainst_res[0]['yield'], 2)

        betagainst_details_res = pd.read_sql(f"SELECT * FROM betting_table WHERE (team1 = '{team_data['name']}' OR team2 = '{team_data['name']}') AND place != '{team_data['name']}' AND betdate LIKE '{year}%%' ORDER BY betdate DESC;", con = engine).to_dict('records')
        
        data['bet_against']['details'] = betagainst_details_res

        HeavyU_res = pd.read_sql(f"SELECT 'HeavyU' AS total, COUNT(*) AS number_of_bets, \
                                    SUM(CASE WHEN status = '2' THEN 1 ELSE 0 END) AS won_count, \
                                    SUM(CASE WHEN status = '1' THEN 1 ELSE 0 END) AS lost_count, \
                                    to_char(ROUND(SUM(stake)::numeric, 2), 'FM999999999.00') AS total_stake, \
                                SUM(CASE \
                                        WHEN status::integer = 1 THEN stake * -1 \
                                        WHEN status::integer = 2 THEN wins \
                                    ELSE 0 \
                                    END) AS total_P_L, \
                                (SUM(CASE \
                                        WHEN status::integer = 1 THEN stake * -1 \
                                        WHEN status::integer = 2 THEN wins \
                                    ELSE 0 \
                                    END) / SUM(stake)) * 100 AS Yield \
                                FROM betting_table \
                                WHERE CAST(odds AS DECIMAL) >= 150 AND betdate LIKE '{year}%%';", con = engine).to_dict('records')

        if len(HeavyU_res) == 0 or HeavyU_res[0]['total_stake'] == None:
            data['HeavyU']['num_bet'] = 0
            data['HeavyU']['win'] = 0
            data['HeavyU']['loss'] = 0
            data['HeavyU']['stake'] = 0
            data['HeavyU']['pl'] = 0
            data['HeavyU']['yield'] = 0
        else:
            data['HeavyU']['num_bet'] = HeavyU_res[0]['number_of_bets']
            data['HeavyU']['win'] = HeavyU_res[0]['won_count']
            data['HeavyU']['loss'] = HeavyU_res[0]['lost_count']
            data['HeavyU']['stake'] = "${:,.2f}".format(round(float(HeavyU_res[0]['total_stake']), 2))
            data['HeavyU']['pl'] = "${:,.2f}".format(round(float(HeavyU_res[0]['total_p_l']), 2))
            data['HeavyU']['yield'] = round(HeavyU_res[0]['yield'], 2)
        
        LightU_res = pd.read_sql(f"SELECT 'LightU' AS total, COUNT(*) AS number_of_bets, \
                                    SUM(CASE WHEN status = '2' THEN 1 ELSE 0 END) AS won_count, \
                                    SUM(CASE WHEN status = '1' THEN 1 ELSE 0 END) AS lost_count, \
                                    to_char(ROUND(SUM(stake)::numeric, 2), 'FM999999999.00') AS total_stake, \
                                SUM(CASE \
                                        WHEN status::integer = 1 THEN stake * -1 \
                                        WHEN status::integer = 2 THEN wins \
                                    ELSE 0 \
                                    END) AS total_P_L, \
                                (SUM(CASE \
                                        WHEN status::integer = 1 THEN stake * -1 \
                                        WHEN status::integer = 2 THEN wins \
                                    ELSE 0 \
                                    END) / SUM(stake)) * 100 AS Yield \
                                FROM betting_table \
                                WHERE CAST(odds AS DECIMAL) BETWEEN 115 AND 149 AND betdate LIKE '{year}%%';", con = engine).to_dict('records')
        if len(LightU_res) == 0 or LightU_res[0]['total_stake'] == None:
            data['LightU']['num_bet'] = 0
            data['LightU']['win'] = 0
            data['LightU']['loss'] = 0
            data['LightU']['stake'] = 0
            data['LightU']['pl'] = 0
            data['LightU']['yield'] = 0
        else:
            data['LightU']['num_bet'] = LightU_res[0]['number_of_bets']
            data['LightU']['win'] = LightU_res[0]['won_count']
            data['LightU']['loss'] = LightU_res[0]['lost_count']
            data['LightU']['stake'] = "${:,.2f}".format(round(float(LightU_res[0]['total_stake']), 2))
            data['LightU']['pl'] = "${:,.2f}".format(round(float(LightU_res[0]['total_p_l']), 2))
            data['LightU']['yield'] = round(LightU_res[0]['yield'], 2)
        
        Even_res = pd.read_sql(f"SELECT 'Even' AS total, COUNT(*) AS number_of_bets, \
                                    SUM(CASE WHEN status = '2' THEN 1 ELSE 0 END) AS won_count, \
                                    SUM(CASE WHEN status = '1' THEN 1 ELSE 0 END) AS lost_count, \
                                    to_char(ROUND(SUM(stake)::numeric, 2), 'FM999999999.00') AS total_stake, \
                                SUM(CASE \
                                        WHEN status::integer = 1 THEN stake * -1 \
                                        WHEN status::integer = 2 THEN wins \
                                    ELSE 0 \
                                    END) AS total_P_L, \
                                (SUM(CASE \
                                        WHEN status::integer = 1 THEN stake * -1 \
                                        WHEN status::integer = 2 THEN wins \
                                    ELSE 0 \
                                    END) / SUM(stake)) * 100 AS Yield \
                                FROM betting_table \
                                WHERE CAST(odds AS DECIMAL) BETWEEN -114 AND 114 AND betdate LIKE '{year}%%';", con = engine).to_dict('records')
        if len(Even_res) == 0 or Even_res[0]['total_stake'] == None:
            data['Even']['num_bet'] = 0
            data['Even']['win'] = 0
            data['Even']['loss'] = 0
            data['Even']['stake'] = 0
            data['Even']['pl'] = 0
            data['Even']['yield'] = 0
        else:
            data['Even']['num_bet'] = Even_res[0]['number_of_bets']
            data['Even']['win'] = Even_res[0]['won_count']
            data['Even']['loss'] = Even_res[0]['lost_count']
            data['Even']['stake'] = "${:,.2f}".format(round(float(Even_res[0]['total_stake']), 2))
            data['Even']['pl'] = "${:,.2f}".format(round(float(Even_res[0]['total_p_l']), 2))
            data['Even']['yield'] = round(Even_res[0]['yield'], 2)
        
        LightF_res = pd.read_sql(f"SELECT 'LightF' AS total, COUNT(*) AS number_of_bets, \
                                    SUM(CASE WHEN status = '2' THEN 1 ELSE 0 END) AS won_count, \
                                    SUM(CASE WHEN status = '1' THEN 1 ELSE 0 END) AS lost_count, \
                                    to_char(ROUND(SUM(stake)::numeric, 2), 'FM999999999.00') AS total_stake, \
                                SUM(CASE \
                                        WHEN status::integer = 1 THEN stake * -1 \
                                        WHEN status::integer = 2 THEN wins \
                                    ELSE 0 \
                                    END) AS total_P_L, \
                                (SUM(CASE \
                                        WHEN status::integer = 1 THEN stake * -1 \
                                        WHEN status::integer = 2 THEN wins \
                                    ELSE 0 \
                                    END) / SUM(stake)) * 100 AS Yield \
                                FROM betting_table \
                                WHERE CAST(odds AS DECIMAL) BETWEEN -149 AND -115 AND betdate LIKE '{year}%%';", con = engine).to_dict('records')
        
        if len(LightF_res) == 0 or LightF_res[0]['total_stake'] == None:
            data['LightF']['num_bet'] = 0
            data['LightF']['win'] = 0
            data['LightF']['loss'] = 0
            data['LightF']['stake'] = 0
            data['LightF']['pl'] = 0
            data['LightF']['yield'] = 0
        else:
            data['LightF']['num_bet'] = LightF_res[0]['number_of_bets']
            data['LightF']['win'] = LightF_res[0]['won_count']
            data['LightF']['loss'] = LightF_res[0]['lost_count']
            data['LightF']['stake'] = "${:,.2f}".format(round(float(LightF_res[0]['total_stake']), 2))
            data['LightF']['pl'] = "${:,.2f}".format(round(float(LightF_res[0]['total_p_l']), 2))
            data['LightF']['yield'] = round(LightF_res[0]['yield'], 2)
        
        HeavyF_res = pd.read_sql(f"SELECT 'HeavyF' AS total, COUNT(*) AS number_of_bets, \
                                    SUM(CASE WHEN status = '2' THEN 1 ELSE 0 END) AS won_count, \
                                    SUM(CASE WHEN status = '1' THEN 1 ELSE 0 END) AS lost_count, \
                                    to_char(ROUND(SUM(stake)::numeric, 2), 'FM999999999.00') AS total_stake, \
                                SUM(CASE \
                                        WHEN status::integer = 1 THEN stake * -1 \
                                        WHEN status::integer = 2 THEN wins \
                                    ELSE 0 \
                                    END) AS total_P_L, \
                                (SUM(CASE \
                                        WHEN status::integer = 1 THEN stake * -1 \
                                        WHEN status::integer = 2 THEN wins \
                                    ELSE 0 \
                                    END) / SUM(stake)) * 100 AS Yield \
                                FROM betting_table \
                                WHERE CAST(odds AS DECIMAL) <= -150 AND betdate LIKE '{year}%%';", con = engine).to_dict('records')
        
        if len(HeavyF_res) == 0 or HeavyF_res[0]['total_stake'] == None:
            data['HeavyF']['num_bet'] = 0
            data['HeavyF']['win'] = 0
            data['HeavyF']['loss'] = 0
            data['HeavyF']['stake'] = 0
            data['HeavyF']['pl'] = 0
            data['HeavyF']['yield'] = 0
        else:
            data['HeavyF']['num_bet'] = HeavyF_res[0]['number_of_bets']
            data['HeavyF']['win'] = HeavyF_res[0]['won_count']
            data['HeavyF']['loss'] = HeavyF_res[0]['lost_count']
            data['HeavyF']['stake'] = "${:,.2f}".format(round(float(HeavyF_res[0]['total_stake']), 2))
            data['HeavyF']['pl'] = "${:,.2f}".format(round(float(HeavyF_res[0]['total_p_l']), 2))
            data['HeavyF']['yield'] = round(HeavyF_res[0]['yield'], 2)

        price_res = pd.read_sql(f"SELECT game_id, game_date, away, home, CASE WHEN away = '{team_data['name']}' THEN away_open WHEN home = '{team_data['name']}' THEN home_open ELSE 0 END as open_price, \
                                CASE WHEN away = '{team_data['name']}' THEN away_close WHEN home = '{team_data['name']}' THEN home_close ELSE 0 END as close_price FROM odds_table WHERE (away = '{team_data['name']}' OR home = '{team_data['name']}') AND game_date LIKE '{year}%%' ORDER BY game_date DESC LIMIT 15;", con = engine).to_dict('records')   
        data['price'] = price_res

        players_res = pd.read_sql(f"SELECT p_id, p_name FROM team_table INNER JOIN player_table ON team_table.team_id = player_table.t_id WHERE team_table.team_name = '{team_data['name']}';", con = engine).to_dict('records')   

        data['players'] = players_res

        return data

@app.route('/starterprice', methods = ["GET", "POST"]) 
@login_required
def starterprice():
    if request.method == 'POST':
        player_data = request.get_json()
        playerID = player_data['pid']

        #engine = database.connect_to_db()

        today = date.today()
        today_str = today.strftime("%Y/%m/%d")
        year = today.year

        price_res = pd.read_sql(f"SELECT game_date, away, home,  CASE WHEN team = 'away' THEN away_open WHEN team = 'home' THEN home_open ELSE 0 END as open_price, \
                                CASE WHEN team = 'away' THEN away_close WHEN team = 'home' THEN home_close ELSE 0 END as close_price  FROM odds_table INNER JOIN pitcher_table oN odds_table.game_id = pitcher_table.game_id WHERE pitcher_table.playerid = '{playerID}' AND pitcher_table.role = 'starter' AND game_date LIKE '{year}%%' ORDER BY game_date DESC LIMIT 5;", con = engine).to_dict('records')   

        data = {}
        data['playerprice'] = price_res
        return data 

@app.route('/teams/<team_abbreviation>', methods=["GET", "POST"])
@login_required
def team(team_abbreviation): 
    
    team_info = mlb.lookup_team(team_abbreviation)[0]
    team_id = team_info['id']
    team_name = team_info['name']
    roster = mlb.get('team_roster', params = {'teamId' : team_id, 'date' : date.today()})['roster']

    
    return render_template("MLB/team.html", team = team_abbreviation, team_name = team_name, roster = roster)

@app.route('/update_data', methods = ["POST"])
def update_data(): 
    backup_database()
    update_date, update_time, last_record, num_games_added = database.update_database()
    update_league_average()
    update_data = {'update_date': update_date, 'update_time': update_time, 'last_record': last_record, 'games_added': num_games_added}
    schedule.update_schedule()
    update_data = jsonify(update_data = update_data)

    #engine = database.connect_to_db()
    game_sched = mlb.schedule(start_date = date.today())

    playerData = {}

    for game in game_sched:
        playerData[game['game_id']] = {}
        playerData[game['game_id']]['away_batter'] = []
        playerData[game['game_id']]['home_batter'] = []
        playerData[game['game_id']]['away_pitcher'] = []
        playerData[game['game_id']]['home_pitcher'] = []
        playerData[game['game_id']]['name'] = {}
        away_batter_atbats = {}
        home_batter_atbats = {}
        away_pitcher_atbats = {}
        home_pitcher_atbats = {}
        away_pitcher_played = {}
        home_pitcher_played = {}
        away_batter = []
        home_batter = []
        away_pitcher = []
        home_pitcher = []
        data = mlb.boxscore_data(game['game_id'])
        game_date = data['gameId'][:10]
        away_team = data['teamInfo']['away']['abbreviation']
        home_team = data['teamInfo']['home']['abbreviation']

        away_batter_res = pd.read_sql(text(f"SELECT * FROM (SELECT * FROM game_table WHERE away_team = '{data['teamInfo']['away']['abbreviation']}' or home_team = '{data['teamInfo']['away']['abbreviation']}' ORDER BY game_date DESC LIMIT 30) games INNER JOIN batter_table ON games.game_id = batter_table.game_id \
            WHERE (games.away_team='{data['teamInfo']['away']['abbreviation']}' AND batter_table.team = 'away') OR (games.home_team='{data['teamInfo']['away']['abbreviation']}' AND batter_table.team = 'home');"), con = engine).to_dict('records')

        home_batter_res = pd.read_sql(text(f"SELECT * FROM (SELECT * FROM game_table WHERE away_team = '{data['teamInfo']['home']['abbreviation']}' or home_team = '{data['teamInfo']['home']['abbreviation']}' ORDER BY game_date DESC LIMIT 30) games INNER JOIN batter_table ON games.game_id = batter_table.game_id \
            WHERE (games.away_team='{data['teamInfo']['home']['abbreviation']}' AND batter_table.team = 'away') OR (games.home_team='{data['teamInfo']['home']['abbreviation']}' AND batter_table.team = 'home');"), con = engine).to_dict('records')


        for away_player in away_batter_res:
            if away_player['playerid'] in away_batter_atbats:
                away_batter_atbats[away_player['playerid']] += int(away_player['atbats'])          
            else:
                away_batter_atbats[away_player['playerid']] = int(away_player['atbats'])

        for home_player in home_batter_res:
            if home_player['playerid'] in home_batter_atbats:
                home_batter_atbats[home_player['playerid']] += int(home_player['atbats'])
            else:
                home_batter_atbats[home_player['playerid']] = int(home_player['atbats'])

        away_batter_atbats_list = sorted(away_batter_atbats.items(), key=lambda x:x[1], reverse = True)
        away_batter_sort_atbats = dict(away_batter_atbats_list)

        home_batter_atbats_list = sorted(home_batter_atbats.items(), key=lambda x:x[1], reverse = True)
        home_batter_sort_atbats = dict(home_batter_atbats_list)

        away_pitcher_res = pd.read_sql(text(f"SELECT * FROM (SELECT * FROM game_table WHERE away_team = '{data['teamInfo']['away']['abbreviation']}' or home_team = '{data['teamInfo']['away']['abbreviation']}' ORDER BY game_date DESC LIMIT 30) games INNER JOIN pitcher_table ON games.game_id = pitcher_table.game_id \
            WHERE (games.away_team='{data['teamInfo']['away']['abbreviation']}' AND pitcher_table.team = 'away' AND pitcher_table.role = 'bullpen') OR (games.home_team='{data['teamInfo']['away']['abbreviation']}' AND pitcher_table.team = 'home' AND pitcher_table.role = 'bullpen');"), con = engine).to_dict('records')

        home_pitcher_res = pd.read_sql(text(f"SELECT * FROM (SELECT * FROM game_table WHERE away_team = '{data['teamInfo']['home']['abbreviation']}' or home_team = '{data['teamInfo']['home']['abbreviation']}' ORDER BY game_date DESC LIMIT 30) games INNER JOIN pitcher_table ON games.game_id = pitcher_table.game_id \
            WHERE (games.away_team='{data['teamInfo']['home']['abbreviation']}' AND pitcher_table.team = 'away' AND pitcher_table.role = 'bullpen') OR (games.home_team='{data['teamInfo']['home']['abbreviation']}' AND pitcher_table.team = 'home' AND pitcher_table.role = 'bullpen');"), con = engine).to_dict('records')


        for away_player in away_pitcher_res:
            if away_player['playerid'] in away_pitcher_atbats:
                away_pitcher_atbats[away_player['playerid']] += int(away_player['atbats'])
            else:
                away_pitcher_atbats[away_player['playerid']] = int(away_player['atbats'])

            if away_player['playerid'] not in away_pitcher_played:
                away_pitcher_played[away_player['playerid']] = {}
                away_pitcher_played[away_player['playerid']]['gamedate'] = away_player['game_date']
                away_pitcher_played[away_player['playerid']]['count'] = 1
            else:
                # print((datetime.combine(date.today(), datetime.min.time()) - datetime.strptime(away_player['game_date'], '%Y/%m/%d')).days)
                if((datetime.strptime(away_player['game_date'], '%Y/%m/%d') - datetime.strptime(away_pitcher_played[away_player['playerid']]['gamedate'], '%Y/%m/%d')).days) == 1:
                    away_pitcher_played[away_player['playerid']]['count'] = 2
                else:
                    away_pitcher_played[away_player['playerid']]['count'] = 1

                away_pitcher_played[away_player['playerid']]['gamedate'] = away_player['game_date']

        for home_player in home_pitcher_res:
            if home_player['playerid'] in home_pitcher_atbats:
                home_pitcher_atbats[home_player['playerid']] += int(home_player['atbats'])
            else:
                home_pitcher_atbats[home_player['playerid']] = int(home_player['atbats'])

            if home_player['playerid'] not in home_pitcher_played:
                home_pitcher_played[home_player['playerid']] = {}
                home_pitcher_played[home_player['playerid']]['gamedate'] = home_player['game_date']
                home_pitcher_played[home_player['playerid']]['count'] = 1
            else:
                if((datetime.strptime(home_player['game_date'], '%Y/%m/%d') - datetime.strptime(home_pitcher_played[home_player['playerid']]['gamedate'], '%Y/%m/%d')).days) == 1:
                    home_pitcher_played[home_player['playerid']]['count'] = 2
                else:
                    home_pitcher_played[home_player['playerid']]['count'] = 1

                home_pitcher_played[home_player['playerid']]['gamedate'] = home_player['game_date']

        away_pitcher_atbats_list = sorted(away_pitcher_atbats.items(), key=lambda x:x[1], reverse = True)
        away_pitcher_sort_atbats = dict(away_pitcher_atbats_list)


        home_pitcher_atbats_list = sorted(home_pitcher_atbats.items(), key=lambda x:x[1], reverse = True)
        home_pitcher_sort_atbats = dict(home_pitcher_atbats_list)


        rosters = schedule.get_rosters(game['game_id'])
        name = {}

        for away in rosters['away']:
            if 'fullName' in away:
                name[str(away['id'])] = away['fullName'].replace("'", " ")
            else:
                name[str(away['id'])] = ''

        for home in rosters['home']:
            if 'fullName' in home:
                name[str(home['id'])] = home['fullName'].replace("'", " ")
            else:
                name[str(home['id'])] = ''

        count = 0
        for key in away_batter_sort_atbats.keys():
            if (count == 15):
                break

            if key not in name:
                continue

            away_batter.append(key)
            count += 1
        
        count = 0
        for key in home_batter_sort_atbats.keys():
            if (count == 15):
                break

            if key not in name:
                continue

            home_batter.append(key)
            count += 1
        
        count = 0
        for key in away_pitcher_sort_atbats.keys():
            if (count == 4):
                break

            if (datetime.combine(date.today(), datetime.min.time()) - datetime.strptime(away_pitcher_played[key]['gamedate'], '%Y/%m/%d')).days == 1 and away_pitcher_played[key]['count'] == 2:
                continue

            if key not in name:
                continue

            away_pitcher.append(key)
            count += 1

        count = 0
        for key in home_pitcher_sort_atbats.keys():
            if (count == 4):
                break

            if (datetime.combine(date.today(), datetime.min.time()) - datetime.strptime(home_pitcher_played[key]['gamedate'], '%Y/%m/%d')).days == 1 and home_pitcher_played[key]['count'] == 2:
                continue

            if key not in name:
                continue

            home_pitcher.append(key)
            count += 1

        playerData[game['game_id']]['away_batter'] = away_batter
        playerData[game['game_id']]['home_batter'] = home_batter
        playerData[game['game_id']]['away_pitcher'] = away_pitcher
        playerData[game['game_id']]['home_pitcher'] = home_pitcher
        playerData[game['game_id']]['name'] = name

    thread = threading.Thread(target=calculate, args=(playerData,))
    thread.start()
    winprob.scrappe_win_pro()

    return update_data

@app.route('/update_predicdata', methods = ["POST"])
def update_predicdata(): 
    modify_data = json.loads(request.form['data'])
    #engine = database.connect_to_db()

    if modify_data['team'] == 'away':
        if modify_data['modal'] == 'A':
            engine.execute(f"INSERT INTO predict_table(game_id, la_away_edge, la_away_betsize) VALUES('{modify_data['game_id']}', '{modify_data['Ev']}', '{modify_data['betSize']}') ON CONFLICT (game_id) DO UPDATE SET la_away_edge = excluded.la_away_edge, la_away_betsize = excluded.la_away_betsize;") 
        elif modify_data['modal'] == 'B':
            engine.execute(f"INSERT INTO predict_table(game_id, lb_away_edge, lb_away_betsize) VALUES('{modify_data['game_id']}', '{modify_data['Ev']}', '{modify_data['betSize']}') ON CONFLICT (game_id) DO UPDATE SET lb_away_edge = excluded.lb_away_edge, lb_away_betsize = excluded.lb_away_betsize;") 
    if modify_data['team'] == 'home':
        if modify_data['modal'] == 'A':
            engine.execute(f"INSERT INTO predict_table(game_id, la_home_edge, la_home_betsize) VALUES('{modify_data['game_id']}', '{modify_data['Ev']}', '{modify_data['betSize']}') ON CONFLICT (game_id) DO UPDATE SET la_home_edge = excluded.la_home_edge, la_home_betsize = excluded.la_home_betsize;") 
        elif modify_data['modal'] == 'B':
            engine.execute(f"INSERT INTO predict_table(game_id, lb_home_edge, lb_home_betsize) VALUES('{modify_data['game_id']}', '{modify_data['Ev']}', '{modify_data['betSize']}') ON CONFLICT (game_id) DO UPDATE SET lb_home_edge = excluded.lb_home_edge, lb_home_betsize = excluded.lb_home_betsize;") 

    return 'Success'

@app.route('/database', methods = ["GET", "POST"])
@login_required
def show_database(): 
    if session["state"] == 0:
        return redirect(url_for("show_betting"))
    #engine = database.connect_to_db()
    res = pd.read_sql("SELECT * FROM game_table", con = engine)
    res_15 = res.tail(10)
    cols = ['game_id', 'game_date', 'away_team', 'home_team', 'away_score', 'home_score']
    res_15_cols = res_15[cols]
    
    return render_template("MLB/database.html", data = list(res_15_cols.T.to_dict().values()))

@app.route('/showbetting', methods = ["GET", "POST"])
def show_betting():
    #engine = database.connect_to_db()
    if request.method == 'GET':
        return render_template("MLB/betting.html")

    modify_data = request.get_json()
    daystr = modify_data["gamedate"]

    if modify_data["status"] == 1 or modify_data["status"] == 2:
        global res
        res = pd.read_sql(f"SELECT * FROM betting_table WHERE betdate = '{modify_data['gamedate']}' AND team1 = '{modify_data['away']}' AND team2 = '{modify_data['home']}'AND place = '{modify_data['place']}';", con = engine)
        betstate = res.to_dict('records')

        win_count_res = pd.read_sql(f"SELECT COUNT(*) FROM staking_table WHERE result = 'W';", con = engine).to_dict('records')
        bet_count_res = pd.read_sql(f"SELECT COUNT(*) FROM staking_table WHERE result != 'P';", con = engine).to_dict('records')

        if modify_data["status"] == 1:
            engine.execute(f"UPDATE staking_table SET result = 'L', win_count = '{win_count_res[0]['count']}', bet_count = '{bet_count_res[0]['count'] + 1}',  bet_win = {round(win_count_res[0]['count'] / (bet_count_res[0]['count'] + 1) * 100, 2)}, pl_coeff = -1 * stake_size WHERE game_date = '{modify_data['gamedate']}' AND away = '{modify_data['away']}' AND home = '{modify_data['home']}' AND bet = '{modify_data['place']}';")
        elif modify_data["status"] == 2:
            engine.execute(f"UPDATE staking_table SET result = 'W', win_count = '{win_count_res[0]['count'] + 1}', bet_count = '{bet_count_res[0]['count'] + 1}',  bet_win = {round((win_count_res[0]['count'] + 1) / (bet_count_res[0]['count'] + 1) * 100, 2)}, pl_coeff = (decimal_odd -1) * stake_size WHERE game_date = '{modify_data['gamedate']}' AND away = '{modify_data['away']}' AND home = '{modify_data['home']}' AND bet = '{modify_data['place']}';")

        status = "L" if modify_data["status"] == 1 else "W"

        for bet in betstate:
            if bet['regstate'] == '0':
                index = smartContract.betIndex
                betindex = int(index) + 1
                engine.execute(f"UPDATE betting_table SET regstate = '1', betindex = '{betindex}' WHERE betid = '{bet['betid']}';")
                smartContract.createBetData(bet)
                # smartContract.changeBetStatus(betindex, status)

            betindex = int(bet['betindex'])

            # smartContract.changeBetStatus(betindex, status)

        engine.execute(f"UPDATE betting_table SET status = '{modify_data['status']}' WHERE betdate = '{modify_data['gamedate']}' AND team1 = '{modify_data['away']}' AND team2 = '{modify_data['home']}'AND place = '{modify_data['place']}';")

    elif modify_data["status"] == 3:
        res = engine.execute(f"SELECT regstate FROM betting_table WHERE betdate = '{modify_data['gamedate']}' AND team1 = '{modify_data['away']}' AND team2 = '{modify_data['home']}'AND place = '{modify_data['place']}';").fetchall()
        if int(res[0][0]) == 0:
            engine.execute(f"UPDATE betting_table SET regstate = '2' WHERE betdate = '{modify_data['gamedate']}' AND team1 = '{modify_data['away']}' AND team2 = '{modify_data['home']}'AND place = '{modify_data['place']}';")

    res = pd.read_sql(f"SELECT COUNT(betid), team1, team2, place, SUM(stake) as stake, SUM(wins) as wins, status FROM betting_table WHERE betdate = '{daystr}' AND game = 'baseball' AND regstate != '2' GROUP BY team1, team2, place, status;", con = engine)
    betdata = res.to_dict('records')
    
    for bet in betdata:
        dec = float(bet['wins']) / float(bet['stake']) + 1
        bet['odds'] = odds.decimalToAmerian(dec)

        if(bet["team1"] == bet["team2"]):
            bet["game"] = bet["team1"]
        else:    
            bet["game"] = bet["team1"] + " vs " + bet["team2"]

        if bet["status"] == "0":
            bet["status"] = "PENDING"
            bet["wins"] = "PENDING"
        elif bet["status"] == "1":
            bet["status"] = "L"
            bet["wins"] = -bet["stake"]
        elif bet["status"] == "2":
            bet["status"] = "W"


    stake = pd.read_sql(f"SELECT betdate, SUM(stake) stake, SUM(CASE WHEN status = '2' THEN wins ELSE 0 END) wins, SUM(CASE WHEN status = '1' THEN stake ELSE 0 END) losses FROM betting_table WHERE betdate = '{daystr}' GROUP BY betdate ORDER BY betdate;", con = engine).to_dict('records')
    
    data = {}
    data['bet'] = betdata
    data['stake'] = stake

    return data

@app.route('/reconciliation', methods = ["GET", "POST"])
def reconciliation():
    #engine = database.connect_to_db()
    if request.method == 'GET':
        site_res = pd.read_sql(f"SELECT * FROM site_list", con = engine).to_dict('records')
        return render_template("MLB/reconciliation.html", sitelist = site_res, admin = session["state"])

    request_data = request.get_json()

    startdate = request_data["startdate"]
    enddate = request_data["enddate"]
    betsite = request_data["betsite"]

    if betsite == 'All':
        res = pd.read_sql(f"SELECT betid, betdate, team1, team2, place, site, stake, wins, status FROM betting_table WHERE regstate != '2' AND betdate BETWEEN '{startdate}' AND '{enddate}' ORDER BY betdate, site, place;", con = engine)
    else:
        res = pd.read_sql(f"SELECT betid, betdate, team1, team2, place, site, stake, wins, status FROM betting_table WHERE site = '{betsite}' AND regstate != '2' AND betdate BETWEEN '{startdate}' AND '{enddate}' ORDER BY betdate, site, place;", con = engine)

    betdata = res.to_dict('records')
    
    for bet in betdata:
        dec = float(bet['wins']) / float(bet['stake']) + 1
        bet['odds'] = odds.decimalToAmerian(dec)

        if(bet["team1"] == bet["team2"]):
            bet["game"] = bet["team1"]
        else:    
            bet["game"] = bet["team1"] + " vs " + bet["team2"]

        if bet["status"] == "0":
            bet["status"] = "PENDING"
            bet["wins"] = "PENDING"
        elif bet["status"] == "1":
            bet["status"] = "L"
            bet["wins"] = -bet["stake"]
        elif bet["status"] == "2":
            bet["status"] = "W"


    if betsite == 'All':
        stake = pd.read_sql(f"SELECT SUM(stake) stake, SUM(CASE WHEN status = '2' THEN wins ELSE 0 END) wins, SUM(CASE WHEN status = '1' THEN stake ELSE 0 END) losses FROM betting_table WHERE regstate != '2' AND betdate BETWEEN '{startdate}' AND '{enddate}';", con = engine).to_dict('records')
    else:
        stake = pd.read_sql(f"SELECT SUM(stake) stake, SUM(CASE WHEN status = '2' THEN wins ELSE 0 END) wins, SUM(CASE WHEN status = '1' THEN stake ELSE 0 END) losses FROM betting_table WHERE site = '{betsite}' AND regstate != '2' AND betdate BETWEEN '{startdate}' AND '{enddate}';", con = engine).to_dict('records')
    
    data = {}
    data['bet'] = betdata
    data['stake'] = stake

    return data

@app.route('/season', methods = ["GET"]) 
@login_required
def season_state():
    bet_res = pd.read_sql(f"SELECT * FROM graph_table", con = engine).to_dict('records')

    pl, total = 0, 0
    data = {}

    for bet in bet_res:
        pl += float(bet["pl"])
        total += float(bet["risk"])

    if pl >= 0:
        data["color"] = "green"
    else:
        data["color"] = "red"


    print('pl=====>', pl)
    data['stake'] = "{:,.2f}".format(total)
    data['pl'] = "{:,.2f}".format(pl)
    yd = pl / total * 100
    data["yield"] = round(yd, 2)
    return render_template("MLB/season.html", data = data)

@app.route('/betting', methods = ["POST"])    
def betting_proc(): 
    data = {}
    betting_data = request.get_json()
    #engine = database.connect_to_db()
    current_GMT = time.gmtime()
    regtime = calendar.timegm(current_GMT)

    if betting_data['flag'] == 0:
        betting_table_sql = 'INSERT INTO betting_table(betdate, game, team1, team2, market, place, odds, stake, wins, status, site, regtime, regstate, betindex) '\
                        'VALUES (' + \
                        '\'' + betting_data["betdate"] + '\'' + ',' + '\'' + 'baseball' + '\'' + ','+  '\'' + betting_data["away"] + '\'' +  ',' + \
                        '\'' + betting_data["home"] + '\'' +  ',' + '\'' +  'Money' + '\'' +  ',' + '\'' + betting_data["place"] + '\'' +  ','\
                        '\'' + betting_data["odds"] + '\'' +  ',' + '\'' + betting_data["stake"] + '\'' +  ',' + '\'' + betting_data["wins"] + '\'' +  ',' + \
                        '\'' + '0' + '\'' +  ',' + '\'' + betting_data["site"] + '\'' +  ',' + '\'' + str(regtime) + '\'' +  ',' + '\'' + "0" + '\'' +  ',' + '\'' + "0" + '\''+ ');'
    
        engine.execute(betting_table_sql)

        decimal_odd = odds.decimalToAmerian(int(betting_data["odds"]))
        win_count_res = pd.read_sql(f"SELECT COUNT(*) FROM staking_table WHERE result = 'W' AND game_date != '{betting_data['betdate']}';", con = engine).to_dict('records')
        bet_count_res = pd.read_sql(f"SELECT COUNT(*) FROM staking_table WHERE game_date != '{betting_data['betdate']}';", con = engine).to_dict('records')

        win_precent = 0
        risk_coeff = 0
        stake_size = 0

        if bet_count_res[0]['count'] <= 20:
            win_percent = 0
            risk_coeff = 0
        else:
            win_percent = round(((win_count_res[0]['count'] + 291) / (bet_count_res[0]['count'] + 572)) * 100, 2)
            if win_percent > 49.25 and win_percent <= 49.75:
                risk_coeff = 0.1
            elif win_percent <= 49.25:
                risk_coeff = 0.5
            elif win_percent >= 50.25 and win_percent < 50.75:
                risk_coeff = -0.1
            elif win_percent >= 50.75:
                risk_coeff = -0.5
            else:
                risk_coeff = 0
        if bet_count_res[0]['count'] <= 20:
            stake_size = 25000
        else:
            stake_size = 40000 + risk_coeff * 40000

        query = text(f"""
            INSERT INTO staking_table
                (game_date, away, home, bet, american_odd, decimal_odd, bet_size, result, win_count, bet_count, bet_win, risk_coeff, stake_size)
            VALUES
                (:betdate, :away, :home, :place, :odds, :decimal_odd, :stake, 'P', :win_count, :bet_count, :win_percent, :risk_coeff, :stake_size)
            ON CONFLICT (game_date, away, home, bet)
            DO UPDATE SET
                bet_size = staking_table.bet_size + EXCLUDED.bet_size;
            """)

        engine.execute(query, {
            'betdate': betting_data['betdate'],
            'away': betting_data['away'],
            'home': betting_data['home'],
            'place': betting_data['place'],
            'odds': int(betting_data['odds']),
            'decimal_odd': 0,
            'stake': betting_data['stake'],
            'win_count': win_count_res[0]['count'],
            'bet_count': bet_count_res[0]['count'],
            'win_percent': win_percent,
            'risk_coeff': risk_coeff,
            'stake_size': stake_size
        })


    elif betting_data['flag'] == 1:
        betting_table_sql = f"UPDATE betting_table SET place = '{betting_data['place']}', odds = '{betting_data['odds']}', stake = '{betting_data['stake']}', wins = '{betting_data['wins']}', regtime = '{regtime}' WHERE betdate = '{betting_data['betdate']}' AND team1 = '{betting_data['away']}' AND team2 = '{betting_data['home']}' AND site = '{betting_data['site']}';"
    
        engine.execute(betting_table_sql)
    elif betting_data['flag'] == 2:
        betting_table_sql = f"UPDATE betting_table SET place = '{betting_data['place']}', odds = '{betting_data['odds']}', stake = '{betting_data['stake']}', wins = '{betting_data['wins']}', regtime = '{regtime}', site = '{betting_data['site']}' WHERE betid = '{betting_data['betid']}';"
    
        engine.execute(betting_table_sql)
    elif betting_data['flag'] == 3:
        betting_table_sql = f"DELETE FROM betting_table WHERE betdate = '{betting_data['betdate']}' AND team1 = '{betting_data['away']}' AND team2 = '{betting_data['home']}' AND site = '{betting_data['site']}';"
    
        engine.execute(betting_table_sql)
    data['result'] = 'OK'
    return jsonify(data)

@app.route("/download_game_table")
def get_game_csv_table():
    #engine = database.connect_to_db()
    csv = pd.read_sql("SELECT * FROM game_table", con = engine).to_csv()
    return Response(
        csv,
        mimetype="text/csv",
        headers={"Content-disposition":
                 f"attachment; filename = game_table.csv"})

@app.route("/download_pitcher_table")
def get_pitcher_csv_table():
    #engine = database.connect_to_db()
    csv = pd.read_sql("SELECT * FROM pitcher_table", con = engine).to_csv()
    return Response(
        csv,
        mimetype="text/csv",
        headers={"Content-disposition":
                 f"attachment; filename = pitcher_table.csv"})

@app.route("/download_batter_table")
def get_batter_csv_table():
    #engine = database.connect_to_db()
    csv = pd.read_sql("SELECT * FROM batter_table", con = engine).to_csv()
    return Response(
        csv,
        mimetype="text/csv",
        headers={"Content-disposition":
                 f"attachment; filename = batter_table.csv"})        

@app.route('/getNHLPlayerStats', methods = ["POST"])
def getNHLPlayerStats():
    data = json.loads(request.form['data'])
    game_id = data['game_id']
    data = {}
   
    skaterData = pd.read_sql(f"SELECT * FROM model_input WHERE game_id = '{game_id}' AND is_forward = '1' ORDER BY plays_for_home_team, weighted_average_time_on_ice DESC LIMIT 36;", con = engine_nhl).to_dict('records')
    goaltenderData = pd.read_sql(f"SELECT * FROM model_input WHERE game_id = '{game_id}' AND is_goaltender = '1' ORDER BY plays_for_home_team, weighted_average_time_on_ice DESC LIMIT 36;", con = engine_nhl).to_dict('records')
    data['skater'] = skaterData
    data['goaltender'] = goaltenderData
    
    return data

@app.route('/get_PlayerStats', methods = ["POST"])
def get_PlayerStats():
    data = json.loads(request.form['data'])
    game_id = data['game_id']
    type = data['type']
    batter_table = ''
    pitcher_table = ''
    data = {}

    if type == 0:
        batter_table = 'batter_stats'
        pitcher_table = 'pitcher_stats'
        data['model'] = 0
    elif type == 1:
        batter_table = 'batter_stats_c'
        pitcher_table = 'pitcher_stats_c'
        data['model'] = 1
    
    #engine = database.connect_to_db()
    
    batterData = pd.read_sql(f"SELECT * FROM {batter_table} WHERE game_id = '{game_id}' ORDER BY position;", con = engine).to_dict('records')
    pitcherData = pd.read_sql(f"SELECT * FROM {pitcher_table} WHERE game_id = '{game_id}' ORDER BY position;", con = engine).to_dict('records')
    data['batter'] = batterData
    data['pitcher'] = pitcherData
    
    return data

@app.route('/get_predict_players', methods = ["POST"])
def get_predict_players(): 
    #engine = database.connect_to_db()
    game_id = str(json.loads(request.form['data']))
    print(game_id)
    
    away_batter = []
    home_batter = []
    away_starter = []
    home_starter = []
    away_name = ''
    home_name = ''

    game_res = pd.read_sql(f"SELECT away_name, home_name FROM schedule WHERE game_id = '{game_id}';", con = engine).to_dict('records')

    if len(game_res) > 0:
        away_name = game_res[0]['away_name']
        home_name = game_res[0]['home_name']

    batter_res = pd.read_sql(f"SELECT player_id, player_name, team FROM predict_batter_stats WHERE game_id = '{game_id}' AND role = 'recent';", con = engine).to_dict('records')
    for el in batter_res:
        if el['team'] == 'away':
            away_batter.append(el)
        if el['team'] == 'home':
            home_batter.append(el)
        
    pitcher_res = pd.read_sql(f"SELECT player_id, player_name, team FROM predict_pitcher_stats WHERE game_id = '{game_id}' AND role = 'recent';", con = engine).to_dict('records')
    for el in pitcher_res:
        if el['team'] == 'away':
            away_starter.append(el)
        if el['team'] == 'home':
            home_starter.append(el)

    data = {
        'awayName': away_name,
        'homeName': home_name,
        'awayBatters': away_batter,
        'homeBatters': home_batter,
        'awayPitchers': away_starter,
        'homePitchers': home_starter,
    }

    data = jsonify(data)
    return data

@app.route('/getWinPredict', methods = ["POST"])    
def getWinPredict():
    data = [] 
    players_data = request.get_json()
    
    # Fixing Names
    res = mlb.get('teams', params = {'sportId': 1})['teams']

    gameid = players_data['gameid']

    matchup = players_data['matchup'].split(" @ ")
    away_name, home_name = matchup[0], matchup[1]
    res = mlb.get('teams', params = {'sportId': 1})['teams']

    team_dict = [{k:v for k,v in el.items() if k in ['name', 'teamName', 'abbreviation']} for el in res]
    team_dict = {el['teamName']:el['abbreviation'] for el in team_dict}

    away_name = team_dict[away_name]
    home_name = team_dict[home_name]

    combinations_list = list(combinations(players_data['away_i_batter'], 2))
    away_lists = [list(combination) for combination in combinations_list]

    combinations_list = list(combinations(players_data['home_i_batter'], 2))
    home_lists = [list(combination) for combination in combinations_list]

    for away_list in away_lists:
        awaybatter = players_data['away_f_batter'] + away_list
        for home_list in home_lists:
            homebatter = players_data['home_f_batter'] + home_list
            params = {'away_batters': awaybatter, 
            'home_batters': homebatter, 
            'away_starters': players_data['awaypitcher'], 
            'home_starters': players_data['homepitcher'],
            }
            params['savestate'] = False

            params['away_name'] = away_name
            params['home_name'] = home_name
            params['game_id'] = gameid

            win_predict = predict_c.get_probabilities(params, engine)
            preds_1c = np.round(100 * win_predict[0], 2)
            preds_1c = {'away_prob': preds_1c[0], 'home_prob': preds_1c[1]}
            params['preds_1c'] = preds_1c
            data.append(params)
            homebatter = []
        awaybatter = []
    resdata = {'data': data}
    print('resdata=======>', resdata)
    return jsonify(resdata) 

@app.route('/download_batter_data', methods = ["POST"])
def get_batter_csv_data():
    # game_id = str(json.loads(request.form['data']))
    # data = mlb.boxscore_data(game_id)
    # gamedate = data['gameId'][:10]
    # #engine = database.connect_to_db()
    # csv = pd.read_sql(f"SELECT * FROM current_game_batters WHERE game_id = '{game_id}';", con = engine, index_col = 'index')
    # if csv.empty:
    #     return 'No'
    # else:
    #     csv.drop(csv.iloc[:, 0:2], inplace=True, axis=1)
    #     for index, row in csv.iterrows():
    #         engine.execute(text(f"INSERT INTO batter_stats(game_id, game_date, position, player_id, career_atBats, career_avg, career_homeRuns, career_obp, career_ops, career_rbi, career_slg, career_strikeOuts, recent_atBats, recent_avg, recent_homeRuns, recent_obp, recent_ops, recent_rbi, recent_slg, recent_strikeOuts) \
    #                             VALUES('{game_id}', '{gamedate}', '{index}', '{int(row['player_id'])}', '{round(float(row['career_atBats']), 3)}', '{round(float(row['career_avg']), 3)}', '{round(float(row['career_homeRuns']), 3)}', '{round(float(row['career_obp']), 3)}', '{round(float(row['career_ops']), 3)}', '{round(float(row['career_rbi']), 3)}', '{round(float(row['career_slg']), 3)}', '{round(float(row['career_strikeOuts']), 3)}', '{round(float(row['recent_atBats']), 3)}', '{round(float(row['recent_avg']), 3)}', '{round(float(row['recent_homeRuns']), 3)}', '{round(float(row['recent_obp']), 3)}', '{round(float(row['recent_ops']), 3)}', '{round(float(row['recent_rbi']), 3)}', '{round(float(row['recent_slg']), 3)}', '{round(float(row['recent_strikeOuts']), 3)}') \
    #                                 ON CONFLICT ON CONSTRAINT unique_game_player DO UPDATE SET game_date = excluded.game_date, career_atBats = excluded.career_atBats, career_avg = excluded.career_avg, career_homeRuns = excluded.career_homeRuns, career_obp = excluded.career_obp, career_ops = excluded.career_ops, career_rbi = excluded.career_rbi, career_slg = excluded.career_slg, career_strikeOuts = excluded.career_strikeOuts, \
    #                                 recent_atBats = excluded.recent_atBats, recent_avg = excluded.recent_avg, recent_homeRuns = excluded.recent_homeRuns, recent_obp = excluded.recent_obp, recent_ops = excluded.recent_ops, recent_rbi = excluded.recent_rbi, recent_slg = excluded.recent_slg, recent_strikeOuts = excluded.recent_strikeOuts;"))
        return 'OK'
  
@app.route('/download_pitcher_data', methods = ["POST"])
def get_pitcher_csv_data(): 
    # game_id = str(json.loads(request.form['data']))
    # data = mlb.boxscore_data(game_id)
    # gamedate = data['gameId'][:10]
    # #engine = database.connect_to_db()
    # csv = pd.read_sql(f"SELECT * FROM current_game_pitchers WHERE game_id = '{game_id}';", con = engine, index_col = 'index')
    # if csv.empty:
    #     return 'No'
    # else:
    #     csv.drop(csv.iloc[:, 0:2], inplace=True, axis=1)
    #     pitchers = csv.T
    #     for index, row in pitchers.iterrows():
    #         engine.execute(text(f"INSERT INTO pitcher_stats(game_id, game_date, position, player_id, career_era, career_homeRuns, career_whip, career_battersFaced, recent_era, recent_homeRuns, recent_whip, recent_battersFaced) \
    #                             VALUES('{game_id}', '{gamedate}', '{index}', '{int(row['player_id'])}', '{round(float(row['career_era']), 3)}', '{round(float(row['career_homeRuns']), 3)}', '{round(float(row['career_whip']), 3)}', '{round(float(row['career_battersFaced']), 3)}', '{round(float(row['recent_era']), 3)}', '{round(float(row['recent_homeRuns']), 3)}', '{round(float(row['recent_whip']), 3)}', '{round(float(row['recent_battersFaced']), 3)}') \
    #                             ON CONFLICT ON CONSTRAINT unique_pitcher_player DO UPDATE SET game_date = excluded.game_date, career_era = excluded.career_era, career_homeRuns = excluded.career_homeRuns, career_whip = excluded.career_whip, career_battersFaced = excluded.career_battersFaced, recent_era = excluded.recent_era, recent_homeRuns = excluded.recent_homeRuns, recent_whip = excluded.recent_whip, recent_battersFaced = excluded.recent_battersFaced;"))
        return 'OK'
    
@app.route('/friend_page', methods = ["GET", "POST"]) 
@login_required
def friend_page():  
    #engine = database.connect_to_db()

    if request.method == 'GET':
        game_table = pd.read_sql(f"SELECT (team_name)tname, (team_abbr)abbreviation FROM team_table ORDER BY team_name;", con = engine).to_dict('records')
        print(game_table)
        return render_template("MLB/friend_team.html", data = game_table)

    if request.method == 'POST':
        team_data = request.get_json()
        data = {}
        
        count = 0
        if int(team_data['count']) > 180:
            count = 180
        else:
            count = int(team_data['count'])

        today = date.today()
        year = team_data['year']
        date_table = pd.read_sql(f"SELECT a.game_id, a.game_date, a.pos, a.oppoteam, p.playerid \
                                    FROM ( \
                                        SELECT game_id, game_date, \
                                            (CASE away_team WHEN '{team_data['abbr']}' THEN '1' ELSE '0' END) AS pos, \
                                            (CASE away_team WHEN '{team_data['abbr']}' THEN home_team ELSE away_team END) AS oppoteam \
                                        FROM game_table \
                                        WHERE (away_team = '{team_data['abbr']}' OR home_team = '{team_data['abbr']}') AND game_date LIKE '{year}%%' \
                                        ORDER BY game_date DESC \
                                        LIMIT {count} \
                                    ) a \
                                    LEFT JOIN pitcher_table p ON a.game_id = p.game_id \
                                        AND ( \
                                            (a.pos = '1' AND p.team = 'home' AND p.role = 'starter') OR \
                                            (a.pos = '0' AND p.team = 'away' AND p.role = 'starter') \
                                        ) \
                                    ORDER BY a.game_date;", con = engine).to_dict('records')
      
        if team_data['player'] == 'batter':
            game_table = pd.read_sql(f"SELECT p_name, atbats, position, substitution, pitcher FROM ( \
                            SELECT table1.game_date, table1.game_id, table1.p_id, table1.p_name, batter_table.atbats, batter_table.position, batter_table.substitution, batter_table.pitcher \
                            FROM \
                            (SELECT * \
                            FROM \
                            (SELECT game_id, game_date, (CASE away_team WHEN '{team_data['abbr']}' THEN '1' ELSE '0' END)pos, (CASE away_team WHEN '{team_data['abbr']}' THEN home_team ELSE away_team END)oppoteam \
                            FROM game_table WHERE (away_team = '{team_data['abbr']}' OR home_team = '{team_data['abbr']}') AND game_date LIKE '{year}%%' ORDER BY game_date DESC LIMIT '{count}') game_schudle \
                            CROSS JOIN \
                            (SELECT player_table.p_name, player_table.p_id FROM player_table INNER JOIN team_table ON player_table.t_id = team_table.team_id WHERE team_table.team_name = '{team_data['name']}')player \
                            ) table1 \
                            LEFT JOIN batter_table \
                            ON (table1.p_id = batter_table.playerid AND table1.game_id = batter_table.game_id) \
                            ) t \
                            GROUP BY game_date, game_id, p_id, p_name, atbats, position, substitution, pitcher \
                            ORDER BY p_name, game_date;", con = engine).to_dict('records')
        elif team_data['player'] == 'pitcher':
            game_table = pd.read_sql(f"SELECT p_name, atbats, pitchesthrown, role, batter FROM ( \
                            SELECT table1.game_date, table1.game_id, table1.p_id, table1.p_name, pitcher_table.atbats, pitcher_table.pitchesthrown, pitcher_table.role, pitcher_table.batter \
                            FROM \
                            (SELECT * \
                            FROM \
                            (SELECT game_id, game_date, (CASE away_team WHEN '{team_data['abbr']}' THEN '1' ELSE '0' END)pos, (CASE away_team WHEN '{team_data['abbr']}' THEN home_team ELSE away_team END)oppoteam \
                            FROM game_table WHERE (away_team = '{team_data['abbr']}' OR home_team = '{team_data['abbr']}') AND game_date LIKE '{year}%%' ORDER BY game_date DESC LIMIT '{count}') game_schudle \
                            CROSS JOIN \
                            (SELECT player_table.p_name, player_table.p_id FROM player_table INNER JOIN team_table ON player_table.t_id = team_table.team_id WHERE team_table.team_name = '{team_data['name']}')player \
                            ) table1 \
                            LEFT JOIN pitcher_table \
                            ON (table1.p_id = pitcher_table.playerid AND table1.game_id = pitcher_table.game_id) \
                            ) t \
                            GROUP BY game_date, game_id, p_id, p_name, atbats, pitchesthrown, role, batter \
                            ORDER BY p_name, game_date;", con = engine).to_dict('records')

        game_date = {}

        i=0

        for el in date_table:
            game_date[str(i)] = {}
            game_date[str(i)]['oppoteam'] = el['oppoteam']
            game_date[str(i)]['pos'] = el['pos']
            game_date[str(i)]['game_date'] = el['game_date']

            url = f"https://statsapi.mlb.com/api/v1/people/{el['playerid']}"
            response = requests.get(url)
            if response.status_code == 200:
                result = response.json()
                hander = result['people'][0]['batSide']['code']
            else:
                hander = 'R'

            game_date[str(i)]['hander'] = hander
            i+=1

        data={}
        data['game_date'] = game_date
        data['game_table'] = game_table
        data['name'] = team_data['name']
        data['abbr'] = team_data['abbr']
    
        return data

@app.route('/position_page', methods = ["POST"]) 
@login_required
def position_page():  
    #engine = database.connect_to_db()
    data = {}
    team_data = request.get_json()
    total_res = pd.read_sql(text(f"SELECT COUNT(game_date)count FROM game_table WHERE game_date LIKE '{team_data['year']}%%';"), con = engine).to_dict('records')
    if(total_res) == 0:
        total_count = 0
    else:    
        total_count = total_res[0]['count']
    game_res = pd.read_sql(text(f"SELECT COUNT(game_date)count FROM position WHERE team = '{team_data['abbr']}' AND game_date LIKE '{team_data['year']}%%';"), con = engine).to_dict('records')
    # game_res = pd.read_sql(text(f"SELECT COUNT(game_date)count FROM game_table WHERE (away_team = '{team_data['abbr']}' OR home_team = '{team_data['abbr']}') AND game_date LIKE '{team_data['year']}%%';"), con = engine).to_dict('records')
    if(game_res) == 0:
        game_count = 0
    else:    
        game_count = game_res[0]['count']
    c_res = pd.read_sql(text(f"WITH RankedNames AS (SELECT c, DENSE_RANK() OVER(ORDER BY COUNT(*) DESC) AS c_rank, COUNT(*) AS c_count FROM position WHERE team = '{team_data['abbr']}' AND game_date LIKE '{team_data['year']}%%' GROUP BY c) SELECT c, c_rank, c_count FROM RankedNames;"), con = engine).to_dict('records')
    b1_res = pd.read_sql(text(f"WITH RankedNames AS (SELECT b1, DENSE_RANK() OVER(ORDER BY COUNT(*) DESC) AS b1_rank, COUNT(*) AS b1_count FROM position WHERE team = '{team_data['abbr']}' AND game_date LIKE '{team_data['year']}%%' GROUP BY b1) SELECT b1, b1_rank, b1_count FROM RankedNames;"), con = engine).to_dict('records')
    b2_res = pd.read_sql(text(f"WITH RankedNames AS (SELECT b2, DENSE_RANK() OVER(ORDER BY COUNT(*) DESC) AS b2_rank, COUNT(*) AS b2_count FROM position WHERE team = '{team_data['abbr']}' AND game_date LIKE '{team_data['year']}%%' GROUP BY b2) SELECT b2, b2_rank, b2_count FROM RankedNames;"), con = engine).to_dict('records')    
    b3_res = pd.read_sql(text(f"WITH RankedNames AS (SELECT b3, DENSE_RANK() OVER(ORDER BY COUNT(*) DESC) AS b3_rank, COUNT(*) AS b3_count FROM position WHERE team = '{team_data['abbr']}' AND game_date LIKE '{team_data['year']}%%' GROUP BY b3) SELECT b3, b3_rank, b3_count FROM RankedNames;"), con = engine).to_dict('records')    
    ss_res = pd.read_sql(text(f"WITH RankedNames AS (SELECT ss, DENSE_RANK() OVER(ORDER BY COUNT(*) DESC) AS ss_rank, COUNT(*) AS ss_count FROM position WHERE team = '{team_data['abbr']}' AND game_date LIKE '{team_data['year']}%%' GROUP BY ss) SELECT ss, ss_rank, ss_count FROM RankedNames;"), con = engine).to_dict('records')
    lf_res = pd.read_sql(text(f"WITH RankedNames AS (SELECT lf, DENSE_RANK() OVER(ORDER BY COUNT(*) DESC) AS lf_rank, COUNT(*) AS lf_count FROM position WHERE team = '{team_data['abbr']}' AND game_date LIKE '{team_data['year']}%%' GROUP BY lf) SELECT lf, lf_rank, lf_count FROM RankedNames;"), con = engine).to_dict('records')
    cf_res = pd.read_sql(text(f"WITH RankedNames AS (SELECT cf, DENSE_RANK() OVER(ORDER BY COUNT(*) DESC) AS cf_rank, COUNT(*) AS cf_count FROM position WHERE team = '{team_data['abbr']}' AND game_date LIKE '{team_data['year']}%%' GROUP BY cf) SELECT cf, cf_rank, cf_count FROM RankedNames;"), con = engine).to_dict('records')
    rf_res = pd.read_sql(text(f"WITH RankedNames AS (SELECT rf, DENSE_RANK() OVER(ORDER BY COUNT(*) DESC) AS rf_rank, COUNT(*) AS rf_count FROM position WHERE team = '{team_data['abbr']}' AND game_date LIKE '{team_data['year']}%%' GROUP BY rf) SELECT rf, rf_rank, rf_count FROM RankedNames;"), con = engine).to_dict('records')
    dh_res = pd.read_sql(text(f"WITH RankedNames AS (SELECT dh, DENSE_RANK() OVER(ORDER BY COUNT(*) DESC) AS dh_rank, COUNT(*) AS dh_count FROM position WHERE team = '{team_data['abbr']}' AND game_date LIKE '{team_data['year']}%%' GROUP BY dh) SELECT dh, dh_rank, dh_count FROM RankedNames;"), con = engine).to_dict('records')
    
    data['total_count'] = total_count
    data['game_count'] = game_count
    data['c'] = c_res
    data['b1'] = b1_res
    data['b2'] = b2_res
    data['b3'] = b3_res
    data['ss'] = ss_res
    data['lf'] = lf_res
    data['cf'] = cf_res
    data['rf'] = rf_res
    data['dh'] = dh_res

    print(data)


    return data

@app.route('/bullpen_page', methods = ["POST"]) 
@login_required
def bullpen_page():  
    #engine = database.connect_to_db()
    data = {}
    data['players'] = []
    team_data = request.get_json()
    player_res = pd.read_sql(text(f"WITH RankedNames AS (SELECT playerid, COUNT(*) AS dh_count \
            FROM (SELECT a.game_date, a.away_team, b.* FROM game_table a INNER JOIN pitcher_table b ON a.game_id = b.game_id WHERE ((a.away_team = '{team_data['abbr']}' AND b.team ='away') OR (a.home_team = '{team_data['abbr']}' AND b.team = 'home')) \
            AND b.role = 'bullpen' AND a.game_date LIKE '{team_data['year']}%%') c GROUP BY playerid), \
            LastGameDate AS ( SELECT playerid, MAX(game_date) AS last_game_date, DENSE_RANK() OVER (ORDER BY MAX(game_date) DESC) AS dh_rank FROM ( SELECT a.game_date, a.away_team, b.* \
            FROM game_table a INNER JOIN pitcher_table b ON a.game_id = b.game_id WHERE ((a.away_team = '{team_data['abbr']}' AND b.team ='away') OR (a.home_team = '{team_data['abbr']}' AND b.team = 'home')) \
            AND b.role = 'bullpen' AND a.game_date LIKE '{team_data['year']}%%') c GROUP BY playerid) SELECT rn.playerid, dh_rank, dh_count, lgd.last_game_date \
            FROM RankedNames rn JOIN LastGameDate lgd ON rn.playerid = lgd.playerid ORDER BY dh_rank, lgd.last_game_date DESC;"), con = engine).to_dict('records')

    current_date = datetime.now().date()
    
    for el in player_res:
        player={}
        target_date = datetime.strptime(el['last_game_date'], "%Y/%m/%d").date()
        delta = current_date - target_date
        days_difference = delta.days
        if (days_difference > 15):
            continue

        player['rest'] = days_difference
        player['playerid'] = el['playerid']

        url = f"https://statsapi.mlb.com/api/v1/people/{el['playerid']}"
        response = requests.get(url)
        if response.status_code == 200:
            result = response.json()
            name = result['people'][0]['fullName']
            hander = result['people'][0]['batSide']['code']
            player_name = name.replace("'", " ") + "   " + hander
        else:
            player_name = el['playerid']

        player['name'] = player_name
        player['game'] = el['dh_count']
        
        game_date = datetime.today()
        player_df = sanitycheck.get_starter_df(el['playerid'], team_data['year'])
    
        pitcher_stat_list=[
            'runs', 'doubles', 'triples', 'homeRuns', 'strikeOuts', 'baseOnBalls', 'hits', 'atBats', 
            'stolenBases', 'inningsPitched', 'wins', 'losses', 'holds', 'blownSave',
            'pitchesThrown', 'strikes', 'rbi', 'era', 'whip', 'obp']

    
        recent_data = {}
        career_data = {}

        if len(player_df) > 0 : 
            recent_games, games, recent_data= sanitycheck.process_recent_starter_data(player_df, game_date, pitcher_stat_list)
            career_data = sanitycheck.process_career_starter_data(el['playerid'], games, recent_games, pitcher_stat_list, game_date)
            player['recent'] = {}
            player['recent']['HR'] = recent_data['HR']
            player['recent']['ERA'] = recent_data['ERA']
            player['recent']['WHIP'] = recent_data['WHIP']
            player['recent']['BF'] = recent_data['BattersFaced']

            player['career'] = {}
            player['career']['HR'] = career_data['HR']
            player['career']['ERA'] = career_data['ERA']
            player['career']['WHIP'] = career_data['WHIP']
            player['career']['BF'] = career_data['BattersFaced']
        else: 
            player['recent'] = {}
            player['recent']['HR'] = 0
            player['recent']['ERA'] = 0
            player['recent']['WHIP'] = 0
            player['recent']['BF'] = 0

            player['career'] = {}
            player['career']['HR'] = 0
            player['career']['ERA'] = 0
            player['career']['WHIP'] = 0
            player['career']['BF'] = 0

        
        data['players'].append(player)

    return data

@app.route('/updateTeam', methods = ["POST"])
def update_P_T_table():
    #engine = database.connect_to_db()

    # exec(open("./modify_atbat.py").read(), globals())

    res = mlb.get('teams', params={'sportId':1})['teams']

    team_dict = [{k:v for k,v in el.items() if k in ['name', 'abbreviation', 'clubName']} for el in res]

    engine.execute(text("DROP TABLE IF EXISTS team_table;"))
    engine.execute(text("DROP TABLE IF EXISTS player_table;"))

    engine.execute(text("CREATE TABLE IF NOT EXISTS team_table(team_id TEXT, team_name TEXT, team_abbr TEXT, club_name TEXT);"))
    engine.execute(text("CREATE TABLE IF NOT EXISTS player_table(p_id TEXT, p_name TEXT, t_id TEXT);"))

    # team_data = request.get_json()

    for el in team_dict:
        team_id = mlb.lookup_team(el['name'])[0]['id']

        query1 = f"INSERT INTO team_table(team_id, team_name, team_abbr, club_name) VALUES('{team_id}', '{el['name']}', '{el['abbreviation']}', '{el['clubName']}');"

        engine.execute(text(query1)) 
        
        team_roster = {}
        team_roster = mlb.get('team_roster', params = {'teamId':team_id, 'date':date.today()})['roster']
        team_roster = [el['person'] for el in team_roster]
        team_roster = [{k:v for k,v in el.items() if k!='link'} for el in team_roster]

        for item in team_roster:
            p_name = item['fullName'].replace("'", " ")
            query2 = f"INSERT INTO player_table(p_id, p_name, t_id) VALUES('{item['id']}', '{p_name}','{team_id}');"

            engine.execute(text(query2))

    return 'OK'   

@app.route('/showstats', methods = ["GET"])
@login_required
def showstats(): 
    today_schedule = schedule.get_schedule()
    return render_template("MLB/showstats.html", schedule = today_schedule)

@app.route('/selectPlayer', methods = ["GET"])
@login_required
def selectPlayer(): 
    today_schedule = schedule.get_schedule()
    return render_template("MLB/selectplayer.html", schedule = today_schedule)

@app.route('/getLastGameStatus', methods = ["POST"])
def getLastGameStatus(): 
    req_data = request.get_json()
    boxscore = mlb.boxscore_data(req_data['gameid'])
    length = len(boxscore['gameBoxInfo'])
    data ={}
    data['state'] = length
    return data 

@app.route('/getLineupStatus', methods = ["POST"])
def getLineupStatus(): 
    req_data = request.get_json()
    rosters = schedule.get_rosters(req_data['gameid'])
    awaystate = not bool(rosters['position']['away'])
    homestate = not bool(rosters['position']['home'])

    data ={}
    if awaystate:
        data['away'] = 0
    else:
        data['away'] = 1
    
    if homestate:
        data['home'] = 0
    else:
        data['home'] = 1

    return data 

@app.route('/getWinStatus', methods = ["POST"])
def getWinStatus(): 
    req_data = request.get_json()
    boxscore = mlb.boxscore_data(req_data['gameid'])
    away_score = boxscore['awayBattingTotals']['r']
    home_score = boxscore['homeBattingTotals']['r']
    att_exists = False
    t_exists = False

    for item in boxscore['gameBoxInfo']:
        if item.get('label') == 'Att':
            att_exists = True
        elif item.get('label') == 'T':
            t_exists = True

    data ={}
    data['away_score'] = 0
    data['home_score'] = 0

    if att_exists == True and t_exists == True:
        data['away_score'] = away_score
        data['home_score'] = home_score 

    return data 

@app.route('/getTarget', methods = ["POST"])
def getTarget(): 
    req_data = request.get_json()
    #engine = database.connect_to_db()
    res = pd.read_sql(f"SELECT * FROM predict_table WHERE game_id = '{req_data['gameid']}';", con = engine).to_dict('records')

    return res 

@app.route('/startPrediction', methods = ["POST"])
def startPrediction():
    predictionData = json.loads(request.form['data'])

    thread = threading.Thread(target=calculate, args=(predictionData,))
    
    # Start the thread
    thread.start()
    return redirect(url_for("index"))

# @socketio.on('connect')
# def on_connect():
#     print('Client connected')

# @socketio.on('disconnect')
# def on_disconnect():
#     print('Client disconnected')


@app.route('/liveodds', methods=['POST'])
def liveOdds():
    odd_values = request.get_json()
    socketio.emit('update_odd_values', odd_values['data'])
    return jsonify({'status': 'success', 'data': odd_values}), 200


# @socketio.on('send_odd_values')
# def handle_odd_values(data):
#     print('Received odd values:', data)
#     socketio.emit('update_odd_values', data)

@app.route('/market')
def market():
    #engine = database.connect_to_db()
    # site_res = pd.read_sql(f"SELECT * FROM site_list", con = engine).to_dict('records')
    # return render_template('market.html', sitelist = site_res)
    return render_template('MLB/market.html')

def calculate(predictionData):
    today  = date.today()
    #engine = database.connect_to_db()
    output_date = today.strftime("%Y/%m/%d")

    batter_stat_list = ['home_score', 'away_score', 'atBats', 'avg', 'baseOnBalls', 'doubles', 'hits', 'homeRuns', 'obp', 'ops', 'playerId', 'rbi', 'runs', 
                        'slg', 'strikeOuts', 'triples', 'season', 'singles']
    pitcher_stat_list=['atBats', 'baseOnBalls', 'blownSave', 'doubles', 'earnedRuns', 'era', 'hits', 'holds', 'homeRuns', 'inningsPitched', 
        'losses', 'pitchesThrown', 'playerId', 'rbi', 'runs', 'strikeOuts', 'strikes', 'triples', 'whip',  'wins']
    
    for gameid in predictionData:
        away_batters = predictionData[gameid]['away_batter']
        for away_batter in away_batters:
            player_df = batting_c.get_batter_df(away_batter, output_date, engine)
            recent_batter_stats, games = batting_c.process_recent_batter_data(player_df, output_date, '', batter_stat_list, engine)
            career_batter_data = batting_c.process_career_batter_data(games, batter_stat_list)

            engine.execute(text(f"INSERT INTO predict_batter_stats(game_date, game_id, player_id, player_name, team, role, atBats, avg, baseOnBalls, doubles, hits, homeRuns, obp, ops, rbi, runs, slg, strikeOuts, triples, singles, difficulty) \
                                    VALUES('{output_date}', '{gameid}', '{away_batter}', '{predictionData[gameid]['name'][str(away_batter)]}', 'away', 'recent', '{round(float(recent_batter_stats['atBats']), 3)}', '{round(float(recent_batter_stats['avg']), 3)}', '{round(float(recent_batter_stats['baseOnBalls']), 3)}', '{round(float(recent_batter_stats['doubles']), 3)}', '{round(float(recent_batter_stats['hits']), 3)}', '{round(float(recent_batter_stats['homeRuns']), 3)}', '{round(float(recent_batter_stats['obp']), 3)}', '{round(float(recent_batter_stats['ops']), 3)}', '{round(float(recent_batter_stats['rbi']), 3)}', '{round(float(recent_batter_stats['runs']), 3)}', '{round(float(recent_batter_stats['slg']), 3)}', '{round(float(recent_batter_stats['strikeOuts']), 3)}', '{round(float(recent_batter_stats['triples']), 3)}', '{round(float(recent_batter_stats['singles']), 3)}', '{round(float(recent_batter_stats['difficulty']), 3)}')\
                                    ON CONFLICT ON CONSTRAINT predict_batter_stats_key DO UPDATE SET atBats = excluded.atBats, avg = excluded.avg, baseOnBalls = excluded.baseOnBalls, doubles = excluded.doubles, hits = excluded.hits, homeRuns = excluded.homeRuns, obp = excluded.obp, ops = excluded.ops, rbi = excluded.rbi, runs = excluded.runs, slg = excluded.slg, strikeOuts = excluded.strikeOuts, triples = excluded.triples, singles = excluded.singles, difficulty = excluded.difficulty;"))
            engine.execute(text(f"INSERT INTO predict_batter_stats(game_date, game_id, player_id, player_name, team, role, atBats, avg, baseOnBalls, doubles, hits, homeRuns, obp, ops, rbi, runs, slg, strikeOuts, triples, singles, difficulty) \
                                    VALUES('{output_date}', '{gameid}', '{away_batter}', '{predictionData[gameid]['name'][str(away_batter)]}', 'away', 'career', '{round(float(career_batter_data['atBats']), 3)}', '{round(float(career_batter_data['avg']), 3)}', '{round(float(career_batter_data['baseOnBalls']), 3)}', '{round(float(career_batter_data['doubles']), 3)}', '{round(float(career_batter_data['hits']), 3)}', '{round(float(career_batter_data['homeRuns']), 3)}', '{round(float(career_batter_data['obp']), 3)}', '{round(float(career_batter_data['ops']), 3)}', '{round(float(career_batter_data['rbi']), 3)}', '{round(float(career_batter_data['runs']), 3)}', '{round(float(career_batter_data['slg']), 3)}', '{round(float(career_batter_data['strikeOuts']), 3)}', '{round(float(career_batter_data['triples']), 3)}', '{round(float(career_batter_data['singles']), 3)}', '1')\
                                    ON CONFLICT ON CONSTRAINT predict_batter_stats_key DO UPDATE SET atBats = excluded.atBats, avg = excluded.avg, baseOnBalls = excluded.baseOnBalls, doubles = excluded.doubles, hits = excluded.hits, homeRuns = excluded.homeRuns, obp = excluded.obp, ops = excluded.ops, rbi = excluded.rbi, runs = excluded.runs, slg = excluded.slg, strikeOuts = excluded.strikeOuts, triples = excluded.triples, singles = excluded.singles, difficulty = excluded.difficulty;"))


        home_batters = predictionData[gameid]['home_batter']
        for home_batter in home_batters:
            player_df = batting_c.get_batter_df(home_batter, output_date, engine)
            recent_batter_stats, games = batting_c.process_recent_batter_data(player_df, output_date, '', batter_stat_list, engine)
            career_batter_data = batting_c.process_career_batter_data(games, batter_stat_list)

            engine.execute(text(f"INSERT INTO predict_batter_stats(game_date, game_id, player_id, player_name, team, role, atBats, avg, baseOnBalls, doubles, hits, homeRuns, obp, ops, rbi, runs, slg, strikeOuts, triples, singles, difficulty) \
                                    VALUES('{output_date}', '{gameid}', '{home_batter}', '{predictionData[gameid]['name'][str(home_batter)]}', 'home', 'recent', '{round(float(recent_batter_stats['atBats']), 3)}', '{round(float(recent_batter_stats['avg']), 3)}', '{round(float(recent_batter_stats['baseOnBalls']), 3)}', '{round(float(recent_batter_stats['doubles']), 3)}', '{round(float(recent_batter_stats['hits']), 3)}', '{round(float(recent_batter_stats['homeRuns']), 3)}', '{round(float(recent_batter_stats['obp']), 3)}', '{round(float(recent_batter_stats['ops']), 3)}', '{round(float(recent_batter_stats['rbi']), 3)}', '{round(float(recent_batter_stats['runs']), 3)}', '{round(float(recent_batter_stats['slg']), 3)}', '{round(float(recent_batter_stats['strikeOuts']), 3)}', '{round(float(recent_batter_stats['triples']), 3)}', '{round(float(recent_batter_stats['singles']), 3)}', '{round(float(recent_batter_stats['difficulty']), 3)}')\
                                    ON CONFLICT ON CONSTRAINT predict_batter_stats_key DO UPDATE SET atBats = excluded.atBats, avg = excluded.avg, baseOnBalls = excluded.baseOnBalls, doubles = excluded.doubles, hits = excluded.hits, homeRuns = excluded.homeRuns, obp = excluded.obp, ops = excluded.ops, rbi = excluded.rbi, runs = excluded.runs, slg = excluded.slg, strikeOuts = excluded.strikeOuts, triples = excluded.triples, singles = excluded.singles, difficulty = excluded.difficulty;"))
            engine.execute(text(f"INSERT INTO predict_batter_stats(game_date, game_id, player_id, player_name, team, role, atBats, avg, baseOnBalls, doubles, hits, homeRuns, obp, ops, rbi, runs, slg, strikeOuts, triples, singles, difficulty) \
                                    VALUES('{output_date}', '{gameid}', '{home_batter}', '{predictionData[gameid]['name'][str(home_batter)]}', 'home', 'career', '{round(float(career_batter_data['atBats']), 3)}', '{round(float(career_batter_data['avg']), 3)}', '{round(float(career_batter_data['baseOnBalls']), 3)}', '{round(float(career_batter_data['doubles']), 3)}', '{round(float(career_batter_data['hits']), 3)}', '{round(float(career_batter_data['homeRuns']), 3)}', '{round(float(career_batter_data['obp']), 3)}', '{round(float(career_batter_data['ops']), 3)}', '{round(float(career_batter_data['rbi']), 3)}', '{round(float(career_batter_data['runs']), 3)}', '{round(float(career_batter_data['slg']), 3)}', '{round(float(career_batter_data['strikeOuts']), 3)}', '{round(float(career_batter_data['triples']), 3)}', '{round(float(career_batter_data['singles']), 3)}', '1')\
                                    ON CONFLICT ON CONSTRAINT predict_batter_stats_key DO UPDATE SET atBats = excluded.atBats, avg = excluded.avg, baseOnBalls = excluded.baseOnBalls, doubles = excluded.doubles, hits = excluded.hits, homeRuns = excluded.homeRuns, obp = excluded.obp, ops = excluded.ops, rbi = excluded.rbi, runs = excluded.runs, slg = excluded.slg, strikeOuts = excluded.strikeOuts, triples = excluded.triples, singles = excluded.singles, difficulty = excluded.difficulty;"))

        away_starters = predictionData[gameid]['away_pitcher']
        for away_starter in away_starters:
            player_df = starters_c.get_starter_df(away_starter, output_date, engine)
            recent_pitcher_stats, games = starters_c.process_recent_starter_data(player_df, output_date, [], pitcher_stat_list, engine)
            career_pitcher_data = starters_c.process_career_starter_data(games, pitcher_stat_list)

            engine.execute(text(f"INSERT INTO predict_pitcher_stats(game_date, game_id, player_id, player_name, team, role, atBats, baseOnBalls, blownsaves, doubles, earnedRuns, era, hits, holds, homeRuns, inningsPitched, losses, pitchesThrown, rbi, runs, strikeOuts, strikes, triples, whip, wins, difficulty) \
                                    VALUES('{output_date}', '{gameid}', '{away_starter}', '{predictionData[gameid]['name'][str(away_starter)]}', 'away', 'recent', '{round(float(recent_pitcher_stats['atBats']), 3)}', '{round(float(recent_pitcher_stats['baseOnBalls']), 3)}', '{round(float(recent_pitcher_stats['blownsaves']), 3)}', '{round(float(recent_pitcher_stats['doubles']), 3)}', '{round(float(recent_pitcher_stats['earnedRuns']), 3)}', '{round(float(recent_pitcher_stats['era']), 3)}', '{round(float(recent_pitcher_stats['hits']), 3)}', '{round(float(recent_pitcher_stats['holds']), 3)}', '{round(float(recent_pitcher_stats['homeRuns']), 3)}', '{round(float(recent_pitcher_stats['inningsPitched']), 3)}', '{round(float(recent_pitcher_stats['losses']), 3)}', '{round(float(recent_pitcher_stats['pitchesThrown']), 3)}', '{round(float(recent_pitcher_stats['rbi']), 3)}', '{round(float(recent_pitcher_stats['runs']), 3)}', '{round(float(recent_pitcher_stats['strikeOuts']), 3)}', '{round(float(recent_pitcher_stats['strikes']), 3)}', '{round(float(recent_pitcher_stats['triples']), 3)}', '{round(float(recent_pitcher_stats['whip']), 3)}', '{round(float(recent_pitcher_stats['wins']), 3)}', '{round(float(recent_pitcher_stats['difficulty']), 3)}')\
                                    ON CONFLICT ON CONSTRAINT predict_pitcher_stats_key DO UPDATE SET atBats = excluded.atBats, baseOnBalls = excluded.baseOnBalls, blownsaves = excluded.blownsaves, doubles = excluded.doubles, earnedRuns = excluded.earnedRuns, era = excluded.era, hits = excluded.hits, holds = excluded.holds, homeRuns = excluded.homeRuns, inningsPitched = excluded.inningsPitched, losses = excluded.losses, pitchesThrown = excluded.pitchesThrown, rbi = excluded.rbi, runs = excluded.runs, strikeOuts = excluded.strikeOuts, strikes = excluded.strikes, triples = excluded.triples, whip = excluded.whip, wins = excluded.wins, difficulty = excluded.difficulty;"))
            engine.execute(text(f"INSERT INTO predict_pitcher_stats(game_date, game_id, player_id, player_name, team, role, atBats, baseOnBalls, blownsaves, doubles, earnedRuns, era, hits, holds, homeRuns, inningsPitched, losses, pitchesThrown, rbi, runs, strikeOuts, strikes, triples, whip, wins, difficulty) \
                                    VALUES('{output_date}', '{gameid}', '{away_starter}', '{predictionData[gameid]['name'][str(away_starter)]}', 'away', 'career', '{round(float(career_pitcher_data['atBats']), 3)}', '{round(float(career_pitcher_data['baseOnBalls']), 3)}', '{round(float(career_pitcher_data['blownsaves']), 3)}', '{round(float(career_pitcher_data['doubles']), 3)}', '{round(float(career_pitcher_data['earnedRuns']), 3)}', '{round(float(career_pitcher_data['era']), 3)}', '{round(float(career_pitcher_data['hits']), 3)}', '{round(float(career_pitcher_data['holds']), 3)}', '{round(float(career_pitcher_data['homeRuns']), 3)}', '{round(float(career_pitcher_data['inningsPitched']), 3)}', '{round(float(career_pitcher_data['losses']), 3)}', '{round(float(career_pitcher_data['pitchesThrown']), 3)}', '{round(float(career_pitcher_data['rbi']), 3)}', '{round(float(career_pitcher_data['runs']), 3)}', '{round(float(career_pitcher_data['strikeOuts']), 3)}', '{round(float(career_pitcher_data['strikes']), 3)}', '{round(float(career_pitcher_data['triples']), 3)}', '{round(float(career_pitcher_data['whip']), 3)}', '{round(float(career_pitcher_data['wins']), 3)}', '1')\
                                    ON CONFLICT ON CONSTRAINT predict_pitcher_stats_key DO UPDATE SET atBats = excluded.atBats, baseOnBalls = excluded.baseOnBalls, blownsaves = excluded.blownsaves, doubles = excluded.doubles, earnedRuns = excluded.earnedRuns, era = excluded.era, hits = excluded.hits, holds = excluded.holds, homeRuns = excluded.homeRuns, inningsPitched = excluded.inningsPitched, losses = excluded.losses, pitchesThrown = excluded.pitchesThrown, rbi = excluded.rbi, runs = excluded.runs, strikeOuts = excluded.strikeOuts, strikes = excluded.strikes, triples = excluded.triples, whip = excluded.whip, wins = excluded.wins, difficulty = excluded.difficulty;"))

        home_starters = predictionData[gameid]['home_pitcher']
        for home_starter in home_starters:
            player_df = starters_c.get_starter_df(home_starter, output_date, engine)
            recent_pitcher_stats, games = starters_c.process_recent_starter_data(player_df, output_date, [], pitcher_stat_list, engine)
            career_pitcher_data = starters_c.process_career_starter_data(games, pitcher_stat_list)
            
            engine.execute(text(f"INSERT INTO predict_pitcher_stats(game_date, game_id, player_id, player_name, team, role, atBats, baseOnBalls, blownsaves, doubles, earnedRuns, era, hits, holds, homeRuns, inningsPitched, losses, pitchesThrown, rbi, runs, strikeOuts, strikes, triples, whip, wins, difficulty) \
                                    VALUES('{output_date}', '{gameid}', '{home_starter}', '{predictionData[gameid]['name'][str(home_starter)]}', 'home', 'recent', '{round(float(recent_pitcher_stats['atBats']), 3)}', '{round(float(recent_pitcher_stats['baseOnBalls']), 3)}', '{round(float(recent_pitcher_stats['blownsaves']), 3)}', '{round(float(recent_pitcher_stats['doubles']), 3)}', '{round(float(recent_pitcher_stats['earnedRuns']), 3)}', '{round(float(recent_pitcher_stats['era']), 3)}', '{round(float(recent_pitcher_stats['hits']), 3)}', '{round(float(recent_pitcher_stats['holds']), 3)}', '{round(float(recent_pitcher_stats['homeRuns']), 3)}', '{round(float(recent_pitcher_stats['inningsPitched']), 3)}', '{round(float(recent_pitcher_stats['losses']), 3)}', '{round(float(recent_pitcher_stats['pitchesThrown']), 3)}', '{round(float(recent_pitcher_stats['rbi']), 3)}', '{round(float(recent_pitcher_stats['runs']), 3)}', '{round(float(recent_pitcher_stats['strikeOuts']), 3)}', '{round(float(recent_pitcher_stats['strikes']), 3)}', '{round(float(recent_pitcher_stats['triples']), 3)}', '{round(float(recent_pitcher_stats['whip']), 3)}', '{round(float(recent_pitcher_stats['wins']), 3)}', '{round(float(recent_pitcher_stats['difficulty']), 3)}')\
                                    ON CONFLICT ON CONSTRAINT predict_pitcher_stats_key DO UPDATE SET atBats = excluded.atBats, baseOnBalls = excluded.baseOnBalls, blownsaves = excluded.blownsaves, doubles = excluded.doubles, earnedRuns = excluded.earnedRuns, era = excluded.era, hits = excluded.hits, holds = excluded.holds, homeRuns = excluded.homeRuns, inningsPitched = excluded.inningsPitched, losses = excluded.losses, pitchesThrown = excluded.pitchesThrown, rbi = excluded.rbi, runs = excluded.runs, strikeOuts = excluded.strikeOuts, strikes = excluded.strikes, triples = excluded.triples, whip = excluded.whip, wins = excluded.wins, difficulty = excluded.difficulty;"))
            engine.execute(text(f"INSERT INTO predict_pitcher_stats(game_date, game_id, player_id, player_name, team, role, atBats, baseOnBalls, blownsaves, doubles, earnedRuns, era, hits, holds, homeRuns, inningsPitched, losses, pitchesThrown, rbi, runs, strikeOuts, strikes, triples, whip, wins, difficulty) \
                                    VALUES('{output_date}', '{gameid}', '{home_starter}', '{predictionData[gameid]['name'][str(home_starter)]}', 'home', 'career', '{round(float(career_pitcher_data['atBats']), 3)}', '{round(float(career_pitcher_data['baseOnBalls']), 3)}', '{round(float(career_pitcher_data['blownsaves']), 3)}', '{round(float(career_pitcher_data['doubles']), 3)}', '{round(float(career_pitcher_data['earnedRuns']), 3)}', '{round(float(career_pitcher_data['era']), 3)}', '{round(float(career_pitcher_data['hits']), 3)}', '{round(float(career_pitcher_data['holds']), 3)}', '{round(float(career_pitcher_data['homeRuns']), 3)}', '{round(float(career_pitcher_data['inningsPitched']), 3)}', '{round(float(career_pitcher_data['losses']), 3)}', '{round(float(career_pitcher_data['pitchesThrown']), 3)}', '{round(float(career_pitcher_data['rbi']), 3)}', '{round(float(career_pitcher_data['runs']), 3)}', '{round(float(career_pitcher_data['strikeOuts']), 3)}', '{round(float(career_pitcher_data['strikes']), 3)}', '{round(float(career_pitcher_data['triples']), 3)}', '{round(float(career_pitcher_data['whip']), 3)}', '{round(float(career_pitcher_data['wins']), 3)}', '1')\
                                    ON CONFLICT ON CONSTRAINT predict_pitcher_stats_key DO UPDATE SET atBats = excluded.atBats, baseOnBalls = excluded.baseOnBalls, blownsaves = excluded.blownsaves, doubles = excluded.doubles, earnedRuns = excluded.earnedRuns, era = excluded.era, hits = excluded.hits, holds = excluded.holds, homeRuns = excluded.homeRuns, inningsPitched = excluded.inningsPitched, losses = excluded.losses, pitchesThrown = excluded.pitchesThrown, rbi = excluded.rbi, runs = excluded.runs, strikeOuts = excluded.strikeOuts, strikes = excluded.strikes, triples = excluded.triples, whip = excluded.whip, wins = excluded.wins, difficulty = excluded.difficulty;"))

    return

@app.route('/price_request', methods = ["POST"])
def price_request():
    data = json.loads(request.form['data'])
    
    if(data['site'] == 'NHL'):
        query = text("""
                        INSERT INTO price_table (game_id, awayprice, homeprice, awaystate, homestate, bet, status, stake)
                        VALUES (:game_id, :awayprice, :homeprice, :awaystate, :homestate, :bet, :status, :stake)
                        ON CONFLICT (game_id) 
                        DO UPDATE SET 
                            awayprice = EXCLUDED.awayprice,
                            homeprice = EXCLUDED.homeprice,
                            awaystate = EXCLUDED.awaystate,
                            homestate = EXCLUDED.homestate,
                            bet = EXCLUDED.bet,
                            status = EXCLUDED.status,
                            stake = EXCLUDED.stake;
                    """)

        data = {
                    'game_id': data['gameid'],
                    'awayprice': data['awayprice'],
                    'homeprice': data['homeprice'],
                    'awaystate': '0',
                    'homestate': '0',
                    'bet': data['bet'],
                    'status': '0',
                    'stake' : data['stake']
                }
        engine_nhl.execute(query, data)
    return data

def calModelC(data):
    print('thread start', data)
    params = data['params'] 
    stake_size = data['stake_size'] 
    gameId = data['gameId'] 
    prediction_c = predict_c.get_probabilities(params, engine)
        
    preds_1c = prediction_c
    preds_1c = np.round(100 * preds_1c[0], 2)

    away_odd = 0
    home_odd = 0
    away_dec_odd = 0
    home_dec_odd = 0
    away_dec_odd = round(1.05 / (preds_1c[0] / 100), 2)
    away_odd = odds.decimalToAmerian(away_dec_odd)

    home_dec_odd = round(1.05 / (preds_1c[1] / 100), 2)
    home_odd = odds.decimalToAmerian(home_dec_odd)

    preds_1c = {'away_prob': preds_1c[0], 'home_prob': preds_1c[1], 'away_odd': away_odd, 'home_odd': home_odd, 'stake': stake_size}
    engine.execute(f"INSERT INTO predict_table(game_id, lc_away_prob, lc_home_prob, lc_away_odd, lc_home_odd) VALUES('{gameId}', '{preds_1c['away_prob']}', '{preds_1c['home_prob']}', '{preds_1c['away_odd']}', '{preds_1c['home_odd']}') ON CONFLICT (game_id) DO UPDATE SET lc_away_prob = excluded.lc_away_prob, lc_home_prob = excluded.lc_home_prob, lc_away_odd = excluded.lc_away_odd, lc_home_odd = excluded.lc_home_odd;")
    engine.execute(f"INSERT INTO win_percent_c(game_id, away_prob, home_prob) VALUES('{gameId}', '{preds_1c['away_prob']}', '{preds_1c['home_prob']}') ON CONFLICT (game_id) DO UPDATE SET away_prob = excluded.away_prob, home_prob = excluded.home_prob;")  
    prediction = {'model':'c', '1c': preds_1c}
    print('thread result', prediction)

    return

def update_league_average():
    #engine = database.connect_to_db()
    year = date.today().year
    print(year)
    batter_df = pd.read_sql(f"SELECT b.game_id, b.game_date, b.home_team, b.away_team, b.home_score, b.away_score, (a.atbats)atBats, a.avg, \
            (a.baseonballs)baseonBalls, a.doubles, a.hits, (a.homeruns)homeRuns, a.obp, a.ops, \
            (a.playerid)playerId, a.rbi, a.runs, a.slg, (a.strikeouts)strikeOuts, \
            a.triples FROM batter_table a LEFT JOIN game_table b ON a.game_id = b.game_id WHERE a.substitution = '0' AND b.game_date LIKE '{year}%%';", con = engine).to_dict('records')
    
    print(len(batter_df))
    atbats = 0
    hits = 0
    doubles = 0
    triples = 0
    b_homeruns = 0
    baseonballs = 0
    era = 0
    whip = 0
    rbi = 0
    strikeouts = 0

    for row in batter_df:
        atbats = atbats + float(row['atbats'])
        hits = hits + float(row['hits'])
        doubles = doubles + float(row['doubles'])
        triples = triples + float(row['triples'])
        b_homeruns = b_homeruns + float(row['homeruns'])
        baseonballs = baseonballs + float(row['baseonballs'])
        rbi = rbi + float(row['rbi'])
        strikeouts = strikeouts + float(row['strikeouts'])

    singles = hits-doubles-triples-b_homeruns
    avg = hits/atbats if atbats>0 else 0
    obp = (hits+baseonballs)/(atbats+baseonballs) if (atbats+baseonballs)>0 else 0
    slg = (singles+2*doubles+3*triples+4*b_homeruns)/atbats if atbats>0 else 0
    atbats = atbats / len(batter_df) if len(batter_df)>0 else 0
    b_homeruns = b_homeruns / len(batter_df) if len(batter_df)>0 else 0
    rbi = rbi / len(batter_df) if len(batter_df)>0 else 0
    strikeouts = strikeouts / len(batter_df) if len(batter_df)>0 else 0
    ops = obp + slg
    atbats = round(atbats, 3)
    rbi = round(rbi, 3)
    strikeouts = round(strikeouts, 3)
    b_homeruns = round(b_homeruns, 3)
    avg = round(avg, 3)
    obp = round(obp, 3)
    slg = round(slg, 3)
    ops = round(ops, 3)

    pitcher_df = pd.read_sql(f"SELECT b.game_id, b.game_date, b.home_team, b.away_team, b.home_score, b.away_score, (a.atbats)atBats, \
            (a.baseonballs)baseonBalls, a.blownsaves, a.doubles, (a.earnedruns)earnedRuns, a.era, a.hits, a.holds, (a.homeruns)homeRuns, \
            (a.inningspitched)inningsPitched, a.losses, (a.pitchesthrown)pitchesThrown, (a.playerid)playerId, a.rbi, a.runs, (a.strikeouts)strikeOuts, \
            a.strikes, a.triples, a.whip, a.wins FROM pitcher_table a LEFT JOIN game_table b ON a.game_id = b.game_id WHERE a.role = 'starter' AND a.batter = '0' AND b.game_date LIKE '{year}%%';", con = engine).to_dict('records')
    
    baseonballs = 0
    hits = 0
    inningspitched = 0
    earnedruns = 0
    battersfaced = 0
    atbats = 0
    p_homeruns = 0

    for row in pitcher_df:
        atbats = atbats + float(row['atbats'])
        p_homeruns = p_homeruns + float(row['homeruns'])
        hits = hits + float(row['hits'])
        baseonballs = baseonballs + float(row['baseonballs'])
        inningspitched = inningspitched + float(row['inningspitched'])
        earnedruns = earnedruns + float(row['earnedruns'])

    battersfaced = baseonballs + atbats
    era = 9*earnedruns/inningspitched if inningspitched>0 else 0
    whip = (baseonballs+hits)/inningspitched if inningspitched>0 else 0
    battersfaced = battersfaced / len(pitcher_df) if len(pitcher_df)>0 else 0
    p_homeruns = p_homeruns / len(pitcher_df) if len(pitcher_df)>0 else 0

    era = round(era, 3)
    whip = round(whip, 3)
    battersfaced = round(battersfaced, 3)
    p_homeruns = round(p_homeruns, 3)
    print(p_homeruns, battersfaced, era, whip)
    engine.execute(text(f"INSERT INTO league_average (year, avg, obp, slg, ops, era, whip) VALUES ('{year}', '{avg}', '{obp}', '{slg}', '{ops}', '{era}', '{whip}') ON CONFLICT (year) DO UPDATE SET avg = excluded.avg, obp = excluded.obp, slg = excluded.slg, ops = excluded.ops, era = excluded.era, whip = excluded.whip;"))   

# model_1a = None
# model_1b = None
# def load_models():
#     global model_1a
#     global model_1b
#     model_1a = pickle.load(open('algorithms/model_1a_v10.sav', 'rb'))
#     model_1b = pickle.load(open('algorithms/model_1b_v10.sav', 'rb'))

    return 

def backup_database():
    # Current date to append to the backup file's name
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Filename for the backup
    filename = f"./backup/{date_str}.sql"
    
    # PostgreSQL credentials
    db_username = "postgres"
    db_host = "localhost"
    db_port = "5432"
    db_name = "betmlb"
    db_password = "lucamlb123"  # Be cautious with password handling

    # Setting the PGPASSWORD environment variable
    os.environ['PGPASSWORD'] = db_password

    # Command to run pg_dump
    command = f"pg_dump -U {db_username} -h {db_host} -p {db_port} -d {db_name} -f {filename}"
    
    try:
        # Execute the pg_dump command
        subprocess.run(command, check=True, shell=True)
        print("Backup successful")
    finally:
        # Ensure that the password is cleared from the environment variables after running
        del os.environ['PGPASSWORD']

def print_date_time():
    current_GMT = time.gmtime()

    time_stamp = calendar.timegm(current_GMT)
    estimatestamp = time_stamp - 60 * 10

    #engine = database.connect_to_db()
    res = pd.read_sql(f"SELECT * FROM betting_table WHERE regstate = '0' AND game = 'baseball' AND regtime <= {estimatestamp} ORDER BY betid;", con = engine)
    betdata = res.to_dict('records')
    
    for bet in betdata:
        betIndex = smartContract.betIndex()
        print(betIndex)
        engine.execute(f"UPDATE betting_table SET regstate = '1', betindex = '{betIndex + 1}' WHERE betid = '{bet['betid']}';")
        smartContract.createBetData(bet)

def update_NHL():
    databaseNHL.update_database()
    return

scheduler = BackgroundScheduler()
scheduler.add_job(func=print_date_time, trigger="interval", seconds=600)
scheduler.start()

update_nhl = BackgroundScheduler()
update_nhl.add_job(update_NHL, 'cron', hour=10, minute=0)
update_nhl.start()

atexit.register(lambda: scheduler.shutdown())

if __name__ == '__main__':
    # app.run(ssl_context='adhoc')
    app.run(debug=True)
    