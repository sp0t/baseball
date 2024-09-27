import requests

#################################
#
#   Player Information API
#
#################################

#-------- Get Game Log ---------------
#   Retrieve the game log for a specific player, season, and game type.
#   get_Game_Log(8478402, 20232024, 2)
#-------------------------------------

def get_Game_Log(playerID, season, gameType):
    gameLog = {}
    url = f"https://api-web.nhle.com/v1/player/{playerID}/game-log/{season}/{gameType}"
    response = requests.get(url)

    if response.status_code == 200:
        gameLog = response.json()
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
    
    return gameLog

#-------- Get Specific Player Info ---------------
#   Retrieve information for a specific player.
#   get_Specific_Player_Info(8478402)
#-------------------------------------------------

def get_Specific_Player_Info(playerID):
    playerInfo = {}
    url = f"https://api-web.nhle.com/v1/player/{playerID}/landing"
    response = requests.get(url)

    if response.status_code == 200:
        playerInfo = response.json()
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
    
    return playerInfo

#-------- Get Game Log As of Now ---------------
#   Retrieve the game log for a specific player as of the current moment.
#   get_Game_Log_Now(8478402)
#-------------------------------------------------

def get_Game_Log_Now(playerID):
    gameLog = {}
    url = f"https://api-web.nhle.com/v1/player/{playerID}/game-log/now"
    response = requests.get(url)

    if response.status_code == 200:
        gameLog = response.json()
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
    
    return gameLog

#-------- Get Current Skater Stats Leaders ---------------
#   Retrieve current skater stats leaders.
#   get_Current_Skater_Stats_Leaders('goals', 5)
#   categories - Optional
#   limit - Optional
#-------------------------------------------------

def get_Current_Skater_Stats_Leaders(categories = '', limit = -1):
    statsLeaders = {}
    url = ''

    if categories != '' and limit != -1:
        url = f"https://api-web.nhle.com/v1/skater-stats-leaders/current?categories={categories}&limit={limit}"
    elif categories == '' and limit != -1:
        url = f"https://api-web.nhle.com/v1/skater-stats-leaders/current?limit={limit}"
    elif categories != '' and limit == -1:
        url = f"https://api-web.nhle.com/v1/skater-stats-leaders/current?categories={categories}"
    else:
        url = f"https://api-web.nhle.com/v1/skater-stats-leaders/current"
        
    response = requests.get(url)

    if response.status_code == 200:
        statsLeaders = response.json()
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
    
    return statsLeaders

#-------- Get Skater Stats Leaders for a Specific Season and Game Type ---------------
#   Retrieve skater stats leaders for a specific season and game type.
#   get_Specific_Staker_Stats_Leaders('goals', 5)
#   categories - Optional
#   limit - Optional
#-------------------------------------------------

def get_Specific_Staker_Stats_Leaders(season, gameType, categories = '', limit = -1):
    statsLeaders = {}
    url = ''

    if categories != '' and limit != -1:
        url = f"https://api-web.nhle.com/v1/skater-stats-leaders/{season}/{gameType}?categories={categories}&limit={limit}"
    elif categories == '' and limit != -1:
        url = f"https://api-web.nhle.com/v1/skater-stats-leaders/{season}/{gameType}?limit={limit}"
    elif categories != '' and limit == -1:
        url = f"https://api-web.nhle.com/v1/skater-stats-leaders/{season}/{gameType}?categories={categories}"
    else:
        url = f"https://api-web.nhle.com/v1/skater-stats-leaders/{season}/{gameType}"
        
    response = requests.get(url)

    if response.status_code == 200:
        statsLeaders = response.json()
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
    
    return statsLeaders

#-------- Get Current Goalie Stats Leaders ---------------
#   Retrieve current goalie stats leaders.
#   get_Current_Goalie_Stats_Leaders('wins', 5)
#   categories - Optional
#   limit - Optional
#-------------------------------------------------

def get_Current_Goalie_Stats_Leaders(categories = '', limit = -1):
    statsLeaders = {}
    url = ''

    if categories != '' and limit != -1:
        url = f"https://api-web.nhle.com/v1/goalie-stats-leaders/current?categories={categories}&limit={limit}"
    elif categories == '' and limit != -1:
        url = f"https://api-web.nhle.com/v1/goalie-stats-leaders/current?limit={limit}"
    elif categories != '' and limit == -1:
        url = f"https://api-web.nhle.com/v1/goalie-stats-leaders/current?categories={categories}"
    else:
        url = f"https://api-web.nhle.com/v1/goalie-stats-leaders/current"
        
    response = requests.get(url)

    if response.status_code == 200:
        statsLeaders = response.json()
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
    
    return statsLeaders

#-------- Get Goalie Stats Leaders by Season ---------------
#   Retrieve current goalie stats leaders.
#   get_Season_Goalie_Stats_Leaders(20232024, 2, 'wins', 3)
#   categories - Optional
#   limit - Optional
#-------------------------------------------------

def get_Season_Goalie_Stats_Leaders(season, gameType, categories = '', limit = -1):
    statsLeaders = {}
    url = ''

    if categories != '' and limit != -1:
        url = f"https://api-web.nhle.com/v1/goalie-stats-leaders/{season}/{gameType}?categories={categories}&limit={limit}"
    elif categories == '' and limit != -1:
        url = f"https://api-web.nhle.com/v1/goalie-stats-leaders/{season}/{gameType}?limit={limit}"
    elif categories != '' and limit == -1:
        url = f"https://api-web.nhle.com/v1/goalie-stats-leaders/{season}/{gameType}?categories={categories}"
    else:
        url = f"https://api-web.nhle.com/v1/goalie-stats-leaders/{season}/{gameType}"
        
    response = requests.get(url)

    if response.status_code == 200:
        statsLeaders = response.json()
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
    
    return statsLeaders

#-------- Get Players ---------------
#   Retrieve information about players in the "spotlight".
#   get_Spotlight_Players()
#-------------------------------------------------

def get_Spotlight_Players():
    players = {}
    url = f"https://api-web.nhle.com/v1/player-spotlight"
        
    response = requests.get(url)

    if response.status_code == 200:
        players = response.json()
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
    
    return players

#################################
#
#   Team Information API
#
#################################

#-------- Get Standings ---------------
#   Retrieve the standings as of the current moment.
#   get_Standings()
#-------------------------------------------------

def get_Standings():
    standings = {}
    url = f"https://api-web.nhle.com/v1/standings/now"
        
    response = requests.get(url)

    if response.status_code == 200:
        standings = response.json()
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
    
    return standings

#-------- Get Standings by Date ---------------
#   Retrieve the standings for a specific date.
#   get_Standings_By_Date('2023-11-10')
#-------------------------------------------------

def get_Standings_By_Date(date):
    standings = {}
    url = f"https://api-web.nhle.com/v1/standings/{date}"
        
    response = requests.get(url)

    if response.status_code == 200:
        standings = response.json()
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
    
    return standings

#-------- Get Standings information for each Season ---------------
#   Retrieves information for each season's standings
#   get_Season_Standings()
#-------------------------------------------------

def get_Season_Standings():
    standings = {}
    url = f"https://api-web.nhle.com/v1/standings-season"
        
    response = requests.get(url)

    if response.status_code == 200:
        standings = response.json()
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
    
    return standings

#-------- Get Club Stats Now ---------------
#   Retrieve current statistics for a specific club.
#   get_Club_Stats('TOR')
#-------------------------------------------------

def get_Club_Stats(team):
    stats = {}
    url = f"https://api-web.nhle.com/v1/club-stats/{team}/now"
        
    response = requests.get(url)

    if response.status_code == 200:
        stats = response.json()
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
    
    return stats

#-------- Get Club Stats by Season and Game Type ---------------
#   Retrieve the stats for a specific team, season, and game type.
#   get_Specific_Club_Stats('TOR', 20232024, 2)
#-------------------------------------------------

def get_Specific_Club_Stats(team, season, gameType):
    stats = {}
    url = f"https://api-web.nhle.com/v1/club-stats/{team}/{season}/{gameType}"
        
    response = requests.get(url)

    if response.status_code == 200:
        stats = response.json()
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
    
    return stats

#-------- Get Team Scoreboard ---------------
#   Retrieve the scoreboard for a specific team as of the current moment.
#   get_Team_Scoreboard('TOR')
#-------------------------------------------------

def get_Team_Scoreboard(team):
    scoreboard = {}
    url = f"https://api-web.nhle.com/v1/scoreboard/{team}/now"
        
    response = requests.get(url)

    if response.status_code == 200:
        scoreboard = response.json()
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
    
    return scoreboard

#-------- Get Team Roster As of Now ---------------
#   Retrieve the roster for a specific team as of the current moment.
#   get_Team_Roster('TOR')
#-------------------------------------------------

def get_Team_Roster(team):
    roster = {}
    url = f"https://api-web.nhle.com/v1/roster/{team}/current"
        
    response = requests.get(url)

    if response.status_code == 200:
        roster = response.json()
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
    
    return roster

#-------- Get Team Roster by Season---------------
#   Retrieve the roster for a specific team and season.
#   get_Team_Roster_By_Season('TOR', '20232024')
#-------------------------------------------------

def get_Team_Roster_By_Season(team, season):
    roster = {}
    url = f"https://api-web.nhle.com/v1/roster/{team}/{season}"
        
    response = requests.get(url)

    if response.status_code == 200:
        roster = response.json()
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
    
    return roster

#-------- Get Roster Season for Team---------------
#   Seems to just return a list of all of the seasons that the team played.
#   get_Roster_Season('TOR')
#-------------------------------------------------

def get_Roster_Season(team):
    season = []
    url = f"https://api-web.nhle.com/v1/roster-season/{team}"
        
    response = requests.get(url)

    if response.status_code == 200:
        season = response.json()
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
    
    return season

#-------- Get Team Prospects---------------
#   Retrieve prospects for a specific team.
#   get_Team_Prospects('TOR')
#-------------------------------------------------

def get_Team_Prospects(team):
    prospects = {}
    url = f"https://api-web.nhle.com/v1/prospects/{team}"
        
    response = requests.get(url)

    if response.status_code == 200:
        prospects = response.json()
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
    
    return prospects

#-------- Get Team Season Schedule As of Now---------------
#   Retrieve the season schedule for a specific team as of the current moment.
#   get_Team_Schedule('TOR')
#-------------------------------------------------

def get_Team_Schedule(team):
    schedule = {}
    url = f"https://api-web.nhle.com/v1/club-schedule-season/{team}/now"
        
    response = requests.get(url)

    if response.status_code == 200:
        schedule = response.json()
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
    
    return schedule

#-------- Get Team Season Schedule---------------
#   Retrieve the season schedule for a specific team and season.
#   get_Team_Season_Schedule('TOR', 20232024)
#-------------------------------------------------

def get_Team_Season_Schedule(team, season):
    schedule = {}
    url = f"https://api-web.nhle.com/v1/club-schedule-season/{team}/{season}"
        
    response = requests.get(url)

    if response.status_code == 200:
        schedule = response.json()
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
    
    return schedule

#-------- Get Month Schedule As of Now---------------
#   Retrieve the monthly schedule for a specific team as of the current moment.
#   get_Team_Month_Schedule_Now('TOR')
#-------------------------------------------------

def get_Team_Month_Schedule_Now(team):
    schedule = {}
    url = f"https://api-web.nhle.com/v1/club-schedule/{team}/month/now"
        
    response = requests.get(url)

    if response.status_code == 200:
        schedule = response.json()
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
    
    return schedule

#-------- Get Month Schedule As of Now---------------
#   Retrieve the monthly schedule for a specific team as of the current moment.
#   get_Team_Month_Schedule('TOR', '2023-11')
#-------------------------------------------------

def get_Team_Month_Schedule(team, month):
    schedule = {}
    url = f"https://api-web.nhle.com/v1/club-schedule/{team}/month/{month}"
        
    response = requests.get(url)

    if response.status_code == 200:
        schedule = response.json()
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
    
    return schedule

#-------- Get Week Schedule---------------
#   Retrieve the weekly schedule for a specific team and date.
#   get_Team_Week_Schedule('TOR', '2023-11-10')
#-------------------------------------------------

def get_Team_Week_Schedule(team, date):
    schedule = {}
    url = f"https://api-web.nhle.com/v1/club-schedule/{team}/week/{date}"
        
    response = requests.get(url)

    if response.status_code == 200:
        schedule = response.json()
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
    
    return schedule

#-------- Get Week Schedule As of Now---------------
#   Retrieve the weekly schedule for a specific team as of the current moment.
#   get_Team_Week_Schedule_Now('TOR')
#-------------------------------------------------

def get_Team_Week_Schedule_Now(team):
    schedule = {}
    url = f"https://api-web.nhle.com/v1/club-schedule/{team}/week/now"
        
    response = requests.get(url)

    if response.status_code == 200:
        schedule = response.json()
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
    
    return schedule


#################################
#
#   League Schedule Information API
#
#################################

#-------- Get Current Schedule---------------
#   Retrieve the current schedule.
#   get_Current_Schedule()
#-------------------------------------------------

def get_Current_Schedule():
    schedule = {}
    url = f"https://api-web.nhle.com/v1/schedule/now"
        
    response = requests.get(url)

    if response.status_code == 200:
        schedule = response.json()
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
    
    return schedule

#-------- Get Schedule by Date---------------
#   Retrieve the schedule for a specific date.
#   get_Schedule_By_Date('2023-11-10')
#-------------------------------------------------

def get_Schedule_By_Date(date):
    schedule = {}
    url = f"https://api-web.nhle.com/v1/schedule/{date}"
        
    response = requests.get(url)

    if response.status_code == 200:
        schedule = response.json()
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
    
    return schedule

#-------- Get Schedule Calendar As of Now---------------
#   Retrieve the schedule calendar as of the current moment.
#   get_Schedule_Calender_Now()
#-------------------------------------------------

def get_Schedule_Calender_Now():
    calender = {}
    url = f"https://api-web.nhle.com/v1/schedule-calendar/now"
        
    response = requests.get(url)

    if response.status_code == 200:
        schedule = response.json()
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
    
    return schedule

#-------- Get Schedule Calendar for a Specific Date---------------
#   Retrieve the schedule calendar for a specific date.
#   get_Schedule_Calender_By_Date('2023-11-10')
#-------------------------------------------------

def get_Schedule_Calender_By_Date(date):
    calender = {}
    url = f"https://api-web.nhle.com/v1/schedule-calendar/{date}"
        
    response = requests.get(url)

    if response.status_code == 200:
        schedule = response.json()
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
    
    return schedule

#################################
#
#   Game Information API
#
#################################

#-------- Get Daily Scores As of Now---------------
#   Retrieve daily scores as of the current moment.
#   get_Daily_Scores_Now()
#-------------------------------------------------

def get_Daily_Scores_Now():
    scores = {}
    url = f"https://api-web.nhle.com/v1/score/now"
        
    response = requests.get(url)

    if response.status_code == 200:
        scores = response.json()
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
    
    return scores

#-------- Get Daily Scores by Date---------------
#   Retrieve daily scores for a specific date.
#   get_Daily_Scores_By_Date('2023-11-10')
#-------------------------------------------------

def get_Daily_Scores_By_Date(date):
    scores = {}
    url = f"https://api-web.nhle.com/v1/score/{date}"
        
    response = requests.get(url)

    if response.status_code == 200:
        scores = response.json()
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
    
    return scores

#-------- Get Scoreboard---------------
#   Retrieve the overall scoreboard as of the current moment.
#   get_Scoreboard()
#-------------------------------------------------

def get_Scoreboard():
    scoreboard = {}
    url = f"https://api-web.nhle.com/v1/scoreboard/now"
        
    response = requests.get(url)

    if response.status_code == 200:
        scoreboard = response.json()
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
    
    return scoreboard

#-------- Where to Watch---------------
#   Retrieve information about streaming options.
#   get_Streaming()
#-------------------------------------------------

def get_Streaming():
    streaming = {}
    url = f"https://api-web.nhle.com/v1/where-to-watch"
        
    response = requests.get(url)

    if response.status_code == 200:
        streaming = response.json()
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
    
    return streaming

#-------- Get Play By Play---------------
#   Retrieve play-by-play information for a specific game.
#   get_P2P_Info(2023020204)
#-------------------------------------------------

def get_P2P_Info(gameID):
    information = {}
    url = f"https://api-web.nhle.com/v1/gamecenter/{gameID}/play-by-play"
        
    response = requests.get(url)

    if response.status_code == 200:
        information = response.json()
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
    
    return information

#-------- Get Landing---------------
#   Retrieve landing information for a specific game.
#   get_Landing(2023020204)
#-------------------------------------------------

def get_Landing(gameID):
    landing = {}
    url = f"https://api-web.nhle.com/v1/gamecenter/{gameID}/landing"
        
    response = requests.get(url)

    if response.status_code == 200:
        landing = response.json()
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
    
    return landing

#-------- Get Boxscore---------------
#   Retrieve boxscore information for a specific game.
#   get_Boxscore(2023020204)
#-------------------------------------------------

def get_Boxscore(gameID):
    boxscore = {}
    url = f"https://api-web.nhle.com/v1/gamecenter/{gameID}/boxscore"
        
    response = requests.get(url)

    if response.status_code == 200:
        boxscore = response.json()
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
    
    return boxscore

#-------- Get Game Story---------------
#   Retrieve game story information for a specific game.
#   get_Game_Story(2023020204)
#-------------------------------------------------

def get_Game_Story(gameID):
    story = {}
    url = f"https://api-web.nhle.com/v1/wsc/game-story/{gameID}"
        
    response = requests.get(url)

    if response.status_code == 200:
        story = response.json()
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
    
    return story

#-------- Get Seasons ---------------
#   Retrieve a list of all season IDs past & present in the NHL.
#   get_Season()
#-------------------------------------------------

def get_Season():
    season = []
    url = f"https://api-web.nhle.com/v1/season"
        
    response = requests.get(url)

    if response.status_code == 200:
        season = response.json()
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
    
    return season

#-------- Get Game Information ---------------
#   Retrieve information for a specific game.
#   get_Season()
#-------------------------------------------------

def get_Game_Info(gameID):
    gameInfo = {}
    url = f"https://api-web.nhle.com/v1/meta/game/{gameID}"
        
    response = requests.get(url)

    if response.status_code == 200:
        gameInfo = response.json()
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
    
    return gameInfo


#-------- Get Team Information ---------------
#   Retrieve list of all teams.
#   get_Teams()
#-------------------------------------------------
def get_Teams():
    teams = {}
    url = 'https://api.nhle.com/stats/rest/en/team'
    response = requests.get(url)

    if response.status_code == 200:
        teams = response.json()
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
    
    return teams


