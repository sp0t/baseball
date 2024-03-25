from passlib.hash import sha256_crypt
import statsapi as mlb
import pandas as pd
from datetime import date, time, datetime, timedelta
from database import database
from pytz import timezone
from functions import batting, predict, starters, smartContract, sanitycheck, odds
from schedule import schedule

rosters = schedule.get_rosters('745444')

print(rosters['position']['away'])
res = not bool(rosters['position']['away'])
print(res)
    