
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
from API import nhlAPI


oldengine = create_engine('postgresql://postgres:lucamlb123@localhost:5432/betnhl', connect_args = {'connect_timeout': 10}, echo=False, pool_size=20, max_overflow=0)
newengine = create_engine('postgresql://postgres:lucamlb123@localhost:5432/betnhl_new', connect_args = {'connect_timeout': 10}, echo=False, pool_size=20, max_overflow=0)

skater_res = pd.read_sql(f"SELECT COALESCE(game.nhl_id, '0') AS game_id, player.nhl_id as player_id, player_stats.team_side, player_stats.plus_minus, player_stats.penalty_minutes, player_stats.assists, player_stats.time_on_ice, player_stats.fenwick_for_percent_relative, player_stats.corsi_for, player_stats.position, player_stats.goals, player_stats.points, player_stats.corsi_against, player_stats.fenwick_for_percent FROM player_stats LEFT JOIN game ON player_stats.game_id = game.id LEFT JOIN player ON player_stats.player_id = player.id WHERE player_stats.save_percentage is NULL AND player_stats.goals_against IS NULL ORDER BY game_id, team_side, position;", con = oldengine).to_dict('records')

for skater in skater_res:
    print('skater ------->', skater['game_id'])
    newengine.execute("INSERT INTO skater_stats(game_id, player_id, team_side,  plus_mius, penalty_minutes, assists, time_on_ice, fenwick_for_percent_relative, corsi_for, position, goals, points, corsi_against, fenwick_for_percent) VALUES(%s, %s, %s,  %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (skater['game_id'], skater['player_id'], skater['team_side'],  skater['plus_minus'], skater['penalty_minutes'], skater['assists'], skater['time_on_ice'], skater['fenwick_for_percent_relative'], skater['corsi_for'], skater['position'], skater['goals'], skater['points'], skater['corsi_against'], skater['fenwick_for_percent']))


goaltender_res = pd.read_sql(f"SELECT COALESCE(game.nhl_id, '0') as game_id, player.nhl_id as player_id, player_stats.team_side, player_stats.penalty_minutes, player_stats.time_on_ice, player_stats.position, player_stats.save_percentage, player_stats.goals_against FROM player_stats LEFT JOIN game ON player_stats.game_id = game.id LEFT JOIN player ON player_stats.player_id = player.id WHERE player_stats.save_percentage IS NOT NULL AND player_stats.goals_against IS NOT NULL ORDER BY game_id, team_side, position;", con = oldengine).to_dict('records')

for goaltender in goaltender_res:
    print('goaltender ------->', goaltender['game_id'])
    newengine.execute("INSERT INTO goaltender_stats(game_id, player_id, team_side,  penalty_minutes, time_on_ice, position, save_percentage, goals_against) VALUES(%s, %s, %s,  %s, %s, %s, %s, %s)", (goaltender['game_id'], goaltender['player_id'], goaltender['team_side'],  goaltender['penalty_minutes'], goaltender['time_on_ice'], goaltender['position'], goaltender['save_percentage'], goaltender['goals_against']))

game_res = pd.read_sql(f"SELECT game.nhl_id as game_id, game.away_score, game.home_score, game.state, game.import_state FROM game ORDER BY game_id;", con = oldengine).to_dict('records')

for game in game_res:
    boxscore = nhlAPI.get_Boxscore(game['game_id'])

    if not boxscore:
        continue

    game_date = boxscore['gameDate']
    season_id = boxscore['season']
    start_time = boxscore['startTimeUTC']
    start_time = datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%SZ')
    offset_sign = 1 if boxscore['easternUTCOffset'][0] == '+' else -1 
    offset_hours, offset_minutes = map(int,  boxscore['easternUTCOffset'][1:].split(':'))
    time_offset = timedelta(hours=offset_hours * offset_sign, minutes=offset_minutes * offset_sign)
    start_time = start_time + time_offset
    start_time = start_time.strftime('%Y/%m/%d %H:%M:%S')
    away_team = boxscore['awayTeam']['abbrev']
    home_team = boxscore['homeTeam']['abbrev']


    if boxscore['gameState'] == 'FUT':
        newengine.execute("INSERT INTO game_table(game_id, game_date, away_team, home_team, season_id, state, start_time, import_state) VALUES(%s, %s, %s, %s, %s, %s, %s, %s)", (game['game_id'], game_date, away_team,  home_team, season_id, game['state'], start_time, game['import_state']))
        continue



    away_score = boxscore['awayTeam']['score']
    home_score = boxscore['homeTeam']['score']

    if away_score < home_score:
        winner = 0
    else:
        winner = 1

    newengine.execute("INSERT INTO game_table(game_id, game_date, away_team, home_team, away_score, home_score, winner, season_id, state, start_time, import_state) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (game['game_id'], game_date, away_team,  home_team, away_score, home_score, winner, season_id, game['state'], start_time, game['import_state']))

model_input_res = pd.read_sql(f"SELECT game.nhl_id as gameid, player.nhl_id as playerid, model_input.* FROM model_input LEFT JOIN game ON model_input.game_id = game.id INNER JOIN player ON model_input.player_id = player.id ORDER BY gameid;", con = oldengine).to_dict('records')

for model_input in model_input_res:
    print('model_input ------->', model_input['gameid'])
    start_time = datetime.strptime(model_input['start_time'], '%d/%m/%Y %H:%M:%S+00')
    start_time = start_time.strftime('%Y/%m/%d %H:%M:%S')
    newengine.execute("INSERT INTO model_input(game_id, start_time, player_id,  position, plays_for_home_team, home_team_won, total_games, is_goaltender, is_forward, weighted_average_goals, weighted_average_assists, weighted_average_points, weighted_average_plus_minus, weighted_average_penalty_minutes, weighted_average_time_on_ice, weighted_average_corsi_for, weighted_average_corsi_against, weighted_average_fenwick_for_percent, weighted_average_fenwick_for_percent_relative, weighted_average_save_percentage, weighted_average_goals_against, recent_form_goals, recent_form_assists, recent_form_points, recent_form_plus_minus, recent_form_penalty_minutes, recent_form_time_on_ice,recent_form_corsi_for, recent_form_corsi_against, recent_form_fenwick_for_percent, recent_form_fenwick_for_percent_relative, recent_form_save_percentage, recent_form_goals_against, current_game_position, current_game_goals, current_game_assists, current_game_points, current_game_plus_minus, current_game_penalty_minutes, current_game_time_on_ice, current_game_corsi_for, current_game_corsi_against, current_game_fenwick_for_percent, current_game_fenwick_for_percent_relative, current_game_save_percentage, current_game_goals_against) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (model_input['gameid'], start_time, model_input['playerid'], model_input['position'], model_input['plays_for_home_team'], model_input['home_team_won'], model_input['total_games'], model_input['is_goaltender'], model_input['is_forward'], model_input['weighted_average_goals'], model_input['weighted_average_assists'], model_input['weighted_average_points'], model_input['weighted_average_plus_minus'], model_input['weighted_average_penalty_minutes'], model_input['weighted_average_time_on_ice'], model_input['weighted_average_corsi_for'], model_input['weighted_average_corsi_against'], model_input['weighted_average_fenwick_for_percent'], model_input['weighted_average_fenwick_for_percent_relative'], model_input['weighted_average_save_percentage'], model_input['weighted_average_goals_against'], model_input['recent_form_goals'], model_input['recent_form_assists'], model_input['recent_form_points'], model_input['recent_form_plus_minus'], model_input['recent_form_penalty_minutes'], model_input['recent_form_time_on_ice'],model_input['recent_form_corsi_for'], model_input['recent_form_corsi_against'], model_input['recent_form_fenwick_for_percent'], model_input['recent_form_fenwick_for_percent_relative'], model_input['recent_form_save_percentage'], model_input['recent_form_goals_against'], model_input['current_game_position'], model_input['current_game_goals'], model_input['current_game_assists'], model_input['current_game_points'], model_input['current_game_plus_minus'], model_input['current_game_penalty_minutes'], model_input['current_game_time_on_ice'], model_input['current_game_corsi_for'], model_input['current_game_corsi_against'], model_input['current_game_fenwick_for_percent'], model_input['current_game_fenwick_for_percent_relative'], model_input['current_game_save_percentage'], model_input['current_game_goals_against']))

model_result_res = pd.read_sql(f"SELECT COALESCE(game.nhl_id, '0') as gameid, model_result.* FROM model_result LEFT JOIN game ON model_result.game_id = game.id ORDER BY gameid;", con = oldengine).to_dict('records')

for model_result in model_result_res:
    print('model_result ------->', model_result['gameid'])
    newengine.execute("INSERT INTO predictions(game_id, model_type, away_team, home_team) VALUES(%s, %s, %s,  %s)", (model_result['gameid'], model_result['model_name'], model_result['away_team_win_chance'],  model_result['home_team_win_chance']))

    


