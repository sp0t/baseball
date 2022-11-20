import pandas as pd
from datetime import date, datetime, timedelta
import statsapi as mlb
import time

def get_game_id_list(start_date, end_date, show_progress = False): 

    delta = end_date - start_date
    game_id_list = []
    error_days=[]
    for i in range(delta.days+1): 
        day = start_date + timedelta(days=i)
        day = datetime.strftime(day, '%Y-%m-%d')
        try: 
            schedule = mlb.schedule(start_date=day)
        except: 
            error_days.append(day)
            continue 
        day_games = [el['game_id'] for el in schedule]
        game_id_list.append(day_games)

        if show_progress and i%25==0:
            print(day, i)
    game_id_list = [item for sublist in game_id_list for item in sublist]
    game_id_list = [str(item) for item in game_id_list]
    
    seen = set()
    seen_add = seen.add
    game_id_list = [x for x in game_id_list if not (x in seen or seen_add(x))]
    
    return game_id_list, error_days

def get_batting_box_score(data, team): 

    team_batters = [str(el) for el in data[team]['batters'][:9]]
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