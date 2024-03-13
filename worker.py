from passlib.hash import sha256_crypt
import statsapi as mlb
import pandas as pd
from datetime import date, time, datetime, timedelta
from database import database
from pytz import timezone

# data = mlb.boxscore_data("748104")
end_date = date.today()
print(end_date)
schedule = mlb.schedule(start_date=end_date)
print(schedule)