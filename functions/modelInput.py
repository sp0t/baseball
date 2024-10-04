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
import copy
from collections import defaultdict
import re
import numpy as np

def combine_weighted_stats(*stats):
    accumulator = defaultdict(int)  

    for stat_set in stats:
        for stat_name, stat_value in stat_set.items():
            if isinstance(stat_value, (int, float)):
                accumulator[stat_name] += stat_value
            else:
                accumulator[stat_name] = stat_value

    return dict(accumulator)  

def get_season_finish_year(season_nhl_id):
    return int(season_nhl_id) % 10000


def camel_to_snake_case(string):
    return re.sub(r'([A-Z])', r'_\1', string).lower()

def rename_object_key(obj, old_key, new_key):
    obj[new_key] = obj.pop(old_key)

def has_game_relationship(player_game):
    if player_game['gameid'] == 0 or player_game['season_id'] is None:
        return False
    return True


def has_time_on_ice(player_game):
    return player_game.get('stats', {}).get('time_on_ice') is not None

def is_past_game_item(player_game, main_game_nhl_id):
    return int(player_game.get('gameid', 0)) < int(main_game_nhl_id)

def sort_by_nhl_id(game_item_a, game_item_b):
    return int(game_item_a['gameid']) - int(game_item_b['gameid'])

def convert_time_on_ice_to_integer(game_item):
    clone = game_item
    clone['stats']['time_on_ice'] = time_on_ice_string_to_decimal(clone['stats']['time_on_ice'])
    return clone

def time_on_ice_string_to_decimal(time_on_ice_str):
    minutes, seconds = map(int, time_on_ice_str.split(':'))
    return (minutes * 60 + seconds) / 3600

def get_skater_historical_stats(player_id, engine):
    skater_stats = pd.read_sql(f"SELECT skater_stats.*, game_table.season_id FROM skater_stats LEFT JOIN game_table ON skater_stats.game_id = game_table.game_id WHERE skater_stats.player_id = '{player_id}' ORDER BY game_table.game_id DESC;", con = engine).to_dict('records')
    sakter_items = [{'gameid':skater['game_id'], 'season_id':skater['season_id'], 'stats':{'position':skater['position'], 'goals':skater['goals'], 'assists':skater['assists'], 'points':skater['points'], 'plus_minus':skater['plus_mius'], 'penalty_minutes':skater['penalty_minutes'], 'time_on_ice':skater['time_on_ice'], 'corsi_for':skater['corsi_for'], 'corsi_against':skater['corsi_against'], 'fenwick_for_percent':skater['fenwick_for_percent'], 'fenwick_for_percent_relative':skater['fenwick_for_percent_relative']}} for skater in skater_stats]

    return sakter_items

def get_goaltender_historical_stats(player_id, engine):
    goaltender_stats = pd.read_sql(f"SELECT goaltender_stats.*, game_table.season_id FROM goaltender_stats LEFT JOIN game_table ON goaltender_stats.game_id = game_table.game_id WHERE goaltender_stats.player_id = '{player_id}' ORDER BY game_table.game_id DESC;", con = engine).to_dict('records')
    goaltender_items = [{'gameid':goaltender['game_id'], 'season_id':goaltender['season_id'], 'stats':{'position':goaltender['position'], 'penalty_minutes':goaltender['penalty_minutes'], 'time_on_ice':goaltender['time_on_ice'], 'save_percentage':goaltender['save_percentage'], 'goals_against':goaltender['goals_against']}} for goaltender in goaltender_stats]    

    return goaltender_items

def get_weighted_averages(game_items, main_game_season_nhl_id):
    main_game_season_year = get_season_finish_year(main_game_season_nhl_id)

    stats_per_age = defaultdict(list)
    game_items.reverse()

    for game_item in game_items:
        if game_item['gameid'] == 0 or game_item['season_id'] is None:
            print(f"gameItem doesn't have a game or season", game_item)
            continue

        game_season_nhl_id = game_item['season_id']
        stats = game_item['stats']
        amount_seasons_ago = main_game_season_year - get_season_finish_year(game_season_nhl_id)

        stats_per_age[amount_seasons_ago].append(stats)

    def average(array):
        numeric_array = [float(item) for item in array]
        return np.mean(numeric_array)

    def get_averaged_stats(stats_array, weight=1):
        stat_names = [key for key in stats_array[0].keys() if key != 'position']
  
        averaged_stats = {}
        for stat_name in stat_names:
            averaged_stats[stat_name] = average([float(stats[stat_name] if stats[stat_name] is not None else 0) for stats in stats_array]) * weight
            
        return averaged_stats

    played_game_ages = list(stats_per_age.keys())

    averaged_stats = {}

    if len(played_game_ages) == 0:
        averaged_stats = {}
    elif len(played_game_ages) == 1:
        averaged_stats = get_averaged_stats(stats_per_age[played_game_ages[0]])
    elif len(played_game_ages) == 2:
        first_age, second_age = played_game_ages

        age1_average = get_averaged_stats(stats_per_age[first_age], 0.7)
        age2_average = get_averaged_stats(stats_per_age[second_age], 0.3)

        averaged_stats = combine_weighted_stats(age1_average, age2_average)
    else:
        first_age, second_age, *other_ages = played_game_ages

        age1_average = get_averaged_stats(stats_per_age[first_age], 0.5)
        age2_average = get_averaged_stats(stats_per_age[second_age], 0.3)

        mapped_rest = [stats for age in other_ages for stats in stats_per_age[age]]
        rest_ages_average = get_averaged_stats(mapped_rest, 0.2)

        averaged_stats = combine_weighted_stats(age1_average, age2_average, rest_ages_average)

    for stat_name in list(averaged_stats.keys()):
        new_key = f"weighted_average_{camel_to_snake_case(stat_name)}"
        rename_object_key(averaged_stats, stat_name, new_key)

    return averaged_stats

def get_recent_form(past_sorted_game_items):
    cloned_games = copy.deepcopy(past_sorted_game_items[-10:])
    recent_stats = [game_item['stats'] for game_item in cloned_games]
    recent_stats.reverse()

    def apply_recent_form_weights(stats_set, index):
        weights = {
            0: 0.16,
            1: 0.15,
            2: 0.14,
            3: 0.13,
            4: 0.11,
            5: 0.09,
            6: 0.07,
            7: 0.06,
            8: 0.05,
            9: 0.04,
        }
        weight = weights[index]
        stats_set.pop('position', None)

        for stat_name, stat_value in stats_set.items():
            if isinstance(float(stat_value if stat_value is not None else 0), (int, float)):
                stats_set[stat_name] = float(stats_set[stat_name] if stats_set[stat_name] is not None else 0) * weight
        return stats_set



    weighted_stats = [apply_recent_form_weights(stats, index) for index, stats in enumerate(recent_stats)]

    averaged_stats = combine_weighted_stats(*weighted_stats)

    for stat_name in list(averaged_stats.keys()):
        rename_object_key(averaged_stats, stat_name, f"recent_form_{camel_to_snake_case(stat_name)}")

    return {
        'meta': {
            'game_ids': [game['gameid'] for game in cloned_games],
        },
        'stats': averaged_stats
    }

def get_current_game_stats(stats):
    cloned_stats = copy.deepcopy(stats)

    for stat_name in list(cloned_stats.keys()):
        rename_object_key(cloned_stats, stat_name, f"current_game_{camel_to_snake_case(stat_name)}")

    return cloned_stats

def generate_model_input(gameId, engine):
    skater_stats = pd.read_sql(f"SELECT * FROM skater_stats WHERE game_id = '{gameId}';", con = engine).to_dict('records')
    goaltender_stats = pd.read_sql(f"SELECT * FROM goaltender_stats WHERE game_id = '{gameId}';", con = engine).to_dict('records')
    game_center_data = nhlAPI.get_Landing(gameId)

    matchup = game_center_data.get('matchup', {})
    away_team_scratches = matchup.get('gameInfo', {}).get('awayTeam', {}).get('scratches', [])
    home_team_scratches = matchup.get('gameInfo', {}).get('homeTeam', {}).get('scratches', [])
    scratched_player_nhl_ids = [player.get('id') for player in (away_team_scratches + home_team_scratches)]

    away_team_id = game_center_data.get('awayTeam', {}).get('id', 0)
    home_team_id = game_center_data.get('homeTeam', {}).get('id', 0)
    away_team_abbrev = game_center_data.get('awayTeam', {}).get('abbrev', '')
    home_team_abbrev = game_center_data.get('homeTeam', {}).get('abbrev', '')
    away_team_score = game_center_data.get('awayTeam', {}).get('score', 0)
    home_team_score = game_center_data.get('homeTeam', {}).get('score', 0)
    start_time = game_center_data.get('startTimeUTC', '')
    game_date = game_center_data.get('gameDate', '')
    start_time = datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%SZ')
    offset_sign = 1 if game_center_data['easternUTCOffset'][0] == '+' else -1 
    offset_hours, offset_minutes = map(int,  game_center_data['easternUTCOffset'][1:].split(':'))
    time_offset = timedelta(hours=offset_hours * offset_sign, minutes=offset_minutes * offset_sign)
    start_time = start_time + time_offset
    start_time = start_time.strftime('%Y/%m/%d %H:%M:%S')
    home_team_won = 1 if away_team_score < home_team_score else 0
    season_id = game_center_data.get('season', 0)

    if away_team_id == 0 or home_team_id == 0 or away_team_abbrev == '' or home_team_abbrev == '' or season_id == 0:
        return

    if skater_stats == [] or goaltender_stats == []:   
        away_team_roster = nhlAPI.get_Team_Roster_By_Season(away_team_abbrev, season_id)
        home_team_roster = nhlAPI.get_Team_Roster_By_Season(home_team_abbrev, season_id)

        def map_roster_ids(roster):
            forwards = roster.get('forwards', [])
            defensemen = roster.get('defensemen', [])
            goalies = roster.get('goalies', [])
            
            return [player['id'] for player in (forwards + defensemen)], [player['id'] for player in goalies]

        active_away_team_skater_ids, active_away_team_goaltender_ids = map_roster_ids(away_team_roster)
        active_home_team_skater_ids, active_home_team_goaltender_ids = map_roster_ids(home_team_roster)
        active_away_team_skater_ids = [nhl_id for nhl_id in active_away_team_skater_ids if nhl_id not in scratched_player_nhl_ids]
        active_away_team_goaltender_ids = [nhl_id for nhl_id in active_away_team_goaltender_ids if nhl_id not in scratched_player_nhl_ids]
        active_home_team_skater_ids = [nhl_id for nhl_id in active_home_team_skater_ids if nhl_id not in scratched_player_nhl_ids]
        active_home_team_goaltender_ids = [nhl_id for nhl_id in active_home_team_goaltender_ids if nhl_id not in scratched_player_nhl_ids]

        skater_rows_with_team_side = [
            {'player_id': nhl_id, 'team_side': 'AWAY'} for nhl_id in active_away_team_skater_ids
        ] + [
            {'player_id': nhl_id, 'team_side': 'HOME'} for nhl_id in active_home_team_skater_ids
        ]

        goaltender_rows_with_team_side = [
            {'player_id': nhl_id, 'team_side': 'AWAY'} for nhl_id in active_away_team_goaltender_ids
        ] + [
            {'player_id': nhl_id, 'team_side': 'HOME'} for nhl_id in active_home_team_goaltender_ids
        ]

        sakter_items = [{'player_id': player['player_id'], 'team_side': player['team_side'], 'stats': {}} for player in skater_rows_with_team_side]
        goaltender_items = [{'player_id': player['player_id'], 'team_side': player['team_side'], 'stats': {}} for player in goaltender_rows_with_team_side]
    else:
        sakter_items = [{'player_id':skater['player_id'], 'team_side':skater['team_side'], 'stats':{'position':skater['position'], 'goals':skater['goals'], 'assists':skater['assists'], 'points':skater['points'], 'plus_minus':skater['plus_mius'], 'penalty_minutes':skater['penalty_minutes'], 'time_on_ice':skater['time_on_ice'], 'corsi_for':skater['corsi_for'], 'corsi_against':skater['corsi_against'], 'fenwick_for_percent':skater['fenwick_for_percent'], 'fenwick_for_percent_relative':skater['fenwick_for_percent_relative']}} for skater in skater_stats]
        goaltender_items = [{'player_id':goaltender['player_id'], 'team_side':goaltender['team_side'], 'stats':{'position':goaltender['position'], 'penalty_minutes':goaltender['penalty_minutes'], 'time_on_ice':goaltender['time_on_ice'], 'save_percentage':goaltender['save_percentage'], 'goals_against':goaltender['goals_against']}} for goaltender in goaltender_stats]
        
    sakter_items = [sakter_item for sakter_item in sakter_items if sakter_item is not None]
    goaltender_items = [goaltender_item for goaltender_item in goaltender_items if goaltender_item is not None]
    recent_form_game_ids = []

    for sakter_item in sakter_items:
        
        all_skater_items = get_skater_historical_stats(sakter_item['player_id'], engine)
        plays_for_home_team = 1 if sakter_item['team_side'] == 'HOME' else 0
        is_goaltender = 0
        is_forward = 1

        past_sorted_skater_items = sorted(
            map(convert_time_on_ice_to_integer,
                filter(lambda item: is_past_game_item(item, gameId),
                    filter(has_time_on_ice,
                            filter(has_game_relationship, all_skater_items)
                            )
                    )
                ),
            key=lambda item: item['gameid']
        )

        total_games = len(past_sorted_skater_items)

        games_to_fill = 10 - len(past_sorted_skater_items)

        while games_to_fill > 0:
            past_sorted_skater_items.insert(0, {
                'gameid': gameId,
                'season_id': season_id,
                'stats': {
                    'position': None,
                    'goals': None,
                    'assists': None,
                    'points': None,
                    'plus_minus': None,
                    'penalty_minutes': None,
                    'time_on_ice': None,
                    'corsi_for': None,
                    'corsi_against': None,
                    'fenwick_for_percent': None,
                    'fenwick_for_percent_relative': None
                },
            })
            games_to_fill -= 1

        if sakter_item['stats'] and sakter_item['stats'].get('time_on_ice'):
            sakter_item['stats']['time_on_ice'] = time_on_ice_string_to_decimal(sakter_item['stats']['time_on_ice'])

        position = next(
            (item['stats'].get('position') for item in past_sorted_skater_items if item['stats'].get('position')),
            None
        )

        recent_form = get_recent_form(past_sorted_skater_items)
        weighted_stats = get_weighted_averages(past_sorted_skater_items, season_id)
        current_game_stats = get_current_game_stats(sakter_item['stats']) if sakter_item['stats'] else []
        engine.execute("INSERT INTO model_input(game_id, start_time, player_id,  position, plays_for_home_team, home_team_won, total_games, is_goaltender, is_forward, weighted_average_goals, weighted_average_assists, weighted_average_points, weighted_average_plus_minus, weighted_average_penalty_minutes, weighted_average_time_on_ice, weighted_average_corsi_for, weighted_average_corsi_against, weighted_average_fenwick_for_percent, weighted_average_fenwick_for_percent_relative, recent_form_goals, recent_form_assists, recent_form_points, recent_form_plus_minus, recent_form_penalty_minutes, recent_form_time_on_ice,recent_form_corsi_for, recent_form_corsi_against, recent_form_fenwick_for_percent, recent_form_fenwick_for_percent_relative, current_game_position, current_game_goals, current_game_assists, current_game_points, current_game_plus_minus, current_game_penalty_minutes, current_game_time_on_ice, current_game_corsi_for, current_game_corsi_against, current_game_fenwick_for_percent, current_game_fenwick_for_percent_relative) VALUES(%s, %s, %s,  %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (gameId, start_time, sakter_item['player_id'],  sakter_item['stats']['position'], plays_for_home_team, home_team_won, total_games, is_goaltender, is_forward, weighted_stats['weighted_average_goals'], weighted_stats['weighted_average_assists'], weighted_stats['weighted_average_points'], weighted_stats['weighted_average_plus_minus'], weighted_stats['weighted_average_penalty_minutes'], weighted_stats['weighted_average_time_on_ice'], weighted_stats['weighted_average_corsi_for'], weighted_stats['weighted_average_corsi_against'], weighted_stats['weighted_average_fenwick_for_percent'], weighted_stats['weighted_average_fenwick_for_percent_relative'], recent_form['stats']['recent_form_goals'], recent_form['stats']['recent_form_assists'], recent_form['stats']['recent_form_points'], recent_form['stats']['recent_form_plus_minus'], recent_form['stats']['recent_form_penalty_minutes'], recent_form['stats']['recent_form_time_on_ice'], recent_form['stats']['recent_form_corsi_for'], recent_form['stats']['recent_form_corsi_against'], recent_form['stats']['recent_form_fenwick_for_percent'], recent_form['stats']['recent_form_fenwick_for_percent_relative'], current_game_stats['current_game_position'], current_game_stats['current_game_goals'], current_game_stats['current_game_assists'], current_game_stats['current_game_points'], current_game_stats['current_game_plus_minus'], current_game_stats['current_game_penalty_minutes'], current_game_stats['current_game_time_on_ice'], current_game_stats['current_game_corsi_for'], current_game_stats['current_game_corsi_against'], current_game_stats['current_game_fenwick_for_percent'], current_game_stats['current_game_fenwick_for_percent_relative']))
    
    for goaltender_item in goaltender_items:

        all_goaltender_items = get_goaltender_historical_stats(goaltender_item['player_id'], engine)
        plays_for_home_team = 1 if goaltender_item['team_side'] == 'HOME' else 0
        is_goaltender = 1
        is_forward = 0

        past_sorted_goaltender_items = sorted(
            map(convert_time_on_ice_to_integer,
                filter(lambda item: is_past_game_item(item, gameId),
                    filter(has_time_on_ice,
                            filter(has_game_relationship, all_goaltender_items)
                            )
                    )
                ),
            key=lambda item: item['gameid']
        )

        total_games = len(past_sorted_goaltender_items)

        games_to_fill = 10 - len(past_sorted_goaltender_items)

        while games_to_fill > 0:
            past_sorted_goaltender_items.insert(0, {
                'gameid': gameId,
                'season_id': season_id,
                'stats': {
                    'position': None,
                    'penalty_minutes': None,
                    'time_on_ice': None,
                    'save_percentage': None,
                    'goals_against': None
                },
            })
            games_to_fill -= 1

        if goaltender_item['stats'] and goaltender_item['stats'].get('time_on_ice'):
            goaltender_item['stats']['time_on_ice'] = time_on_ice_string_to_decimal(goaltender_item['stats']['time_on_ice'])

        position = next(
            (item['stats'].get('position') for item in past_sorted_goaltender_items if item['stats'].get('position')),
            None
        )

        recent_form = get_recent_form(past_sorted_goaltender_items)
        current_game_stats = get_current_game_stats(goaltender_item['stats']) if goaltender_item['stats'] else []
        weighted_stats = get_weighted_averages(past_sorted_goaltender_items, season_id)

        engine.execute("INSERT INTO model_input(game_id, start_time, player_id,  position, plays_for_home_team, home_team_won, total_games, is_goaltender, is_forward, weighted_average_penalty_minutes, weighted_average_time_on_ice, weighted_average_save_percentage, weighted_average_goals_against, recent_form_penalty_minutes, recent_form_time_on_ice, recent_form_save_percentage, recent_form_goals_against, current_game_position, current_game_penalty_minutes, current_game_time_on_ice, current_game_save_percentage, current_game_goals_against) VALUES(%s, %s, %s,  %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (gameId, start_time, goaltender_item['player_id'],  goaltender_item['stats']['position'], plays_for_home_team, home_team_won, total_games, is_goaltender, is_forward, weighted_stats['weighted_average_penalty_minutes'], weighted_stats['weighted_average_time_on_ice'], weighted_stats['weighted_average_save_percentage'], weighted_stats['weighted_average_goals_against'], recent_form['stats']['recent_form_penalty_minutes'], recent_form['stats']['recent_form_time_on_ice'], recent_form['stats']['recent_form_save_percentage'], recent_form['stats']['recent_form_goals_against'], current_game_stats['current_game_position'], current_game_stats['current_game_penalty_minutes'], current_game_stats['current_game_time_on_ice'], current_game_stats['current_game_save_percentage'], current_game_stats['current_game_goals_against']))
    
    return
