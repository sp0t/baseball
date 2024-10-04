from API import nhlAPI
from scrapper import NHLStats
import psycopg2
from io import StringIO
import statsapi as mlb
from datetime import date, datetime, timedelta
import time
import pandas as pd
from pytz import timezone
import psycopg2.extras as extras
from sqlalchemy import create_engine
import uuid
import requests
from functions import modelInput 

def connect_to_db(): 
    
    try: 
        engine = create_engine('postgresql://postgres:lucamlb123@localhost:5432/betnhl_new', connect_args = {'connect_timeout': 10}, echo=False, pool_size=20, max_overflow=0)
        print('Connection Initiated')
    except:
        raise ValueError("Can't connect to Heroku PostgreSQL! You must be so embarrassed")
    return engine

def get_game_id_list(start_date, end_date, show_progress = False): 

    delta = end_date - start_date
    game_id_list = []
    error_days=[]
    for i in range(delta.days+1): 
        day = start_date + timedelta(days=i)
        day = datetime.strftime(day, '%Y-%m-%d')
        print(day)
        try: 
            schedule = nhlAPI.get_Daily_Scores_By_Date(date = day)
        except: 
            error_days.append(day)
            continue 
        for el in schedule['games']:
            day_games = {}
            day_games['id'] = el['id']
            day_games['season'] = el['season']
            day_games['awayTeam'] = el['awayTeam']['abbrev']
            day_games['homeTeam'] = el['homeTeam']['abbrev']
            game_id_list.append(day_games)

        if show_progress and i%25==0:
            print(day, i)

    seen_gameids = set()
    unique_games = []
    for game in game_id_list:
        if game["id"] not in seen_gameids:
            unique_games.append(game)
            seen_gameids.add(game["id"])
    
    return unique_games, error_days

def update_database(): 
    engine = connect_to_db()
    res = engine.execute("SELECT game_id, game_date FROM game_table;").fetchall()

    if len(res) == 0:
        current_game_list = []
        last_record = date.today() - timedelta(days = 2)
    else:
        current_game_list = [el[0] for el in res]
        last_record = max([el[1] for el in res])
        last_record = datetime.strptime(last_record, '%Y-%m-%d').date()
        print(last_record)
        record_day = date.today() - timedelta(days = 1)
        print(record_day)
        if last_record > record_day:
            last_record = record_day
            print(last_record)

    print(f'Old Last Record is {last_record}')
    game_list, errored_days = get_game_id_list(start_date = last_record + timedelta(days = 1), 
                                                  end_date = date.today() - timedelta(days = 1), 
                                                  show_progress = False )
    print(game_list, errored_days)
    game_list = [el for el in game_list if el['id'] not in current_game_list]
    print(f'Games to add = {len(game_list)}')
    print(print)
    if len(game_list) > 0: 
        # Get Box Scores! 
        box_list = []
        tic = time.time()
        num_games = len(game_list)
        errored_games = []
        for game in game_list: 
            game_index = game_list.index(game)
            apiBoxScore = nhlAPI.get_Boxscore(game['id'])
            scrapedNstData = NHLStats.scrape(game['id'], game['season'], game['awayTeam'], game['homeTeam'])
            
            if apiBoxScore is None or scrapedNstData is None: 
                errored_games.append(game['id'])
                continue

            box = {}

            box['game_id'] = game['id']
            box['season'] = apiBoxScore['season']
            box['game_date'] = apiBoxScore['gameDate']
            box['away_team'] = apiBoxScore['awayTeam']['abbrev']
            box['home_team'] = apiBoxScore['homeTeam']['abbrev']
            start_time = apiBoxScore['startTimeUTC']
            start_time = datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%SZ')
            offset_sign = 1 if apiBoxScore['easternUTCOffset'][0] == '+' else -1 
            offset_hours, offset_minutes = map(int,  apiBoxScore['easternUTCOffset'][1:].split(':'))
            time_offset = timedelta(hours=offset_hours * offset_sign, minutes=offset_minutes * offset_sign)
            start_time = start_time + time_offset
            start_time = start_time.strftime('%Y/%m/%d %H:%M:%S')
            box['start_time'] = start_time

            if apiBoxScore['gameState'] == 'FUT':
                engine.execute("INSERT INTO game_table(game_id, game_date, away_team, home_team, season_id, state, start_time, import_state) VALUES(%s, %s, %s, %s, %s, %s, %s, %s)", (box['game_id'], box['game_date'], box['away_team'],  box['home_team'], box['season'], apiBoxScore['gameState'], box['start_time'], 'FAILED'))
                continue


            box['away_score'] = apiBoxScore['awayTeam']['score']
            box['home_score'] = apiBoxScore['homeTeam']['score']
            if box['away_score'] < box['home_score']:
                winner = 0
            else:
                winner = 1

            box['winner'] = winner


            box['player'] = {}
            box['player']['goalies'] = []
            box['player']['skaters'] = []

            all_box_scores = [
                player_stats
                for _team_side, team_side_squads in apiBoxScore['playerByGameStats'].items()
                for _squad_name, player_stats_list in team_side_squads.items()
                for player_stats in player_stats_list
            ]

            def check_if_duplicates_exist(arr):
                return len(set(arr)) != len(arr)

            box_score_player_names = [player_stats['name']['default'] for player_stats in all_box_scores]
            any_players_share_names = check_if_duplicates_exist(box_score_player_names)

            if any_players_share_names:
                engine.execute("INSERT INTO game_table(game_id, game_date, away_team, home_team, away_score, home_score, winner, season_id, state, start_time, import_state) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (box['game_id'], box['game_date'], box['away_team'],  box['home_team'], box['away_score'], box['home_score'], box['winner'], box['season'], apiBoxScore['gameState'], box['start_time'], 'MULTIPLE_PLAYERS_WITH_SAME_NAME'))
                continue
            else:
                engine.execute("INSERT INTO game_table(game_id, game_date, away_team, home_team, away_score, home_score, winner, season_id, state, start_time, import_state) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (box['game_id'], box['game_date'], box['away_team'],  box['home_team'], box['away_score'], box['home_score'], box['winner'], box['season'], apiBoxScore['gameState'], box['start_time'], 'COMPLETED'))

            all_scraped_player_stats = [
                {**player_stat, 'teamSide': team_side, 'role': _squad_name }
                for team_side, team_side_squads in scrapedNstData.items()
                for _squad_name, player_stats_list in team_side_squads.items()
                for player_stat in player_stats_list
            ]

            def find_box_score(scraped_player_stats):
                name_parts = scraped_player_stats['name'].split(' ')
                first_name = name_parts.pop(0).strip()
                last_name = ' '.join(name_parts).strip()
                alternative_last_name = name_parts[-1] if name_parts else ''

                def to_comparable_name(name):
                    return name.lower() \
                        .replace('å', 'a') \
                        .replace('ä', 'a') \
                        .replace('ö', 'o') \
                        .replace('ü', 'u') \
                        .replace('é', 'e') \
                        .replace('è', 'e') \
                        .replace('janmark-nylen', 'janmark') \
                        .replace('iakovlev', 'yakovlev') \
                        .replace('vorobyov', 'vorobyev') \
                        .replace('\x1A', 'c')

                def build_combined_name(name1, name2):
                    return to_comparable_name(f"{name1[0]}. {name2}")

                comparable_name = build_combined_name(first_name, last_name)
                alternative_comparable_name = build_combined_name(first_name, alternative_last_name)

                if comparable_name == 'r. nardella':
                    alternative_comparable_name = 'b. nardella'
                elif comparable_name == 'y. zamula':
                    alternative_comparable_name = 'e. zamula'

                possible_comparable_names = [comparable_name, alternative_comparable_name]

                box_score = next(
                    (box_score for box_score in all_box_scores 
                    if to_comparable_name(box_score['name']['default']) in possible_comparable_names), 
                    None
                )

                if not box_score:
                    print(f"Couldn't find NHL API Box Score for player. Looking for: {possible_comparable_names}")
                    print(f"Options: {[to_comparable_name(box_score_player['name']['default']) for box_score_player in all_box_scores]}")

                return box_score


            for scraped_player_stats in all_scraped_player_stats:
                box_score = find_box_score(scraped_player_stats)

                if box_score is None:
                    continue

                if scraped_player_stats['role'] == 'skaters':
                    skater = {}
                    skater['player_id'] = box_score['playerId']
                    skater['position'] = box_score['position']
                    skater['goals'] = box_score['goals']
                    skater['assists'] = box_score['assists']
                    skater['points'] = box_score['points']
                    skater['plus_minus'] = box_score['plusMinus']
                    skater['penalty_minutes'] = box_score['pim']
                    skater['time_on_ice'] = box_score['toi']
                    skater['name'] = scraped_player_stats['name']
                    skater['role'] = scraped_player_stats['role']
                    skater['team'] = 'AWAY' if scraped_player_stats['teamSide'] == 'awayTeam' else 'HOME'
                    skater['corsi_for'] = scraped_player_stats['corsi_for']
                    skater['corsi_against'] = scraped_player_stats['corsi_against']
                    skater['fenwick_for_percent'] = scraped_player_stats['fenwick_for_percent']
                    skater['fenwick_for_percent_relative'] = scraped_player_stats['fenwick_for_percent_relative']
                    box['player']['skaters'].append(skater)
                    engine.execute("INSERT INTO skater_stats(game_id, player_id, team_side,  plus_mius, penalty_minutes, assists, time_on_ice, fenwick_for_percent_relative, corsi_for, position, goals, points, corsi_against, fenwick_for_percent) VALUES(%s, %s, %s,  %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (box['game_id'], skater['player_id'], skater['team'], skater['plus_minus'], skater['penalty_minutes'], skater['assists'], skater['time_on_ice'], skater['fenwick_for_percent_relative'], skater['corsi_for'], skater['position'], skater['goals'], skater['points'], skater['corsi_against'], skater['fenwick_for_percent']))

                elif scraped_player_stats['role'] == 'goalies':
                    goalies = {}
                    goalies['player_id'] = box_score['playerId']
                    goalies['position'] = box_score['position']
                    goalies['time_on_ice'] = box_score['toi']
                    goalies['penalty_minutes'] = box_score.get('pim', 0)
                    goalies['name'] = scraped_player_stats['name']
                    goalies['role'] = scraped_player_stats['role']
                    goalies['team'] = 'AWAY' if scraped_player_stats['teamSide'] == 'awayTeam' else 'HOME'
                    goalies['goals_against'] = scraped_player_stats['goals_against']
                    goalies['save_percentage'] = scraped_player_stats['save_percentage']
                    box['player']['goalies'].append(goalies)
                    engine.execute("INSERT INTO goaltender_stats(game_id, player_id, team_side,  penalty_minutes, time_on_ice, position, save_percentage, goals_against) VALUES(%s, %s, %s,  %s, %s, %s, %s, %s)", (box['game_id'], goalies['player_id'], goalies['team'], goalies['penalty_minutes'], goalies['time_on_ice'], goalies['position'], goalies['save_percentage'], goalies['goals_against']))
            box_list.append(box)

            modelInput.generate_model_input(box['game_id'], engine)
    tz = timezone('US/Eastern')
    last_update_date = date.today()
    last_update_time = datetime.now() + timedelta(hours = 3)
    last_update_time = datetime.strftime(last_update_time, '%H:%M:%S')

    new_last_record = pd.read_sql("SELECT * FROM updates ORDER BY update_date DESC, update_time DESC", con = engine).to_dict('records')
    if len(new_last_record) == 0:
        last_record = last_update_date
    else:
        last_record = new_last_record[0]['update_date']

        
    new_updates = pd.DataFrame({'update_id': str(uuid.uuid4()), 
                                'update_date': last_update_date, 
                     'update_time': last_update_time, 
                     'last_record': last_record}, index = [0])

    new_updates.to_sql(con = engine, 
                 name = 'updates', 
                 if_exists = 'append', 
                 index = False)
    print('DB Updated')
update_database()