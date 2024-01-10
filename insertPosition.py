# Dependencies
import statsapi as mlb
import time
from datetime import date, timedelta, datetime
import numpy as np
import pandas as pd
import sqlite3
from database import database
from sqlalchemy import text
import csv
import requests
from schedule import schedule
import pickle
import joblib
import requests

engine = database.connect_to_db()
engine.execute(text("CREATE TABLE IF NOT EXISTS site_list(site TEXT);"))


engine.execute(text(f"INSERT INTO site_list(site) VALUES('bet487.org');"))
engine.execute(text(f"INSERT INTO site_list(site) VALUES('sports411.ag');"))
engine.execute(text(f"INSERT INTO site_list(site) VALUES('probet42.com');"))
engine.execute(text(f"INSERT INTO site_list(site) VALUES('shiba.ag');"))

