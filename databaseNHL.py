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

def connect_to_db(): 
    
    try: 
        engine = create_engine('postgresql://postgres:lucamlb123@localhost:5432/betnhl', connect_args = {'connect_timeout': 10}, echo=False, pool_size=20, max_overflow=0)
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
        record_day = date.today() - timedelta(days = 2)
        if last_record > record_day:
            last_record = record_day

    print(f'Old Last Record is {last_record}')
    game_list, errored_days = get_game_id_list(start_date = last_record, 
                                                  end_date = date.today() - timedelta(days = 1), 
                                                  show_progress = False )
    print(game_list, errored_days)
    game_list = [el for el in game_list if el['id'] not in current_game_list]
    print(f'Games to add = {len(game_list)}')
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
            box['away_score'] = apiBoxScore['awayTeam']['score']
            box['home_score'] = apiBoxScore['homeTeam']['score']
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
                return

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
                    skater['team'] = scraped_player_stats['teamSide']
                    skater['corsi_for'] = scraped_player_stats['corsi_for']
                    skater['corsi_against'] = scraped_player_stats['corsi_against']
                    skater['fenwick_for_percent'] = scraped_player_stats['fenwick_for_percent']
                    skater['fenwick_for_percent_relative'] = scraped_player_stats['fenwick_for_percent_relative']
                    box['player']['skaters'].append(skater)
                elif scraped_player_stats['role'] == 'goalies':
                    goalies = {}
                    goalies['player_id'] = box_score['playerId']
                    goalies['position'] = box_score['position']
                    goalies['time_on_ice'] = box_score['toi']
                    goalies['name'] = scraped_player_stats['name']
                    goalies['role'] = scraped_player_stats['role']
                    goalies['team'] = scraped_player_stats['teamSide']
                    goalies['goals_against'] = scraped_player_stats['goals_against']
                    goalies['save_percentage'] = scraped_player_stats['save_percentage']
                    box['player']['goalies'].append(goalies)

            print(box)

            break
            # box_list.append(box)

            # if game_index % 10 == 0: 
            #     print(f'Game {game_index} of {num_games} -- {time.time() - tic:.2f} sec')

update_database()