from database import database
import pandas as pd
import csv
from datetime import datetime

engine = database.connect_to_db()
engine.execute("CREATE TABLE IF NOT EXISTS graph_table(id SERIAL PRIMARY KEY, betdate TEXT, away TEXT, home TEXT, bet TEXT, american TEXT, decimal TEXT, result TEXT, wcount TEXT, ncount TEXT, run_win TEXT, RC TEXT, risk TEXT, pl TEXT, f_pos TEXT, s_pos TEXT, f_neg TEXT, s_neg TEXT);")

with open('Book1.csv', mode='r') as file:
    csv_reader = csv.DictReader(file)
    for row in csv_reader:
        betdate = datetime.strptime(row['Date'], '%d/%m/%Y')
        betdate = betdate.strftime('%Y-%m-%d')
        run_win = round(float(row['running % wins']) * 100, 2)
        f_pos = round(float(row['1st positive threshold']) * 100, 2)
        s_pos = round(float(row['2nd positive threshold']) * 100, 2)
        f_neg = round(float(row['1st negative threshold']) * 100, 2)
        s_neg = round(float(row['2nd negative threshold']) * 100, 2)
        print(run_win,f_pos, s_pos, f_neg, s_neg)
        engine.execute("INSERT INTO graph_table(betdate, away, home, bet, american, decimal, result, wcount, ncount, run_win, RC, risk, pl, f_pos, s_pos, f_neg, s_neg) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (betdate, row['Away Team'], row['Home Team'], row['Bet'], row['American Odds'], row['Decimal Odds'], row['Result'], row['running W'], row['n. bets'], run_win, row['RC'], row['Risk'], row['P/L'], f_pos, s_pos, f_neg, s_neg))
        if(row['Betting Day'] == '335'):
            break