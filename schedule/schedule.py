import statsapi as mlb
import pandas as pd
from datetime import date, time, datetime, timedelta
from database import database
from pytz import timezone


def get_schedule(): 
    
    away_state = True
    home_state = True

    engine = database.connect_to_db()
    try: 
        schedule = list(pd.read_sql('SELECT schedule.*, predict_table.la_away_prob, predict_table.la_home_prob, predict_table.lb_away_prob, predict_table.lb_home_prob FROM schedule LEFT JOIN predict_table ON schedule.game_id = predict_table.game_id', con = engine).T.to_dict().values())
    except: 
        schedule = get_schedule_from_mlb()
        return "Today's schedule can't be found. Try force-updating or waiting a few minutes to refresh!"
    
    res = mlb.get('teams', params = {'sportId': 1})['teams']
    team_dict = [{k:v for k,v in el.items() if k in ['name', 'teamName']} for el in res]
    team_dict = {el['name']:el['teamName'] for el in team_dict}

    for game in schedule: 
        if game['away_name'] in team_dict.keys():
            away_state = True
        else:
            away_state = False
        
        if game['home_name'] in team_dict.keys():
            home_state = True
        else:
            home_state = False

        if away_state == False or home_state == False:
            return schedule
            game['away_name'], game['home_name'] = insert_newTeam(game['game_id'], game['away_name'], game['home_name'], away_state, home_state)
            if away_state:
                game['away_name'] = team_dict[game['away_name']]
            if home_state:
                game['home_name'] = team_dict[game['home_name']]
        else:
        game['away_name'] = team_dict[game['away_name']]
        game['home_name'] = team_dict[game['home_name']]

    return schedule

def get_rosters(game_id):
    data = mlb.boxscore_data(game_id)

    away_team_id = data['teamInfo']['away']['id']
    home_team_id = data['teamInfo']['home']['id']

    # away_roster = mlb.get('team_roster', params = {'teamId':away_team_id,'date':date.today()})['roster']
    # testcommit
    away_roster = mlb.get('team_roster', params = {'teamId':away_team_id,'date':"2022-10-14"})['roster']
    away_roster = [el['person'] for el in away_roster]
    away_roster = [{k:v for k,v in el.items() if k!='link'} for el in away_roster]

    # home_roster = mlb.get('team_roster', params = {'teamId':home_team_id,'date':date.today()})['roster']
    # testcommit
    home_roster = mlb.get('team_roster', params = {'teamId':home_team_id,'date':"2022-10-14"})['roster']
    home_roster = [el['person'] for el in home_roster]
    home_roster = [{k:v for k,v in el.items() if k!='link'} for el in home_roster]
    
    rosters = {'home': home_roster, 'away': away_roster}
    
    return rosters

def get_schedule_from_mlb():
    # game_sched = mlb.schedule(start_date = date.today())
    #testcommit
    game_sched = mlb.schedule(start_date = "2022-10-14")
    info_keys = ['game_id', 'game_datetime','away_name', 'home_name']
    game_sched = [{k:v for k,v in el.items() if k in info_keys} for el in game_sched]
    
    tz = timezone('US/Eastern')
    for el in game_sched: 
        el['game_datetime'] = el['game_datetime'].split('T')[1][:-1] 
        el['game_id'] = str(el['game_id'])
        el['game_datetime'] = datetime.strptime(el['game_datetime'], '%H:%M:%S')-timedelta(hours = 3)
        el['game_datetime'] = datetime.strftime(el['game_datetime'], '%H:%M:%S')
        
    game_sched = pd.DataFrame(game_sched)
    return game_sched

def update_schedule(): 
    
    engine = database.connect_to_db()
    engine.execute("DELETE FROM schedule")
    
    new_schedule = get_schedule_from_mlb()
    print(new_schedule)
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



