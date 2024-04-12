from passlib.hash import sha256_crypt
import statsapi as mlb
import pandas as pd
from datetime import date, time, datetime, timedelta
from database import database
from pytz import timezone
from functions import batting, predict, starters, smartContract, sanitycheck, odds
from schedule import schedule
import requests
from sqlalchemy import text
from functions_c import batting_c, starters_c, predict_c
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


day = date.today() - timedelta(days = 1)
last_record = datetime.strptime('2024/04/12', '%Y/%m/%d').date()
if last_record < day:
    print('true')
print(day)