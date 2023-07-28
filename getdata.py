from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup 
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options 
from selenium.webdriver.common.by import By
from datetime import date, timedelta, datetime
import sqlite3
import csv
import time



def connect_to_database(db_name):
    try:
        connection = sqlite3.connect(db_name)
        print(f"Connected to the database: {db_name}")
        return connection
    except sqlite3.Error as e:
        print(f"Error connecting to the database: {e}")
        return None
    
def create_table(connection):
    try:
        # Create a cursor object to execute SQL commands
        cursor = connection.cursor()

        # Define the SQL command to create the "odd" table
        event_query = """
        CREATE TABLE IF NOT EXISTS event (
            eventname TEXT,
            eventdate TEXT,
            venue TEXT,
            city TEXT,
            link TEXT
        )
        """
        fight_query = """
        CREATE TABLE IF NOT EXISTS fighter1 (
            fighter1 TEXT,
            betonline_f1 TEXT,
            pinnacle_f1 TEXT,
            fighter2 TEXT,
            betonline_f2 TEXT,
            pinnacle_f2 TEXT,
            link TEXT
        )
        """
        # Execute the SQL command
        cursor.execute(event_query)
        cursor.execute(fight_query)
        connection.commit()
        print("Table OK.")
    except sqlite3.Error as e:
        print(f"Error table: {e}")

def insert_event(connection, event_data):
    try:
        cursor = connection.cursor()

        # Define the SQL command to insert or update data into the "event" table
        insert_or_replace_query = """
        INSERT INTO event (eventname, eventdate, venue, city, link)
        VALUES (:eventname, :eventdate, :venue, :city, :link)
        """

        # Execute the SQL command with the provided event_data dictionary
        cursor.execute(insert_or_replace_query, event_data)
        connection.commit()
        print("eventdata insert successfully.")
    except sqlite3.Error as e:
        print(f"Error inserting event data: {e}")

def insert_fighter(connection, fighter_data):
    try:
        cursor = connection.cursor()

        # Define the SQL command to insert or update data into the "event" table
        insert_or_replace_query = """
        INSERT INTO fighter (fighter1, betonline_f1, pinnacle_f1, fighter2, betonline_f2, pinnacle_f2, link)
        VALUES (:fighter1, :betonline_f1, :pinnacle_f1, :fighter2, :betonline_f2, :pinnacle_f2, :link)
        """
        # Execute the SQL command with the provided event_data dictionary
        cursor.execute(insert_or_replace_query, fighter_data)
        connection.commit()
        print("fighterdata insert successfully.")
    except sqlite3.Error as e:
        print(f"Error inserting fighter data: {e}")

def extract_data(connection):
    try:
        cursor = connection.cursor()

        # Define the SQL command to extract data from all three tables using INNER JOIN
        extract_data_query = """
        SELECT event.eventname, event.eventdate, event.venue, event.city,
               fighter1.fighter AS fighter1, fighter1.betonline AS fighter1_betonline, fighter1.pinnacle AS fighter1_pinnacle,
               fighter2.fighter AS fighter2, fighter2.betonline AS fighter2_betonline, fighter2.pinnacle AS fighter2_pinnacle, event.link
        FROM event
        INNER JOIN fighter1 ON event.link = fighter1.link
        """
        # extract_data_query = """
        # SELECT * FROM event
        # """

        # Execute the SQL command with the provided link as a parameter
        cursor.execute(extract_data_query)
        result = cursor.fetchall()
        print(result)
        return result
    except sqlite3.Error as e:
        print(f"Error extracting data: {e}")
        return None
    
def save_to_csv(data, csv_filename):
    try:
        with open(csv_filename, 'w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            # Write header row
            header = ["Event Name", "Event Date", "Venue", "City", "Fighter 1", "Fighter 1 BetOnline", "Fighter 1 Pinnacle", "Fighter 2", "Fighter 2 BetOnline", "Fighter 2 Pinnacle", "Link"]
            csv_writer.writerow(header)

            # Write data rows
            for row in data:
                csv_writer.writerow(row)
        print(f"Data saved to '{csv_filename}' successfully.")
    except Exception as e:
        print(f"Error saving data to CSV: {e}")
#database and table create
db_connection = connect_to_database('mma_odds.db')
create_table(db_connection)
# data = extract_data(db_connection)
# save_to_csv(data, 'data.csv')

#run webdriver
options = Options()
options.use_chromium = True
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

driver_path = ChromeDriverManager().install()
driver = webdriver.Chrome(service=Service(driver_path), options=options)

driver.get("https://fightodds.io/recent-mma-events")

print(date.today())
# Wait for the sports list to load
time.sleep(3)
event_datas = []

try:
    target_date = True
    while target_date :
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, "html.parser")
        game_elements = soup.findAll('div', attrs={"class":"MuiGrid-root MuiGrid-item MuiGrid-grid-xs-9"})
        for game_element in game_elements:
            head_element = game_element.find('a', attrs={"class":"MuiTypography-root MuiLink-root MuiLink-underlineNone MuiTypography-colorPrimary"})
            body_element = game_element.find_all('div', recursive=False)
            date_element = body_element[1].findAll('div')[0]
            venue_element = body_element[1].findAll('div')[1]
            city_element = body_element[1].findAll('div')[2]
            odds_url ='https://fightodds.io' + head_element.get('href') + '/odds'

            if head_element.text == 'UFC Fight Night: Holm vs. Bueno Silva' and date_element.text == 'July 15, 2023':
                print('=================================================')
                target_date = False
                break

            event_data = {
                "eventname": head_element.text,
                "eventdate": date_element.text,
                "venue": venue_element.text,
                "city": city_element.text,
                "link": odds_url
            }

            if event_data not in event_datas:
                # insert_event(db_connection, event_data)
                event_datas.append(event_data)
            # if head_element.text == 'Invicta FC 45: Zappitella vs. Delboni 2' and date_element.text == 'January 12, 2022':
            #     target_date = False
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        driver.implicitly_wait(2)

    driver.quit()

    for event_data in event_datas:
        betonline = ''
        pinnacle = ''
        print(event_data)

        odd_driver = webdriver.Chrome(service=Service(driver_path), options=options)
        odd_driver.get(odds_url)
        odd_driver.maximize_window()
        time.sleep(10)
        
        table_source = odd_driver.page_source
        table_soup = BeautifulSoup(table_source, "html.parser")
        try:
            table_element = table_soup.find('table')
            tbody_element = table_element.find(attrs={"class": "MuiTableBody-root"})
            fighters_element = tbody_element.find_all('tr')
            row = 0
            fighter_data = {}
            for fighter_element in fighters_element:
                td_elements = fighter_element.find('td')
                name_element = fighter_element.find('a', attrs={"class":"MuiTypography-root MuiLink-root MuiLink-underlineHover MuiTypography-colorPrimary"})
                # odds_element = td_elements[1].find('span', attrs={"class":"MuiButton-label"})
                for td_element in td_elements:
                    print(td_element.prettify())
                # try:
                #     betonline_element = odds_element.find('div').find('div').find('span')
                #     betonline = betonline_element.text
                # except:
                #     betonline = ''
                # try:
                #     pinnacle_element = odds_element.find('div').find('div').find('span')
                #     pinnacle = pinnacle_element.text
                # except:
                #     pinnacle = ''
                
                # if row % 2 == 0:
                #     fighter_data.fighter1 = name_element.text
                #     fighter_data.betonline_f1 = betonline
                #     fighter_data.pinnacle_f1 = pinnacle
                
                # if row % 2 == 1:
                #     fighter_data.fighter2 = name_element.text
                #     fighter_data.betonline_f2 = betonline
                #     fighter_data.pinnacle_f2 = pinnacle
                #     fighter_data.link = odds_url
                #     print(fighter_data)
                #     # insert_fighter(db_connection, fighter_data)
                #     fighter_data = {}
                # row = row + 1

            odds_url = ''
        except:
            print('No ODDs')
        odd_driver.quit()
except:
    print("Element not found on the page.")
# driver.quit()
db_connection.close()