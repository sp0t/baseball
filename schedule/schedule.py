import statsapi as mlb
import pandas as pd
from datetime import date, time, datetime, timedelta
from database import database
from functions import odds
from pytz import timezone
import math


def get_schedule(): 
    engine = database.connect_to_db()
    try: 
        schedule = list(pd.read_sql('SELECT * FROM schedule;', con = engine).T.to_dict().values())
    except: 
        schedule = get_schedule_from_mlb()
        for game in schedule: 
            game['betting'] = []
            game['predict'] = []

        return "Today's schedule can't be found. Try force-updating or waiting a few minutes to refresh!"
    
    res = mlb.get('teams', params = {'sportId': 1})['teams']
    team_dict = [{k:v for k,v in el.items() if k in ['name', 'teamName']} for el in res]
    team_dict = {el['name']:el['teamName'] for el in team_dict}
    schedule0 = []

    for el in schedule:
        if el['away_name'] in team_dict.keys() and el['home_name'] in team_dict.keys():
            schedule0.append(el.copy())

    for game in schedule0: 
        betting = list(pd.read_sql(f"SELECT team1, team2, betdate, site, SUM(stake) AS total_stake, SUM(wins) AS total_wins FROM betting_table WHERE team1 LIKE '{game['away_name']}%%' AND team2 LIKE '{game['home_name']}%%' AND betdate = '{date.today()}' GROUP BY team1, team2, betdate, site;", con = engine).T.to_dict().values())
        predict = list(pd.read_sql(f"SELECT * FROM predict_table WHERE game_id = '{game['game_id']}';", con = engine).T.to_dict().values())
        
        for bett in betting:
            data = list(pd.read_sql(f"SELECT * FROM betting_table WHERE team1 = '{bett['team1']}' AND team2 = '{bett['team2']}' AND betdate = '{bett['betdate']}' AND site = '{bett['site']}';", con = engine).T.to_dict().values())
            if data[0]['place'] == game['away_name']:
                bett['place'] = team_dict[game['away_name']]
            if data[0]['place'] == game['home_name']:
                bett['place'] = team_dict[game['home_name']]
            
            bett['status'] = data[0]['status']
            bett['site'] = bett['site']
            bett['odds'] = data[0]['odds']
            bett['stake'] = bett['total_stake']
            bett['wins'] = bett['total_wins']

        game['away_name'] = team_dict[game['away_name']]
        game['home_name'] = team_dict[game['home_name']]
        game['betting'] = betting
        if predict != []:
            if predict[0]['la_away_odd'] != None:
                predict[0]['la_away_odd'] = odds.americanToDecimal(float(predict[0]['la_away_odd']))
            if predict[0]['la_home_odd'] != None:
                predict[0]['la_home_odd'] = odds.americanToDecimal(float(predict[0]['la_home_odd']))
            if predict[0]['lb_away_odd'] != None:
                predict[0]['lb_away_odd'] = odds.americanToDecimal(float(predict[0]['lb_away_odd']))
            if predict[0]['lb_home_odd'] != None:
                predict[0]['lb_home_odd'] = odds.americanToDecimal(float(predict[0]['lb_home_odd']))
            if predict[0]['lc_away_odd'] != None:
                predict[0]['lc_away_odd'] = odds.americanToDecimal(float(predict[0]['lc_away_odd']))
            if predict[0]['lc_home_odd'] != None:
                predict[0]['lc_home_odd'] = odds.americanToDecimal(float(predict[0]['lc_home_odd']))

            if(predict[0]['la_away_prob'] != None and predict[0]['lb_away_prob'] != None ):
                predict[0]['away_prob'] = float(predict[0]['la_away_prob']) * 0.8 + float(predict[0]['lb_away_prob']) * 0.2
                predict[0]['home_prob'] = float(predict[0]['la_home_prob']) * 0.8 + float(predict[0]['lb_home_prob']) * 0.2
            else:
                predict[0]['away_prob'] = None
                predict[0]['home_prob'] = None

            if (predict[0]['away_prob'] != None and predict[0]['away_prob'] < 48):
                predict[0]['away_odd'] = 'No Bet'
            elif(predict[0]['away_prob'] == None):
                predict[0]['away_odd'] = None
            elif(predict[0]['la_away_odd'] != None and predict[0]['lb_away_odd'] != None):
                predict[0]['away_odd'] = predict[0]['la_away_odd'] * 0.8 + predict[0]['lb_away_odd'] * 0.2

            if(predict[0]['away_odd'] != None and predict[0]['away_odd'] != "No Bet"):
                predict[0]['away_odd'] = odds.decimalToAmerian(predict[0]['away_odd'])
            
            if (predict[0]['home_prob'] != None and predict[0]['home_prob'] < 48):
                predict[0]['home_odd'] = 'No Bet'
            elif(predict[0]['home_prob'] == None):
                predict[0]['home_odd'] = None
            elif(predict[0]['la_home_odd'] != None and predict[0]['lb_home_odd'] != None):
                predict[0]['home_odd'] = predict[0]['la_home_odd'] * 0.8 + predict[0]['lb_home_odd'] * 0.2

            if(predict[0]['home_odd'] != None and predict[0]['home_odd'] != "No Bet"):
                predict[0]['home_odd'] = odds.decimalToAmerian(predict[0]['home_odd'])

            game['predict'] = predict[0]
            
        else:
            game['predict'] = []

    return schedule0

def get_rosters(game_id):
    data = mlb.boxscore_data(game_id)

    away_team_id = data['teamInfo']['away']['id']
    home_team_id = data['teamInfo']['home']['id']

    away_roster = mlb.get('team_roster', params = {'teamId':away_team_id,'date':date.today()})['roster']
    # testcommit
    # away_roster = mlb.get('team_roster', params = {'teamId':away_team_id,'date':"2022-10-14"})['roster']
    away_roster = [el['person'] for el in away_roster]
    away_roster = [{k:v for k,v in el.items() if k!='link'} for el in away_roster]

    home_roster = mlb.get('team_roster', params = {'teamId':home_team_id,'date':date.today()})['roster']
    # testcommit
    # home_roster = mlb.get('team_roster', params = {'teamId':home_team_id,'date':"2022-10-14"})['roster']
    home_roster = [el['person'] for el in home_roster]
    home_roster = [{k:v for k,v in el.items() if k!='link'} for el in home_roster]

    teams = ['away', 'home']
    position = {}
    pitcher = {}
    for team in teams:
        key = team + 'Batters'
        player_info = data[key]
        position[team] = {}
        num = 1
        for el in player_info:
            if el['personId'] != 0:    
                if el['substitution'] == False:
                    position[team][el['personId']] = num
                    num = num + 1
        
    for team in teams:
        key = team + 'Pitchers'
        player_info = data[key]
        pitcher[team] = {}
        num = 1
        starter = True
        for el in player_info:
            if el['personId'] != 0: 
                if starter == True:
                    pitcher[team][el['personId']] = 'starter'
                    starter = False
    
    rosters = {'home': home_roster, 'away': away_roster, 'position': position, 'pitcher':pitcher }
    
    return rosters

def get_schedule_from_mlb():
    engine = database.connect_to_db()
    game_sched = mlb.schedule(start_date = date.today())
    #testcommit
    # game_sched = mlb.schedule(start_date = "2024-04-04")
    info_keys = ['game_id', 'game_datetime','away_name', 'home_name']
    game_sched = [{k:v for k,v in el.items() if k in info_keys} for el in game_sched]
    game_date = ''

    if len(game_sched) > 0:
        game_date = game_sched[0]['game_datetime'][0:10]
        date_obj = datetime.strptime(game_date, "%Y-%m-%d")
        game_date = date_obj.strftime("%Y/%m/%d") 
    
    tz = timezone('US/Eastern')
    for el in game_sched:
        engine.execute(f"INSERT INTO odds_table(game_id, game_date, away, home, start_time, away_open, away_close, home_open, home_close, state, auto_bet) VALUES('{el['game_id']}', '{game_date}', '{el['away_name']}', '{el['home_name']}', '{el['game_datetime']}', '0', '0', '0', '0', '0', '0');") 

        el['game_datetime'] = el['game_datetime'].split('T')[1][:-1] 
        el['game_id'] = str(el['game_id'])
        el['game_datetime'] = datetime.strptime(el['game_datetime'], '%H:%M:%S')
        el['game_datetime'] = el['game_datetime'].astimezone(tz) 
        el['game_datetime'] += timedelta(hours=1)
        el['game_datetime'] = datetime.strftime(el['game_datetime'], '%H:%M:%S')
        
    game_sched = pd.DataFrame(game_sched)
    return game_sched

def update_schedule(): 
    
    engine = database.connect_to_db()
    engine.execute("DELETE FROM schedule")
    engine.execute("DELETE FROM predict_table")
    
    new_schedule = get_schedule_from_mlb()
    new_schedule.to_sql("schedule", con = engine, index = False, if_exists = 'replace')
    
    return

def insert_newTeam(game_id, away_name, home_name, away_state, home_state):
    engine = database.connect_to_db()     

    data = mlb.boxscore_data(game_id)

    away_Id = data['teamInfo']['away']['id']
    home_Id = data['teamInfo']['home']['id']

    if(away_state == False):
        away_abbr = data['teamInfo']['away']['abbreviation']
        away_club = data['teamInfo']['away']['teamName']

        engine.execute(f"INSERT INTO team_table(team_id, team_name, team_abbr, club_name) VALUES('{away_Id}', '{away_name}', '{away_abbr}', '{away_club}') ON CONFLICT(team_id) DO UPDATE SET team_name = excluded.team_name, team_abbr = excluded.team_abbr, club_name = excluded.club_name;") 
        away_abbr.replace('\'', '')
        away_club.replace('\'', '')
        away_roster = mlb.get('team_roster', params = {'teamId':away_Id,'date':date.today()})['roster']
        away_roster = [el['person'] for el in away_roster]
        away_roster = [{k:v for k,v in el.items() if k!='link'} for el in away_roster]
        for el in away_roster:
            pname = el['fullName'].replace('\'', '')
            engine.execute(f"INSERT INTO player_table(p_id, p_name, t_id) VALUES('{el['id']}', '{pname}','{away_Id}') ON CONFLICT (p_id) DO UPDATE SET p_name = excluded.p_name, t_id = excluded.t_id;") 

        away_name = away_club

    if(home_state == False):
        home_abbr = data['teamInfo']['home']['abbreviation']
        home_club = data['teamInfo']['home']['teamName']

        home_abbr.replace('\'', '')
        home_club.replace('\'', '')
        engine.execute(f"INSERT INTO team_table(team_id, team_name, team_abbr, club_name) VALUES('{home_Id}', '{home_name}', '{home_abbr}', '{home_club}') ON CONFLICT(team_id) DO UPDATE SET team_name = excluded.team_name, team_abbr = excluded.team_abbr, club_name = excluded.club_name;") 
        home_roster = mlb.get('team_roster', params = {'teamId':home_Id,'date':date.today()})['roster']
        home_roster = [el['person'] for el in home_roster]
        home_roster = [{k:v for k,v in el.items() if k!='link'} for el in home_roster]  
        for el in home_roster:
            pname = el['fullName'].replace('\'', '')
            engine.execute(f"INSERT INTO player_table(p_id, p_name, t_id) VALUES('{el['id']}', '{pname}','{away_Id}') ON CONFLICT (p_id) DO UPDATE SET p_name = excluded.p_name, t_id = excluded.t_id;") 

        home_name = home_club
    return away_name, home_name     

