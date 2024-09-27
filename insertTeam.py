import nhlAPI from API
from database import databaseNHL

engine = databaseNHL.connect_to_db()
data = nhlAPI.get_Teams()
teams = data['data']
leagues = [
    'Carolina Hurricanes',
    'Boston Bruins',
    'Columbus Blue Jackets',
    'Buffalo Sabres',
    'New Jersey Devils',
    'Detroit Red Wings',
    'New York Islanders',
    'Florida Panthers',
    'New York Rangers',
    'Montréal Canadiens',
    'Philadelphia Flyers',
    'Ottawa Senators',
    'Pittsburgh Penguins',
    'Tampa Bay Lightning',
    'Washington Capitals',
    'Toronto Maple Leafs',
    'Chicago Blackhawks',
    'Anaheim Ducks',
    'Colorado Avalanche',
    'Calgary Flames',
    'Dallas Stars',
    'Edmonton Oilers',
    'Minnesota Wild',
    'Los Angeles Kings',
    'Nashville Predators',
    'San Jose Sharks',
    'St. Louis Blues',
    'Seattle Kraken',
    'Utah Hockey Club',
    'Vancouver Canucks',
    'Winnipeg Jets',
    'Vegas Golden Knights'
]

for team in teams:
    if team['fullName'] in leagues:
        engine.execute("INSERT INTO team_table(team_id, team_name, team_abbr, franchise_id, league) VALUES(%s, %s, %s, %s, %s)", (team['id'], team['fullName'], team['triCode'], team['franchiseId'], '1'))
    else:
        engine.execute("INSERT INTO team_table(team_id, team_name, team_abbr, franchise_id, league) VALUES(%s, %s, %s, %s, %s)", (team['id'], team['fullName'], team['triCode'], team['franchiseId'], '0'))

