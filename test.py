from sqlalchemy import create_engine
import pandas as pd
import statsapi as mlb
from datetime import date, time, datetime, timedelta
from pytz import timezone
import numpy as np
from database import database

engine = database.connect_to_db()

engine.execute("CREATE TABLE IF NOT EXISTS odds_table(game_id TEXT, game_date TEXT, away TEXT, home TEXT, start_time TEXT, away_open INT, away_close INT, home_open INT, home_close INT);")