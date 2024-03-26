from passlib.hash import sha256_crypt
import statsapi as mlb
import pandas as pd
from datetime import date, time, datetime, timedelta
from database import database
from pytz import timezone
from functions import batting, predict, starters, smartContract, sanitycheck, odds
from schedule import schedule


password = sha256_crypt.encrypt('MODALSAMEER!@#$')

print(password)