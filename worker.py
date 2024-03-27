from passlib.hash import sha256_crypt
import statsapi as mlb
import pandas as pd
from datetime import date, time, datetime, timedelta
from database import database
from pytz import timezone
from functions import batting, predict, starters, smartContract, sanitycheck, odds
from schedule import schedule
import requests


version = 'v1'
gamePk = '12345'
url = f'https://statsapi.mlb.com/api/game/747818/feed/live'

# boxscore = mlb.boxscore_data('747800')
boxscore = mlb.boxscore_data('747810')

print(len(boxscore['gameBoxInfo']))
# Use data as needed
for key in boxscore['gameBoxInfo']:
    print(key)

