import itertools
import math
from sqlalchemy import text

coordinate = {
    'AZ':{
        'x': 33.44506580488069, 
        'y':-112.06717044285102
        },
    'ATL':{
        'x': 33.8899868303296, 
        'y':-84.46702274534717
        },
    'BAL':{
        'x': 39.28393555896092, 
        'y':-76.62113104780491
        },
    'BOS':{
        'x': 42.34680324299623, 
        'y':-71.09660625887447
        },
    'CHC':{
        'x': 41.94852614607134, 
        'y':-87.65527905838262
        },
    'CWS':{
        'x': 41.831296855091956, 
        'y':-87.6333793319141
        },
    'CIN':{
        'x': 39.09749386715958, 
        'y':-84.50704752089635
        },
    'CLE':{
        'x': 41.49606082565256, 
        'y':-81.68483356261892
        },
    'COL':{
        'x': 39.756055480877954, 
        'y':-104.99417810265344
        },
    'DET':{
        'x': 42.33897803317267, 
        'y':-83.04792750305661
        },
    'HOU':{
        'x': 29.685238570058257, 
        'y':-95.40706736030235
        },
    'KC':{
        'x': 39.051830175313626, 
        'y':-94.47953099762564
        },
    'LAA':{
        'x': 33.80015889005588, 
        'y':-117.88189964621851
        },
    'LAD':{
        'x': 34.07397538920459, 
        'y':-118.23943258988264
        },
    'MIA':{
        'x': 25.77831291681971, 
        'y':-80.21872003853885
        },
    'MIL':{
        'x': 43.0271584609408, 
        'y':-87.9712748644097
        },
    'MIN':{
        'x': 44.98184587063457, 
        'y':-93.27759333094187
        },
    'NYM':{
        'x': 40.757245534823234, 
        'y':-73.84539324814143
        },
    'NYY':{
        'x': 40.82991559092179, 
        'y':-73.92534028175406
        },
    'OAK':{
        'x': 37.75174068076763, 
        'y':-122.20052004505865
        },
    'PHI':{
        'x': 39.90632372286718, 
        'y':-75.16553941898019
        },
    'PIT':{
        'x': 40.44758821897035, 
        'y':-80.00658600244697
        },
    'SD':{
        'x': 32.70771754817479, 
        'y':-117.15703381774901
        },
    'SF':{
        'x': 37.77881442401596, 
        'y':-122.3892383214555
        },
    'SEA':{
        'x': 47.59145153513236, 
        'y':-122.33247862820821
        },
    'STL':{
        'x': 38.62277803268148, 
        'y':-90.19272434317051
        },
    'TB':{
        'x': 27.76781388955309, 
        'y':-82.65337945939267
        },
    'TEX':{
        'x': 32.747665179633735, 
        'y':-97.0819831898959
        },
    'TOR':{
        'x': 43.64155790066979, 
        'y':-79.38956747231032
        },
    'WSH':{
        'x': 38.873177154954355, 
        'y':-77.00745437787236
        }
}

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0  # Radius of the Earth in kilometers

    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance_km = R * c
    return distance_km * 0.621371  # Convert to miles

engine = database.connect_to_db()
engine.execute(text("CREATE TABLE IF NOT EXISTS distance_table(team1 TEXT, team2 TEXT, distance FLOAT);"))

# List of teams
teams = ['OAK', 'PIT', 'SD', 'SEA', 'SF', 'STL', 'TB', 'TEX', 'TOR', 'MIN', 'PHI', 'ATL', 'CWS', 'MIA', 'NYY', 'MIL', 'LAA', 'AZ', 'BAL', 'BOS', 'CHC', 'CIN', 'CLE', 'COL', 'DET', 'HOU', 'KC', 'LAD', 'WSH', 'NYM']

# Generate all possible game combinations
game_combinations = list(itertools.combinations(teams, 2))

# Filter the combinations to ensure only one game is created for each pair of teams
filtered_combinations = [[x[0],x[1]] for x in game_combinations if (x[1], x[0]) not in game_combinations]

# Print the filtered game combinations
for combination in filtered_combinations:
    print(combination[0], combination[1], haversine(coordinate[combination[0]]['x'], coordinate[combination[0]]['y'], coordinate[combination[1]]['x'], coordinate[combination[1]]['y']).toFixed(2))
    engine.execute(f"INSERT INTO distance_table('{combination[0]}', '{combination[1]}', '{haversine(coordinate[combination[0]]['x'], coordinate[combination[0]]['y'], coordinate[combination[1]]['x'], coordinate[combination[1]]['y']).toFixed(2)}');")

