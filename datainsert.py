from sqlalchemy import create_engine
import pandas as pd
import statsapi as mlb
from datetime import date, time, datetime, timedelta
from pytz import timezone


#csv file
csv_path = 'betmlb_db.csv'
db_string = "postgresql://postgres:123@localhost:5432/testdb"

db = create_engine(db_string)

df = pd.read_csv(csv_path)
data = df.set_index('game_id').T.to_dict('dict')


#create tables
db.execute("DROP TABLE IF EXISTS game_table;")
db.execute("DROP TABLE IF EXISTS batter_table;")
db.execute("DROP TABLE IF EXISTS pitcher_table;")
db.execute("DROP TABLE IF EXISTS schedule;")
db.execute("CREATE TABLE IF NOT EXISTS game_table(game_id TEXT, game_date TEXT, away_team TEXT, home_team TEXT, away_score TEXT, home_score TEXT, winner TEXT);")
db.execute("CREATE TABLE IF NOT EXISTS batter_table(game_id TEXT, playerid TEXT, team TEXT, position TEXT, atbats TEXT, avg TEXT, baseonballs TEXT, doubles TEXT, "\
           "hits TEXT, homeruns TEXT, obp TEXT, ops TEXT, rbi TEXT, runs TEXT, slg TEXT, strikeouts TEXT, triples TEXT);")
db.execute("CREATE TABLE IF NOT EXISTS pitcher_table(game_id TEXT, team TEXT, role TEXT, playerid TEXT, atbats TEXT, baseonballs TEXT, blownsaves TEXT, doubles TEXT, earnedruns TEXT, era TEXT, "\
           "hits TEXT, holds TEXT, homeruns TEXT, inningspitched TEXT, losses TEXT, pitchesthrown TEXT, rbi TEXT, runs TEXT, strikeouts TEXT, strikes TEXT, triples TEXT, "\
           "whip TEXT, wins TEXT);")
db.execute("CREATE TABLE IF NOT EXISTS schedule();")
          
for i in data:
#game_table insert query
    game_table_sql = 'INSERT INTO game_table( game_id, game_date, away_team, home_team, away_score, home_score, winner) VALUES (' + \
                     '\'' + str(i) + '\'' + ',' +  '\'' + data[i]['game_date'] + '\'' +  ',' + '\'' +  data[i]['away_team'] + '\'' +  ',' + \
                     '\'' + data[i]['home_team'] + '\'' +  ',' + '\'' +  str(data[i]['away_score']) + '\'' +  ','  + '\'' + str(data[i]['home_score'])\
                     + '\'' + ',' + '\'' +str(data[i]['winner']) + '\'' + ');'
    db.execute(game_table_sql)
    
#pitcher_table insert query
    for k in range(1, 5):
        if k % 4 == 0:
            key, team, role = 'home_bullpen_', 'home', 'bullpen'
        elif k % 4 == 1:
            key, team, role = 'away_starter_', 'away', 'starter'
        elif k % 4 == 2:
            key, team, role = 'away_bullpen_', 'away', 'bullpen'
        elif k % 4 == 3:
            key, team, role = 'home_starter_', 'home', 'starter'
   
        pitcher_table_sql = 'INSERT INTO pitcher_table( game_id, playerid, team, role, atbats, baseonballs, blownsaves, doubles, earnedruns, era,' \
                      'hits, holds, homeruns, inningspitched, losses, pitchesthrown, rbi, runs, strikeouts, strikes, triples, whip, wins) VALUES (' + \
                     '\'' + str(i) + '\'' + ',' +  '\'' + str(data[i][key + 'playerid']) + '\'' +  ',' + '\'' +  team + '\'' +  ',' + '\'' + role + '\'' +  ',' + \
                     '\'' + str(data[i][key + 'atbats']) + '\'' +  ',' + '\'' + str(data[i][key + 'baseonballs']) + '\'' +  ',' + '\'' + str(data[i][key + 'blownsaves']) + '\'' +  ',' + \
                     '\'' + str(data[i][key + 'doubles']) + '\'' +  ',' + '\'' + str(data[i][key + 'earnedruns']) + '\'' +  ',' + '\'' + str(data[i][key + 'era']) + '\'' + ',' + \
                     '\'' + str(data[i][key + 'hits']) + '\'' +  ',' + '\'' + str(data[i][key + 'holds']) + '\'' +  ',' + '\'' + str(data[i][key + 'homeruns']) + '\'' +  ',' + \
                     '\'' + str(data[i][key + 'inningspitched']) + '\'' +  ',' + '\'' + str(data[i][key + 'losses']) + '\'' +  ',' + '\'' + str(data[i][key + 'pitchesthrown']) + '\'' +  ',' + \
                     '\'' + str(data[i][key + 'rbi']) + '\'' +  ',' + '\'' + str(data[i][key + 'runs']) + '\'' +  ',' + '\'' + str(data[i][key + 'strikeouts']) + '\'' +  ',' + \
                     '\'' + str(data[i][key + 'strikes']) + '\'' +  ',' + '\'' + str(data[i][key + 'triples']) + '\'' +  ',' + '\'' + str(data[i][key + 'whip']) + '\'' +  ',' + \
                     '\'' + str(data[i][key + 'wins']) + '\'' + ');'
    
        db.execute(pitcher_table_sql)

#batter_table insert query
    for j in range(1, 19):
        if(j < 10):
            batter_table_sql = 'INSERT INTO batter_table( game_id, playerid, team, position, atbats, avg, baseonballs, doubles, hits, homeruns, '\
                         'obp, ops, rbi, runs, slg, strikeouts, triples) VALUES (' + \
                         '\'' + str(i) + '\'' + ',' +  '\'' + str(data[i]['away_b' + str(j) +'_playerid']) + '\'' +  ',' + \
                         '\'' + 'away' + '\'' + ',' + '\'' +  str(j) + '\'' +  ',' +\
                         '\'' + str(data[i]['away_b' + str(j) + '_atbats']) + '\'' +  ',' + '\'' + str(data[i]['away_b' + str(j) + '_avg']) + '\'' +  ',' + \
                         '\'' + str(data[i]['away_b' + str(j) + '_baseonballs']) + '\'' +  ',' + '\'' + str(data[i]['away_b' + str(j) + '_doubles']) + '\'' +  ',' + \
                         '\'' + str(data[i]['away_b' + str(j) + '_hits']) + '\'' +  ',' + '\'' + str(data[i]['away_b' + str(j) + '_homeruns']) + '\'' +  ',' + \
                         '\'' + str(data[i]['away_b' + str(j) + '_obp']) + '\'' +  ',' + '\'' + str(data[i]['away_b' + str(j) + '_ops']) + '\'' +  ',' + \
                         '\'' + str(data[i]['away_b' + str(j) + '_rbi']) + '\'' +  ',' + '\'' + str(data[i]['away_b' + str(j) + '_runs']) + '\'' +  ',' + '\'' + str(data[i]['away_b' + str(j) + '_slg']) + '\'' +  ',' + \
                         '\'' + str(data[i]['away_b' + str(j) + '_strikeouts']) + '\'' +  ',' + '\'' + str(data[i]['away_b' + str(j) + '_triples']) + '\'' + ');'
        else:
            batter_table_sql = 'INSERT INTO batter_table( game_id, playerid, team, position, atbats, avg, baseonballs, doubles, hits, homeruns, '\
                         'obp, ops, rbi, runs, slg, strikeouts, triples) VALUES (' + \
                         '\'' + str(i) + '\'' + ',' +  '\'' + str(data[i]['home_b' + str(j-9) +'_playerid']) + '\'' +  ',' + \
                         '\'' + 'home' + '\'' + ',' + '\'' +  str(j-9) + '\'' +  ',' +\
                         '\'' + str(data[i]['home_b' + str(j-9) + '_atbats']) + '\'' +  ',' + '\'' + str(data[i]['home_b' + str(j-9) + '_avg']) + '\'' +  ',' + \
                         '\'' + str(data[i]['home_b' + str(j-9) + '_baseonballs']) + '\'' +  ',' + '\'' + str(data[i]['home_b' + str(j-9) + '_doubles']) + '\'' +  ',' + \
                         '\'' + str(data[i]['home_b' + str(j-9) + '_hits']) + '\'' +  ',' + '\'' + str(data[i]['home_b' + str(j-9) + '_homeruns']) + '\'' +  ',' + \
                         '\'' + str(data[i]['home_b' + str(j-9) + '_obp']) + '\'' +  ',' + '\'' + str(data[i]['home_b' + str(j-9) + '_ops']) + '\'' +  ',' + \
                         '\'' + str(data[i]['away_b' + str(j-9) + '_rbi']) + '\'' +  ',' + '\'' + str(data[i]['home_b' + str(j-9) + '_runs']) + '\'' +  ',' + '\'' + str(data[i]['home_b' + str(j-9) + '_slg']) + '\'' +  ',' + \
                         '\'' + str(data[i]['home_b' + str(j-9) + '_strikeouts']) + '\'' +  ',' + '\'' + str(data[i]['home_b' + str(j-9) + '_triples']) + '\'' + ');'
        
        db.execute(batter_table_sql)
    
    print(i)
               
print('end')