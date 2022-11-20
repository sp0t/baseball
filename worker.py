import sched
import psycopg2
from io import StringIO
import statsapi as mlb
from datetime import date, datetime, timedelta
import time
import pandas as pd

from database import database
from schedule import schedule

#conn, cur = database.connect_to_db()

database.update_database()
schedule.update_schedule()