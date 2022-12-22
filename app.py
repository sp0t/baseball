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
from flask_basicauth import BasicAuth

# Modules
from functions import batting, predict, starters, smartContract
from schedule import schedule
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

mail = Mail(app)

users = {"username": "luca", "password": "betmlbluca4722"}

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
@login_required
def confirm_email(token):
    email = None
    try:
        email = confirm_token(token)
    except:
        return jsonify('The confirmation link is invalid or has expired.')
    
    engine = database.connect_to_db()
    res = engine.execute(f"SELECT confirmed FROM user_table WHERE username = '{email}';").fetchall()

    if res[0][0] == "1":    
        return jsonify('Account already confirmed. Please login.')
    else:
        engine.execute(f"UPDATE user_table SET confirmed_on = '{date.today()}', confirmed = '1' WHERE username = '{email}';")
        return redirect(url_for('show_betting'))

# Routes
@app.route('/', methods = ["GET", "POST"])
@login_required
def index(): 
    # if('user' in session and session['username'] != users['username']):
    #     return '<h1>You are not logged in.</h1>'
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

    today_schedule = schedule.get_schedule()                                                                                                                                                                                                                                                                                                                                                                                                                                                 
    engine = database.connect_to_db()
    last_update = pd.read_sql("SELECT * FROM updates", con = engine).iloc[-1]

    last_date, last_time, last_record = last_update["update_date"], last_update["update_time"], last_update["last_record"]

    return render_template("index.html", schedule = today_schedule, last_record = last_record, 
                           update_date = last_date, update_time = last_time)


@app.route('/login', methods = ["GET", "POST"])
def login(): 
    if request.method == 'GET':
        return render_template("login.html")

    user = request.get_json()
    engine = database.connect_to_db()

    print(user['username'])

    res = engine.execute(f"SELECT username, password, position, confirmed FROM user_table WHERE username = '{user['username']}';").fetchall()

    if res == []:
        return jsonify("User didn't registered")
    
    if res[0][3] == '0':
        return jsonify("NOCON")

    if sha256_crypt.verify(user["password"], res[0][1]) == True:
        session.permanent = True
        app.permanent_session_lifetime = timedelta(minutes=1)
        session["username"] = user['username']
        if res[0][2] == "0":
            session["state"] = 0
            return jsonify("user")
        elif res[0][2] == "1":
            session["state"] = 1
            return jsonify("admin")
    
    return jsonify("Password failed!")

@app.route('/signup', methods = ["POST"])
def signup(): 
    user = request.get_json()   
    today = date.today()

    engine = database.connect_to_db()
    res = engine.execute(f"SELECT username, confirmed FROM user_table WHERE username = '{user['username']}';").fetchall()

    print(res)

    if res !=[]:
        if res[0][1] == '0':
            return jsonify("NOCON")
        
        if res[0][1] == '1':
            return jsonify("Already regestered")

  
    password = sha256_crypt.encrypt(user["password"])
    engine.execute(f"INSERT INTO user_table(username, password, position, registered_on, confirmed ) VALUES('{user['username']}', '{password}', '0', '{today}', '0');")

    token = generate_confirmation_token(user['username'])

    confirm_url = "https://betmlb.me/confirm/" + token

    # print(html.strip())

    html = "To verify your mail click here. "

    url = "https://send.api.mailtrap.io/api/send"
    email = user['username']

    payload = "{\"from\":{\"email\":\"lucamaurelli@gmail.com\",\"name\":\"Betmlbme\"},\"to\":[{\"email\":\"" + email + "\"}],\"subject\":\"Confrim your mail!\",\"text\":\"" + html + "\",\"category\":\"Integration Test\"}"
    headers = {
    "Authorization": "Bearer fcc5c29e1926dd91538201eaef322987",
    "Content-Type": "application/json"
    }

    response = requests.request("POST", url, headers=headers, data=payload)


    return jsonify("NOCON")

@app.route('/changepassword', methods = ["POST"])
def changepassword(): 
    user = request.get_json()
    engine = database.connect_to_db()
    res = engine.execute(f"SELECT username, password, position FROM user_table WHERE user = '{user['username']}';").fetchall()
    password = sha256_crypt.encrypt("password")

    return

@app.route('/logout', methods = ["GET"])
def logout(): 
    session.clear()
    return redirect(url_for("login"))

@app.route('/get_game_info', methods = ["POST"])
def get_game_info(): 
    engine = database.connect_to_db()
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

@app.route('/make_prediction', methods = ["POST"])
def make_prediction():
    if request.method == 'POST': 
        
        # Get Form Data
    
        form_data = json.loads(request.form['data'])
        params = {'away_batters': form_data['away_batters'], 
                  'home_batters': form_data['home_batters'], 
                  'away_starter': form_data['away_starter'], 
                  'home_starter': form_data['home_starter']}
        
        # Fixing Names
        matchup = form_data['matchup'].split(" @ ")
        away_full_name, home_full_name = matchup[0], matchup[1]
        res = mlb.get('teams', params = {'sportId': 1})['teams']

        team_dict = [{k:v for k,v in el.items() if k in ['name', 'teamName', 'abbreviation']} for el in res]
        team_dict = {el['name']:el['abbreviation'] for el in team_dict}
        params['away_name'] = team_dict[away_full_name]
        params['home_name'] = team_dict[home_full_name]
        
        # Make Prediction
        predictions = predict.get_probabilities(params)
        
        preds_1a = predictions['1a']
        preds_1a = np.round(100 * preds_1a[0], 2)
        preds_1a = {'away_prob': preds_1a[0], 'home_prob': preds_1a[1]}
        
        preds_1b = predictions['1b']
        preds_1b = np.round(100 * preds_1b[0], 2)
        preds_1b = {'away_prob': preds_1b[0], 'home_prob': preds_1b[1]}
        
        prediction = {'1a': preds_1a, '1b': preds_1b}
        
        prediction = jsonify(prediction)
    
    return prediction

@app.route('/teams')
@login_required
def teams():
    if session["state"] == 0:
        return redirect(url_for("show_betting"))
    res = mlb.get('teams', params={'sportId':1})['teams']
    team_dict = [{k:v for k,v in el.items() if k in ['id', 'name', 'abbreviation', 'division', 'teamName']} for el in res]
    team_dict = {item['name']: item for item in team_dict}

    res = list(mlb.standings_data().values())
    for league in res: 
        for team in league['teams']: 
            team.update({'abbreviation':team_dict[team['name']]['abbreviation']})
            team.update({'name':team_dict[team['name']]['teamName']})
    al=res[:3]
    nl=res[3:]


    return render_template('teams.html', al = al, nl = nl)

@app.route('/teams/<team_abbreviation>', methods=["GET", "POST"])
@login_required
def team(team_abbreviation): 
    
    team_info = mlb.lookup_team(team_abbreviation)[0]
    team_id = team_info['id']
    team_name = team_info['name']
    roster = mlb.get('team_roster', params = {'teamId' : team_id, 'date' : date.today()})['roster']
    
    return render_template("team.html", team = team_abbreviation, team_name = team_name, roster = roster)

@app.route('/update_data', methods = ["POST"])
def update_data(): 
    
    update_date, update_time, last_record, num_games_added = database.update_database()
    update_data = {'update_date': update_date, 'update_time': update_time, 'last_record': last_record, 'games_added': num_games_added}
    schedule.update_schedule()
    update_data = jsonify(update_data = update_data)
    return update_data

@app.route('/database', methods = ["GET", "POST"])
@login_required
def show_database(): 
    if session["state"] == 0:
        return redirect(url_for("show_betting"))
    engine = database.connect_to_db()
    res = pd.read_sql("SELECT * FROM game_table", con = engine)
    res_15 = res.tail(10)
    cols = ['game_id', 'game_date', 'away_team', 'home_team', 'away_score', 'home_score']
    res_15_cols = res_15[cols]
    
    
    
    
    return render_template("database.html", data = list(res_15_cols.T.to_dict().values()))

@app.route('/showbetting', methods = ["GET", "POST"])
@login_required
def show_betting():
    engine = database.connect_to_db()
    if request.method == 'GET':
        return render_template("betting.html")

    modify_data = request.get_json()
    daystr = modify_data["gamedate"]

    if modify_data["status"] == 1 or modify_data["status"] == 2:
        global res
        res = pd.read_sql(f"SELECT * FROM betting_table WHERE game = 'baseball' AND betid = '{modify_data['betid']}';", con = engine)
        betstate = res.to_dict('records')

        if betstate[0]['regstate'] == '0':
            Index = smartContract.betIndex
            engine.execute(f"UPDATE betting_table SET regstate = '1', betindex = '{Index + 1}' WHERE betid = '{modify_data['betid']}';")
            smartContract.createBetData(betstate)

        res = engine.execute(f"SELECT betindex FROM betting_table WHERE betid = '{modify_data['betid']}';").fetchall()
        betIndex = int(res[0][0])
        status = "L" if modify_data["status"] == 1 else "W"
        smartContract.changeBetStatus(betIndex, status)
        engine.execute(f"UPDATE betting_table SET status = '{modify_data['status']}' WHERE betid = '{modify_data['betid']}';")
    elif modify_data["status"] == 3:
        res = engine.execute(f"SELECT regstate FROM betting_table WHERE betid = '{modify_data['betid']}';").fetchall()
        if int(res[0][0]) == 0:
            engine.execute(f"UPDATE betting_table SET regstate = '2' WHERE betid = '{modify_data['betid']}';")

    res = pd.read_sql(f"SELECT * FROM betting_table WHERE betdate = '{daystr}' AND game = 'baseball' AND regstate != '2' ORDER BY betindex;", con = engine)
    betdata = res.to_dict('records')
    
    for bet in betdata:
        if(bet["team1"] == bet["team2"]):
            bet["game"] = bet["team1"]
        else:    
            bet["game"] = bet["team1"] + " vs " + bet["team2"]

        if bet["status"] == "0":
            bet["status"] = "PENDING"
            bet["wins"] = "PENDING"
        elif bet["status"] == "1":
            bet["status"] = "L"
            bet["wins"] = "(" + bet["stake"] + ")"
        elif bet["status"] == "2":
            bet["status"] = "W"

    return betdata

@app.route('/season', methods = ["GET"]) 
@login_required
def season_state():
    
    engine = database.connect_to_db()
    res = pd.read_sql(f"SELECT stake, wins, status FROM betting_table WHERE game = 'baseball' AND regstate != '2' ORDER BY betid;", con = engine)
    seasondata = res.to_dict('records')
    stake, profit, losses = 0, 0, 0

    for item in seasondata:
        fwins = (item["wins"]).replace(",", "")
        fstake = (item["stake"]).replace(",", "") 
        stake += float(fstake)
        if(item["status"] == "1"):
            losses += float(fstake)
        elif(item["status"] == "2"):
            profit += float(fwins)
    data = {}
    data["stake"] = f'{stake:.2f}'
    data["profit"] = f'{profit:.2f}'
    data["losses"] = f'{losses:.2f}'

    return render_template("season.html", data = data)

@app.route('/betting', methods = ["POST"])    
def betting_proc(): 
    if request.method == 'POST':
        betting_data = request.get_json()
        engine = database.connect_to_db()
        for betting in betting_data:
            current_GMT = time.gmtime()
            regtime = calendar.timegm(current_GMT)

            betting_table_sql = 'INSERT INTO betting_table(betdate, game, team1, team2, market, place, odds, stake, wins, status, site, regtime, regstate, betindex) '\
                                'VALUES (' + \
                                '\'' + betting["gamedate"] + '\'' + ',' + '\'' + betting["game"].lower() + '\'' + ','+  '\'' + betting["team1"] + '\'' +  ',' + \
                                '\'' + betting["team2"] + '\'' +  ',' + '\'' + betting["market"] + '\'' +  ',' + '\'' + betting["place"] + '\'' +  ','\
                                '\'' + str(betting["odds"]) + '\'' +  ',' + '\'' + betting["stake"] + '\'' +  ',' + '\'' + betting["wins"] + '\'' +  ',' + \
                                '\'' + '0' + '\'' +  ',' + '\'' + betting["site"] + '\'' +  ',' + '\'' + str(regtime) + '\'' +  ',' + '\'' + "0" + '\'' +  ',' + '\'' + "0" + '\''+ ');'
            engine.execute(betting_table_sql)
    ret = "ok"
    return ret

@app.route("/download_game_table")
def get_game_csv_table():
    engine = database.connect_to_db()
    csv = pd.read_sql("SELECT * FROM game_table", con = engine).to_csv()
    return Response(
        csv,
        mimetype="text/csv",
        headers={"Content-disposition":
                 f"attachment; filename = game_table.csv"})

@app.route("/download_pitcher_table")
def get_pitcher_csv_table():
    engine = database.connect_to_db()
    csv = pd.read_sql("SELECT * FROM pitcher_table", con = engine).to_csv()
    return Response(
        csv,
        mimetype="text/csv",
        headers={"Content-disposition":
                 f"attachment; filename = pitcher_table.csv"})

@app.route("/download_batter_table")
def get_batter_csv_table():
    engine = database.connect_to_db()
    csv = pd.read_sql("SELECT * FROM batter_table", con = engine).to_csv()
    return Response(
        csv,
        mimetype="text/csv",
        headers={"Content-disposition":
                 f"attachment; filename = batter_table.csv"})        

@app.route('/download_batter_data')
def get_batter_csv_data(): 
    engine = database.connect_to_db()
    csv = pd.read_sql("SELECT * FROM current_game_batters", con = engine).to_csv()
    return Response(
        csv,
        mimetype="text/csv",
        headers={"Content-disposition":
                 f"attachment; filename = batter_data.csv"})
  
@app.route('/download_pitcher_data')
def get_pitcher_csv_data(): 
    engine = database.connect_to_db()
    csv = pd.read_sql("SELECT * FROM current_game_pitchers", con = engine).to_csv()
    return Response(
        csv,
        mimetype="text/csv",
        headers={"Content-disposition":
                 f"attachment; filename = pitcher_data.csv"})
      

# model_1a = None
# model_1b = None
# def load_models():
#     global model_1a
#     global model_1b
#     model_1a = pickle.load(open('algorithms/model_1a_v10.sav', 'rb'))
#     model_1b = pickle.load(open('algorithms/model_1b_v10.sav', 'rb'))

    return 

def print_date_time():
    current_GMT = time.gmtime()

    time_stamp = calendar.timegm(current_GMT)
    estimatestamp = time_stamp - 60 * 10

    engine = database.connect_to_db()
    res = pd.read_sql(f"SELECT * FROM betting_table WHERE regstate = '0' AND game = 'baseball' AND regtime <= {estimatestamp} ORDER BY betid;", con = engine)
    betdata = res.to_dict('records')
    
    for bet in betdata:
        betIndex = smartContract.betIndex
        engine.execute(f"UPDATE betting_table SET regstate = '1', betindex = '{betIndex + 1}' WHERE betid = '{bet['betid']}';")
        smartContract.createBetData(bet)

scheduler = BackgroundScheduler()
scheduler.add_job(func=print_date_time, trigger="interval", seconds=600)
scheduler.start()
# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())

if __name__ == '__main__':
    # app.run(ssl_context='adhoc')
    app.run(debug=True)
    