# Dependencies
import statsapi as mlb
import time
from datetime import date, timedelta, datetime
import numpy as np
import pandas as pd
import sqlite3
from database import database
from sqlalchemy import text
import csv
import requests
from schedule import schedule
import pickle
import joblib

# engine = database.connect_to_db()
# engine.execute(text("CREATE TABLE IF NOT EXISTS batter_stats_c(game_id TEXT, game_date TEXT, position TEXT, player_id TEXT, career_atBats float8, career_avg float8, career_homeRuns float8, career_obp float8, career_ops float8, career_rbi float8, career_slg float8, career_strikeOuts float8, recent_atBats float8, recent_avg float8, recent_homeRuns float8, recent_obp float8, recent_ops float8, recent_rbi float8, recent_slg float8, recent_strikeOuts float8, difficulty_rating float, UNIQUE (game_id, player_id));"))
# engine.execute(text("CREATE TABLE IF NOT EXISTS pitcher_stats_c(game_id TEXT, game_date TEXT, position TEXT, player_id TEXT, career_era float8, career_homeRuns float8, career_whip float8, career_battersFaced float8, recent_era float8, recent_homeRuns float8, recent_whip float8, recent_battersFaced float8, difficulty_rating float, UNIQUE (game_id, player_id));"))
# engine.execute(text("CREATE TABLE IF NOT EXISTS league_average(year TEXT, avg FLOAT, obp FLOAT, slg FLOAT, ops FLOAT, era FLOAT, whip FLOAT);"))
# engine.execute(text("CREATE TABLE IF NOT EXISTS win_percent_c(game_id TEXT UNIQUE, away_prob FLOAT, home_prob FLOAT);"))
# engine.execute(text("CREATE TABLE IF NOT EXISTS predict_table(game_id TEXT UNIQUE, la_away_prob TEXT, la_home_prob TEXT, lb_away_prob TEXT, lb_home_prob TEXT, lc_away_prob TEXT, lc_home_prob TEXT);"))
game_date = datetime.today().strftime("%Y/%m/%d")

print(game_date)
