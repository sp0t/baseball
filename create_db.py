import psycopg2
import pandas as pd
from io import StringIO
from database import database
from schedule import schedule


path_1 = "algorithms/model_1a_2021_results.csv"
X_train_1 = pd.read_csv(path_1).iloc[:, 1:]
path_2 = "algorithms/model_1a_2022_results.csv"
X_train_2 = pd.read_csv(path_2).iloc[:, 1:]


# Games
col_names = list(X_train_1.columns)
games_string = "CREATE TABLE IF NOT EXISTS X_train ("
for col in col_names: 
    new_string = col + " VARCHAR(255), "
    games_string += new_string
games_string += ")"
games_string = games_string.replace(', )', ')')
games_string = games_string.replace("game_id VARCHAR(255)", "game_id VARCHAR(255) PRIMARY KEY")

engine = database.connect_to_db()
#engine.execute("DROP TABLE IF EXISTS X_train")
engine.execute(games_string)


X_train_1.to_sql("X_train", con = engine, if_exists='append')
X_train_2.to_sql("X_train", con = engine, if_exists='append')


