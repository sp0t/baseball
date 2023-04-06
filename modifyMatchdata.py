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

# engine = create_engine('postgresql://postgres:lucamlb123@ec2-3-115-115-146.ap-northeast-1.compute.amazonaws.com:5432/betmlb', 
#                                 connect_args = {'connect_timeout': 10}, 
#                                 echo=False, pool_size=20, max_overflow=0)

# engine = create_engine('postgresql://postgres:123@localhost:5432/testdb', 
#                                connect_args = {'connect_timeout': 10}, 
#                                echo=False, pool_size=20, max_overflow=0)


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
    batter_data = {}
    away_batter_data = get_batting_box_score(data, 'away')
    batter_data['away'] = away_batter_data
    home_batter_data = get_batting_box_score(data, 'home')
    batter_data['home'] = home_batter_data

    if away_batter_data is None or home_batter_data is None: 
        return None
    
    box_score['batter'] = batter_data
    
    # Pitching Data
    pitcher_data = {}
    away_pitcher_data = get_pitching_box_score(data, 'away')
    pitcher_data['away'] = away_pitcher_data
    home_pitcher_data = get_pitching_box_score(data, 'home')
    pitcher_data['home'] = home_pitcher_data
    
    if away_pitcher_data is None or home_pitcher_data is None: 
        return None
    
    box_score['pitcher'] = pitcher_data
        
    return box_score

def get_batting_box_score(data, team): 

    key = team + 'Batters'
    data_info = data[key]
    team_batters = []
    subinfo = {}
    num = 1
    for el in data_info:
        if el['personId'] != 0:    
            if el['substitution']:
                if el['battingOrder'] == str((num - 1) * 100 + 1):
                    subinfo[str(el['personId'])] = {}
                    team_batters.append(el['personId'])
                    subinfo[str(el['personId'])]['position'] = num - 1
                    subinfo[str(el['personId'])]['substitution'] = 1
            else:
                subinfo[str(el['personId'])] = {}
                team_batters.append(el['personId'])
                subinfo[str(el['personId'])]['position'] = num
                subinfo[str(el['personId'])]['substitution'] = 0
                num = num + 1

    team_box_score = []
 
    for team_batter in team_batters: 
        order = team_batters.index(team_batter)+1
        pbs = data[team]['players'][f'ID{team_batter}']['stats']['batting']
        pbs.update({'playerId': team_batter})
        pbs.update({'position': subinfo[str(team_batter)]['position']})
        pbs.update({'substitution': subinfo[str(team_batter)]['substitution']})

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
        team_box_score.append(pbs)
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

    team_starter_data = {k:v for k,v in team_starter_data.items() if k not in ['leftOnBase', 'stolenBases', 'note', 'notes','numberOfPitches']}

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
    
    team_box_score['starter'] = team_starter_data
    team_box_score['bullpen'] = team_bullpen_data
    
    return team_box_score

old_date = ''
box = get_box_score('718699')
print(box)
# game_dates = engine.execute("SELECT * FROM game_table ORDER BY game_date")
# for dates in game_dates:
#     date_obj = datetime.strptime(dates[1], '%Y/%m/%d')
#     game_date = date_obj.strftime('%Y-%m-%d')

#     if game_date < '2021-03-04':
#         continue

#     if game_date == old_date:
#         continue
#     old_date = game_date
#     print(game_date)

#     game_sched = mlb.schedule(start_date = game_date)

#     info_keys = ['game_id', 'game_datetime','away_name', 'home_name']
#     game_sched = [{k:v for k,v in el.items() if k in info_keys} for el in game_sched]

#     tz = timezone('US/Eastern')

#     for el in game_sched: 
#         el['game_datetime'] = el['game_datetime'].split('T')[1][:-1] 
#         el['game_id'] = str(el['game_id'])
#         el['game_datetime'] = datetime.strptime(el['game_datetime'], '%H:%M:%S')-timedelta(hours = 3)
#         el['game_datetime'] = datetime.strftime(el['game_datetime'], '%H:%M:%S')

#     box_list = []

#     for el in game_sched: 
#         team1 = list(pd.read_sql(f"SELECT * FROM team_table WHERE team_name = '{el['away_name']}'", con = engine).T.to_dict().values())
#         team2 = list(pd.read_sql(f"SELECT * FROM team_table WHERE team_name = '{el['home_name']}'", con = engine).T.to_dict().values())
#         if team1 == [] or team2 == []:
#             continue

#         box = get_box_score(el['game_id'])
#         if box is None: 
#             continue
#         # if el['game_id'] == '718733':
#         box_list.append(box)
#     # Convert to df

#     if box_list == []:
#         continue
#     df = pd.DataFrame()
#     for box in box_list: 
#         df = pd.concat([df, pd.DataFrame(box).T])
#     df = df.drop([col for col in df.columns if 'note' in col], axis = 1)

#     if df is None:
#         continue

#     for el in box_list:
#         if el['away_score'] < el['home_score']:
#             winner = 1
#         else:   
#             winner = 0
#         # game_table
#         # game_table_sql = 'INSERT INTO game_table( game_id, game_date, away_team, home_team, away_score, home_score, winner) VALUES (' + \
#         #         '\'' + el['game_id'] + '\'' + ',' +  '\'' + el['game_date'] + '\'' +  ',' + '\'' +  el['away_team'] + '\'' +  ',' + \
#         #         '\'' + el['home_team'] + '\'' +  ',' + '\'' +  el['away_score'] + '\'' +  ','  + '\'' + el['home_score']\
#                 # + '\'' + ',' + '\'' + str(winner) + '\'' + ');'
#         # print(game_table_sql)
#     #     engine.execute(game_table_sql)
        
#         # pitcher_table insert query
#         teams = ['away', 'home']
#         roles = ['starter', 'bullpen']

#         # for team in teams:
#         #     for role in roles:
#         #         pitcher_table_sql = 'INSERT INTO pitcher_table( game_id, playerid, team, role, atbats, baseonballs, blownsaves, doubles, earnedruns, era,' \
#         #                     'hits, holds, homeruns, inningspitched, losses, pitchesthrown, rbi, runs, strikeouts, strikes, triples, whip, wins) VALUES (' + \
#         #                     '\'' + el['game_id'] + '\'' + ',' +  '\'' + str(el['pitcher'][team][role]['playerId']) + '\'' +  ',' + '\'' + team + '\'' + ',' + '\'' + role + '\'' + ',' + \
#         #                     '\'' + str(el['pitcher'][team][role]['atBats']) + '\'' +  ',' + '\'' + str(el['pitcher'][team][role]['baseOnBalls']) + '\'' +  ',' + '\'' + str(el['pitcher'][team][role]['blownSaves']) + '\'' +  ',' + \
#         #                     '\'' + str(el['pitcher'][team][role]['doubles']) + '\'' +  ',' + '\'' + str(el['pitcher'][team][role]['earnedRuns']) + '\'' +  ',' + '\'' + str(el['pitcher'][team][role]['era']) + '\'' + ',' + \
#         #                     '\'' + str(el['pitcher'][team][role]['hits']) + '\'' +  ',' + '\'' + str(el['pitcher'][team][role]['holds']) + '\'' +  ',' + '\'' + str(el['pitcher'][team][role]['homeRuns']) + '\'' +  ',' + \
#         #                     '\'' + str(el['pitcher'][team][role]['inningsPitched']) + '\'' +  ',' + '\'' + str(el['pitcher'][team][role]['losses']) + '\'' +  ',' + '\'' + str(el['pitcher'][team][role]['pitchesThrown']) + '\'' +  ',' + \
#         #                     '\'' + str(el['pitcher'][team][role]['rbi']) + '\'' +  ',' + '\'' + str(el['pitcher'][team][role]['runs']) + '\'' +  ',' + '\'' + str(el['pitcher'][team][role]['strikeOuts']) + '\'' +  ',' + \
#         #                     '\'' + str(el['pitcher'][team][role]['strikes']) + '\'' +  ',' + '\'' + str(el['pitcher'][team][role]['triples']) + '\'' +  ',' + '\'' + str(el['pitcher'][team][role]['whip']) + '\'' +  ',' + \
#         #                     '\'' + str(el['pitcher'][team][role]['wins']) + '\'' + ');'
#                 # engine.execute(pitcher_table_sql)

#         # batter_table insert query
#         for team in teams:
#             for batter in el['batter'][team]:
#                 batter_table_sql = 'INSERT INTO batter_table( game_id, playerid, team, position, atbats, avg, baseonballs, doubles, hits, homeruns, '\
#                             'obp, ops, rbi, runs, slg, strikeouts, triples, substitution) VALUES (' + \
#                             '\'' + el['game_id'] + '\'' + ',' +  '\'' + str(batter['playerId']) + '\'' +  ',' + \
#                             '\'' + team + '\'' + ',' + '\'' +  str(batter['position']) + '\'' +  ',' +\
#                             '\'' + str(batter['atBats']) + '\'' +  ',' + '\'' + str(batter['avg']) + '\'' +  ',' + \
#                             '\'' + str(batter['baseOnBalls']) + '\'' +  ',' + '\'' + str(batter['doubles']) + '\'' +  ',' + \
#                             '\'' + str(batter['hits']) + '\'' +  ',' + '\'' + str(batter['homeRuns']) + '\'' +  ',' + \
#                             '\'' + str(batter['obp']) + '\'' +  ',' + '\'' + str(batter['ops']) + '\'' +  ',' + \
#                             '\'' + str(batter['rbi']) + '\'' +  ',' + '\'' + str(batter['runs']) + '\'' +  ',' + '\'' + str(batter['slg']) + '\'' +  ',' + \
#                             '\'' + str(batter['strikeOuts']) + '\'' +  ',' + '\'' + str(batter['triples']) + '\'' + ',' + '\'' + str(batter['substitution']) + '\'' + ');'
#                 # print(batter_table_sql)
#                 engine.execute(batter_table_sql)
   
print("success!")