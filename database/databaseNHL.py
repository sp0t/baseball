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


def connect_to_db(): 
    
    try: 
        engine = create_engine('postgresql://postgres:lucamlb123@localhost:5432/betnhl', connect_args = {'connect_timeout': 10}, echo=False, pool_size=20, max_overflow=0)
        print('Connection Initiated')
    except:
        raise ValueError("Can't connect to Heroku PostgreSQL! You must be so embarrassed")
    return engine
