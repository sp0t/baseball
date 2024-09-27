import requests
from bs4 import BeautifulSoup
import time
import re

def scrape(game_nhl_id, season_nhl_id, away_team_abbreviation, home_team_abbreviation):
    game_url_string = str(game_nhl_id)[-5:]
    url = f"https://www.naturalstattrick.com/game.php?season={season_nhl_id}&game={game_url_string}&view=limited"
    print(f"Fetching {url}")
    
    headers = {
        'User-Agent': "Googlebot/2.1 (+http://www.google.com/bot.html)"
    }

    # Fetch the page with retries
    retries_left = 10
    while retries_left > 0:
        response = requests.get(url, headers=headers)
        if response.ok:
            break
        else:
            print(f"Response not ok, retrying. Retries left: {retries_left}")
            retries_left -= 1
            time.sleep(1)
    else:
        raise Exception(f"Couldn't scrape data from {url}")

    data = response.text
    print("Mapping scraped data")

    team_abbreviation_mappings = {
        'NJD': 'NJ',
        'SJS': 'SJ',
        'TBL': 'TB',
        'LAK': 'LA',
    }

    def map_team_abbreviation(abbreviation):
        return team_abbreviation_mappings.get(abbreviation, abbreviation)

    away_team_mapped_abbreviation = map_team_abbreviation(away_team_abbreviation)
    home_team_mapped_abbreviation = map_team_abbreviation(home_team_abbreviation)

    soup = BeautifulSoup(data, 'html.parser')

    nodes = soup.select('.tall table')
    available_abbreviations = [
        node.get('id') for node in nodes if node.get('id') and node.get('id').endswith('shall')
    ]

    available_abbreviations = [re.sub(r'[^A-Z]+', '', id_) for id_ in available_abbreviations]

    if not available_abbreviations:
        raise Exception("Game is missing stats")

    if away_team_mapped_abbreviation not in available_abbreviations or home_team_mapped_abbreviation not in available_abbreviations:
        raise Exception("Scraped team abbreviations do not include expected ones")

    # Select player data for skaters and goalies
    away_skaters = soup.select(f'.tall #tb{away_team_mapped_abbreviation}oiall tbody tr')
    away_goalies = soup.select(f'.tall #tb{away_team_mapped_abbreviation}stgall tbody tr')
    
    home_skaters = soup.select(f'.tall #tb{home_team_mapped_abbreviation}oiall tbody tr')
    home_goalies = soup.select(f'.tall #tb{home_team_mapped_abbreviation}stgall tbody tr')

    # Helper functions to clean and parse text
    def clean_string(s):
        return s.strip()

    def try_parse_number(s):
        try:
            return float(s) if '.' in s else int(s)
        except ValueError:
            return s

    def player_has_fenwick(player_stats):
        return player_stats['fenwick_for_percent'] != '-' and player_stats['fenwick_for_percent_relative'] != '-'

    def goalie_has_save_percentage(player_stats):
        return player_stats['save_percentage'] != '-'

    # Map skater data
    def map_skaters(players):
        result = []
        for tr in players:
            td_texts = [clean_string(td.get_text().replace('\xa0', ' ')) for td in tr.find_all('td') if td.get_text() != '\n']
            player_stats = {
                'name': td_texts[0],
                'position': td_texts[1],
                'corsi_for': try_parse_number(td_texts[3]),
                'corsi_against': try_parse_number(td_texts[4]),
                'fenwick_for_percent': try_parse_number(td_texts[9]),
                'fenwick_for_percent_relative': try_parse_number(td_texts[10])
            }
            if player_has_fenwick(player_stats):
                result.append(player_stats)
        return result

    # Map goalie data
    def map_goalies(goalies):
        result = []
        for tr in goalies:
            td_texts = [clean_string(td.get_text().replace('\xa0', ' ')) for td in tr.find_all('td') if td.get_text() != '\n']

            player_stats = {
                'name': td_texts[0],
                'position': 'G',
                'goals_against': try_parse_number(td_texts[4]),
                'save_percentage': try_parse_number(td_texts[6])
            }
            if goalie_has_save_percentage(player_stats):
                result.append(player_stats)
        return result

    result = {
        'awayTeam': {
            'skaters': [],
            'goalies': []
        },
        'homeTeam': {
            'skaters': [],
            'goalies': []
        }
    }

    # Map away team skaters and goalies
    try:
        result['awayTeam']['skaters'] = map_skaters(away_skaters)
        if not result['awayTeam']['skaters']:
            raise Exception("Couldn't find any skaters for away team")
    except Exception as e:
        print(f"Failed to map away team skaters: {str(e)}")
        raise

    try:
        result['awayTeam']['goalies'] = map_goalies(away_goalies)
        if not result['awayTeam']['goalies']:
            raise Exception("Couldn't find any goalies for away team")
    except Exception as e:
        print(f"Failed to map away team goalies: {str(e)}")
        raise

    # Map home team skaters and goalies
    try:
        result['homeTeam']['skaters'] = map_skaters(home_skaters)
        if not result['homeTeam']['skaters']:
            raise Exception("Couldn't find any skaters for home team")
    except Exception as e:
        print(f"Failed to map home team skaters: {str(e)}")
        raise

    try:
        result['homeTeam']['goalies'] = map_goalies(home_goalies)
        if not result['homeTeam']['goalies']:
            raise Exception("Couldn't find any goalies for home team")
    except Exception as e:
        print(f"Failed to map home team goalies: {str(e)}")
        raise

    return result


# scrapedNstData = scrape('2024010004', '20242025', 'NSH', 'FLA')
