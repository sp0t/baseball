from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from sqlalchemy import create_engine
import pandas as pd
import statsapi as mlb
from datetime import date, time, datetime, timedelta
from pytz import timezone

# chrome_options = Options()
# chrome_options.add_argument('--headless')
# chrome_options.add_argument('--no-sandbox')
# chrome_options.add_argument('--disable-dev-shm-usage')
# driver = webdriver.Chrome('/home/.wdm/drivers/chromedriver',chrome_options=chrome_options)
# driver=webdriver.Chrome(service=Service(ChromeDriverManager().install()))

engine = create_engine('postgresql://postgres:lucamlb123@ec2-3-115-115-146.ap-northeast-1.compute.amazonaws.com:5432/betmlb', 
                                connect_args = {'connect_timeout': 10}, 
                                echo=False, pool_size=20, max_overflow=0)


def get_box_score(game_id): 
    
    data = mlb.boxscore_data(game_id)
    
    # Game Info 
    game_date = data['gameId'][:10]
    away_team = data['teamInfo']['away']['abbreviation']
    home_team = data['teamInfo']['home']['abbreviation']
    
    away_score = data['awayBattingTotals']['r']
    home_score = data['homeBattingTotals']['r']
    
    box_score = {
        'game_id': game_id,
        'game_date': game_date, 
        'away_team': away_team, 
        'home_team': home_team, 
        'away_score': away_score, 
        'home_score': home_score,
    }

    # Batting Data
    away_batter_data = get_batting_box_score(data, 'away')
    home_batter_data = get_batting_box_score(data, 'home')
    box_score.update(away_batter_data)
    box_score.update(home_batter_data)
    
    # Pitching Data
    away_pitcher_data = get_pitching_box_score(data, 'away')
    home_pitcher_data = get_pitching_box_score(data, 'home')
    
    if away_pitcher_data is None or home_pitcher_data is None: 
        return None
    box_score.update(away_pitcher_data)
    box_score.update(home_pitcher_data)
    
    box_score = {box_score['game_id']:box_score}
        
    
    return box_score

def get_batting_box_score(data, team): 

    key = team + 'Batters'
    data_info = data[key]
    num = 1
    team_batters = []
    for el in data_info:
        if el['battingOrder'] == str(num * 100):
            team_batters.append(el['personId'])
            num = num + 1

    if len(team_batters) != 9:
        return
    team_box_score = {}
    for team_batter in team_batters: 
        order = team_batters.index(team_batter)+1
        pbs = data[team]['players'][f'ID{team_batter}']['stats']['batting']
        pbs.update({'playerId': team_batter})

        # Calculate AVG, OBP, SLG, OPS
        atBats = pbs['atBats']
        atBatsWalks = pbs['atBats'] + pbs['baseOnBalls']
        avg = pbs['hits'] / atBats if atBats > 0 else 0
        obp = (pbs['hits'] + pbs['baseOnBalls']) / atBatsWalks if atBatsWalks > 0 else 0
        singles = pbs['hits'] - (pbs['homeRuns'] - pbs['triples'] - pbs['doubles'])
        slg = (4*pbs['homeRuns'] + 3*pbs['triples'] + 2*pbs['doubles'] + singles) / atBats if atBats > 0 else 0
        pbs.update({
            'avg': avg, 
            'obp': obp, 
            'slg': slg, 
            'ops': obp + slg
        })

        pbs = {f'{team}_b{order}_{k}':v for k,v in pbs.items() if k not in ['leftOnBase', 'stolenBases']}
        team_box_score.update(pbs)

    return team_box_score

def get_pitching_box_score(data, team): 
    
    pitchers = data[team]['pitchers']
    if len(pitchers) == 0: 
        return None
    team_starter = str(data[team]['pitchers'][0])
    team_box_score = {}
    
    
    team_pitchers = [str(el) for el in data[team]['pitchers']]
    if len(team_pitchers) == 0: 
        return None
    elif len(team_pitchers) == 1:
        team_bullpen_data = None
        
    team_starter = team_pitchers[0]
    team_relievers = team_pitchers[1:]

    # Starter Data 
    team_starter_data = data[team]['players']['ID' + team_starter]['stats']['pitching']
    team_starter_data.update({'playerId': team_starter})
    team_starter_data['inningsPitched'] = float(team_starter_data['inningsPitched'])
    ip = team_starter_data['inningsPitched']
    era = 9*team_starter_data['earnedRuns']/ip if ip > 0 else 0
    whip = (team_starter_data['baseOnBalls'] + team_starter_data['hits']) / ip if ip > 0 else 0
    team_starter_data.update({
        'era': era, 
        'whip': whip, 
    })

    team_starter_data = {f'{team}_starter_{k}':v for k,v in team_starter_data.items() if k not in ['leftOnBase', 'stolenBases', 'note', 'notes','numberOfPitches']}


    team_reliever_data_list = []
    for team_reliever in team_relievers: 
        team_reliever_data = data[team]['players']['ID' + team_reliever]['stats']['pitching']
        team_reliever_data.update({'playerId': team_reliever})
        team_reliever_data['inningsPitched'] = float(team_reliever_data['inningsPitched'])
        ip = team_reliever_data['inningsPitched']
        era = 9*team_reliever_data['earnedRuns']/ip if ip > 0 else 0
        whip = (team_reliever_data['baseOnBalls'] + team_reliever_data['hits']) / ip if ip > 0 else 0
        team_reliever_data.update({
            'era': era, 
            'whip': whip, 
        })

        team_reliever_data = {k:v for k,v in team_reliever_data.items() if k not in ['leftOnBase', 'stolenBases', 'note', 'notes','numberOfPitches']}
        team_reliever_data_list.append(team_reliever_data)
    team_bullpen_data = pd.DataFrame(team_reliever_data_list).mean().to_dict()
    team_bullpen_data = {f'{team}_bullpen_{k}':v for k,v in team_bullpen_data.items()}
    
    team_box_score.update(team_starter_data)
    team_box_score.update(team_bullpen_data)
    
    
    return team_box_score

game_sched = mlb.schedule(start_date = '2023-03-30')

info_keys = ['game_id', 'game_datetime','away_name', 'home_name']
game_sched = [{k:v for k,v in el.items() if k in info_keys} for el in game_sched]

tz = timezone('US/Eastern')

for el in game_sched: 
    el['game_datetime'] = el['game_datetime'].split('T')[1][:-1] 
    el['game_id'] = str(el['game_id'])
    el['game_datetime'] = datetime.strptime(el['game_datetime'], '%H:%M:%S')-timedelta(hours = 3)
    el['game_datetime'] = datetime.strftime(el['game_datetime'], '%H:%M:%S')

box_list = []

# 533792 718772 718763
# get_box_score('718772')

for el in game_sched: 
    if el['game_id'] != '718772':
        continue

    team1 = list(pd.read_sql(f"SELECT * FROM team_table WHERE team_name = '{el['away_name']}'", con = engine).T.to_dict().values())
    team2 = list(pd.read_sql(f"SELECT * FROM team_table WHERE team_name = '{el['home_name']}'", con = engine).T.to_dict().values())

    print('search gameid', el['game_id'])

    if team1 == [] or team2 == []:
        continue

    box = get_box_score(el['game_id'])
    if box is None: 
        continue
    box_list.append(box)
# Convert to df
df = pd.DataFrame()
for box in box_list: 
    df = pd.concat([df, pd.DataFrame(box).T])
df = df.drop([col for col in df.columns if 'note' in col], axis = 1)
meta_cols = ['game_id','game_date', 'away_team', 'home_team', 'away_score', 'home_score']
df1 = df[meta_cols]
df2 = df[[col for col in df.columns if col not in meta_cols]]
df = pd.concat([df1, df2], axis = 1)
df['winner'] = df.apply(lambda row: 1 if row['home_score'] > row['away_score'] else 0, axis = 1)
df = df.astype(str).reset_index(drop = True)
df.columns = df.columns.str.lower()
new_games = df
for index, row in new_games.iterrows():
    #game_table
    game_table_sql = 'INSERT INTO game_table( game_id, game_date, away_team, home_team, away_score, home_score, winner) VALUES (' + \
            '\'' + str(row[0]) + '\'' + ',' +  '\'' + row[1] + '\'' +  ',' + '\'' +  row[2] + '\'' +  ',' + \
            '\'' + str(row[3]) + '\'' +  ',' + '\'' +  str(row[4]) + '\'' +  ','  + '\'' + str(row[5])\
            + '\'' + ',' + '\'' +str(row[338]) + '\'' + ');'

    engine.execute(game_table_sql)
    
    #pitcher_table insert query
    for k in range(1, 5):
        if k % 4 == 0:
            key, team, role = 298, 'home', 'bullpen'
        elif k % 4 == 1:
            key, team, role = 152, 'away', 'starter'
        elif k % 4 == 2:
            key, team, role = 132, 'away', 'bullpen'
        elif k % 4 == 3:
            key, team, role = 318, 'home', 'starter'

        pitcher_table_sql = 'INSERT INTO pitcher_table( game_id, playerid, team, role, atbats, baseonballs, blownsaves, doubles, earnedruns, era,' \
                    'hits, holds, homeruns, inningspitched, losses, pitchesthrown, rbi, runs, strikeouts, strikes, triples, whip, wins) VALUES (' + \
                    '\'' + str(row[0]) + '\'' + ',' +  '\'' + str(row[key+12]) + '\'' +  ',' + '\'' +  team + '\'' +  ',' + '\'' + role + '\'' +  ',' + \
                    '\'' + str(row[key+0]) + '\'' +  ',' + '\'' + str(row[key+1]) + '\'' +  ',' + '\'' + str(row[key+2]) + '\'' +  ',' + \
                    '\'' + str(row[key+3]) + '\'' +  ',' + '\'' + str(row[key+4]) + '\'' +  ',' + '\'' + str(row[key+5]) + '\'' + ',' + \
                    '\'' + str(row[key+6]) + '\'' +  ',' + '\'' + str(row[key+7]) + '\'' +  ',' + '\'' + str(row[key+8]) + '\'' +  ',' + \
                    '\'' + str(row[key+9]) + '\'' +  ',' + '\'' + str(row[key+10]) + '\'' +  ',' + '\'' + str(row[key+11]) + '\'' +  ',' + \
                    '\'' + str(row[key+13]) + '\'' +  ',' + '\'' + str(row[key+14]) + '\'' +  ',' + '\'' + str(row[key+15]) + '\'' +  ',' + \
                    '\'' + str(row[key+16]) + '\'' +  ',' + '\'' + str(row[key+17]) + '\'' +  ',' + '\'' + str(row[key+18]) + '\'' +  ',' + \
                    '\'' + str(row[key+19]) + '\'' + ');'
        engine.execute(pitcher_table_sql)
    #batter_table insert query
    for j in range(1, 19):
        if(j < 10):
            batter_table_sql = 'INSERT INTO batter_table( game_id, playerid, team, position, atbats, avg, baseonballs, doubles, hits, homeruns, '\
                        'obp, ops, rbi, runs, slg, strikeouts, triples) VALUES (' + \
                        '\'' + str(row[0]) + '\'' + ',' +  '\'' + str(row[6 + (j - 1) * 14 + 8]) + '\'' +  ',' + \
                        '\'' + 'away' + '\'' + ',' + '\'' +  str(j) + '\'' +  ',' +\
                        '\'' + str(row[6 + (j - 1) * 14 + 0]) + '\'' +  ',' + '\'' + str(row[6 + (j - 1) * 14 + 1]) + '\'' +  ',' + \
                        '\'' + str(row[6 + (j - 1) * 14 + 2]) + '\'' +  ',' + '\'' + str(row[6 + (j - 1) * 14 + 3]) + '\'' +  ',' + \
                        '\'' + str(row[6 + (j - 1) * 14 + 4]) + '\'' +  ',' + '\'' + str(row[6 + (j - 1) * 14 + 5]) + '\'' +  ',' + \
                        '\'' + str(row[6 + (j - 1) * 14 + 6]) + '\'' +  ',' + '\'' + str(row[6 + (j - 1) * 14 + 7]) + '\'' +  ',' + \
                        '\'' + str(row[6 + (j - 1) * 14 + 9]) + '\'' +  ',' + '\'' + str(row[6 + (j - 1) * 14 + 10]) + '\'' +  ',' + '\'' + str(row[6 + (j - 1) * 14 + 11]) + '\'' +  ',' + \
                        '\'' + str(row[6 + (j - 1) * 14 + 12]) + '\'' +  ',' + '\'' + str(row[6 + (j - 1) * 14 + 13]) + '\'' + ');'
        else:
            batter_table_sql = 'INSERT INTO batter_table( game_id, playerid, team, position, atbats, avg, baseonballs, doubles, hits, homeruns, '\
                        'obp, ops, rbi, runs, slg, strikeouts, triples) VALUES (' + \
                        '\'' + str(row[0]) + '\'' + ',' +  '\'' + str(row[172 + (j - 10) * 14 + 8]) + '\'' +  ',' + \
                        '\'' + 'home' + '\'' + ',' + '\'' +  str(j - 9) + '\'' +  ',' +\
                        '\'' + str(row[172 + (j - 10) * 14 + 0]) + '\'' +  ',' + '\'' + str(row[172 + (j - 10) * 14 + 1]) + '\'' +  ',' + \
                        '\'' + str(row[172 + (j - 10) * 14 + 2]) + '\'' +  ',' + '\'' + str(row[172 + (j - 10) * 14 + 3]) + '\'' +  ',' + \
                        '\'' + str(row[172 + (j - 10) * 14 + 4]) + '\'' +  ',' + '\'' + str(row[172 + (j - 10) * 14 + 5]) + '\'' +  ',' + \
                        '\'' + str(row[172 + (j - 10) * 14 + 6]) + '\'' +  ',' + '\'' + str(row[172 + (j - 10) * 14 + 7]) + '\'' +  ',' + \
                        '\'' + str(row[172 + (j - 10) * 14 + 9]) + '\'' +  ',' + '\'' + str(row[172 + (j - 10) * 14 + 10]) + '\'' +  ',' + '\'' + str(row[6 + (j - 10) * 14 + 11]) + '\'' +  ',' + \
                        '\'' + str(row[172 + (j - 12) * 14 + 11]) + '\'' +  ',' + '\'' + str(row[172 + (j - 10) * 14 + 13]) + '\'' + ');'
            
        print(batter_table_sql)
        engine.execute(batter_table_sql)

    
print("success!")