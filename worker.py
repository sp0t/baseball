from passlib.hash import sha256_crypt
import statsapi as mlb
import pandas as pd
from datetime import date, time, datetime, timedelta
from database import database
from pytz import timezone
from functions import batting, predict, starters, smartContract, sanitycheck, odds
from schedule import schedule
import requests


# boxscore = mlb.boxscore_data('746418')
boxscore = mlb.boxscore_data('745283')
away_score = boxscore['awayBattingTotals']['r']
home_score = boxscore['homeBattingTotals']['r']
att_exists = False
t_exists = False

for item in boxscore['gameBoxInfo']:
    if item.get('label') == 'Att':
        att_exists = True
    elif item.get('label') == 'T':
        t_exists = True

data ={}
data['away_score'] = 0
data['home_score'] = 0

if att_exists == True and t_exists == True:
    data['away_score'] = away_score
    data['home_score'] = home_score    

print(data)

