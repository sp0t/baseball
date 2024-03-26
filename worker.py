from passlib.hash import sha256_crypt
import statsapi as mlb
import pandas as pd
from datetime import date, time, datetime, timedelta
from database import database
from pytz import timezone
from functions import batting, predict, starters, smartContract, sanitycheck, odds
from schedule import schedule


data = mlb.boxscore_data('747807')
away_score = data['awayBattingTotals']['r']
home_score = data['homeBattingTotals']['r']

data ={}
data['away_score'] = away_score
data['home_score'] = home_score

print(data)