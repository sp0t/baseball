from passlib.hash import sha256_crypt
import statsapi as mlb
import pandas as pd
from datetime import date, time, datetime, timedelta
from database import database
from pytz import timezone
from functions import batting, predict, starters, smartContract, sanitycheck, odds
from schedule import schedule
import requests


data = mlb.boxscore_data('747801')
    
# Game Info 
game_date = data['gameId'][:10]
away_team = data['teamInfo']['away']['abbreviation']
home_team = data['teamInfo']['home']['abbreviation']

#insert position data
awayBatters = data['awayBatters']

print(awayBatters)

