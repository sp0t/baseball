import statsapi as mlb
import pandas as pd
from datetime import date
from database import database

conn, cur = database.connect_to_db()
