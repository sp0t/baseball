# Dependencies 
import pickle
from logging import raiseExceptions
from flask import Flask, render_template, request, Response, url_for, jsonify, redirect
from datetime import datetime, date
import sqlite3
import pandas as pd
import statsapi as mlb
import json
import numpy as np
from database import database
from flask_basicauth import BasicAuth

# Modules
from functions import batting, predict, starters
from schedule import schedule


# Connect App + DB
app = Flask(__name__)
app.secret_key = "^d@0U%['Plt7w,p"

# Password Protect
app.config['BASIC_AUTH_USERNAME'] = 'luca'
app.config['BASIC_AUTH_PASSWORD'] = 'betmlbluca4722'
basic_auth = BasicAuth(app)
app.config['BASIC_AUTH_FORCE'] = False



# Routes
@app.route('/', methods = ["GET", "POST"])
def index(): 
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
def teams():
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
def show_database(): 
    
    engine = database.connect_to_db()
    res = pd.read_sql("SELECT * FROM game_table", con = engine)
    res_15 = res.tail(10)
    cols = ['game_id', 'game_date', 'away_team', 'home_team', 'away_score', 'home_score']
    res_15_cols = res_15[cols]
    
    
    
    
    return render_template("database.html", data = list(res_15_cols.T.to_dict().values()))

@app.route('/betting', methods = ["GET", "POST"])
def betting_proc(): 
    if request.method == 'POST':
        betting_data = request.get_json()
        print(betting_data)
        # engine = database.connect_to_db()
        # print(data)
        # data = request.json
        # for bet in data:
        #     betsql = "INSERT INTO betting"
        #     engine.execute(betsql)
        test = "123"
        print(test)

        return test
    print("not recive from betting site")
    return render_template("team.html")

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
if __name__ == '__main__':
    app.run(ssl_context='adhoc')
    