from sqlalchemy import create_engine
import pandas as pd
import statsapi as mlb
from datetime import date, time, datetime, timedelta
from pytz import timezone
import numpy as np
from database import database

engine = database.connect_to_db()

engine.execute("CREATE TABLE IF NOT EXISTS staking_table(id SERIAL PRIMARY KEY, game_date TEXT, away TEXT, home TEXT, bet TEXT, american_odd INT, decimal_odd FLOAT(8), bet_size FLOAT(8), result TEXT, win_count INT, bet_count INT, bet_win FLOAT(8), risk_coeff FLOAT(8), stake_size FLOAT(8), pl_coeff FLOAT(8));")

