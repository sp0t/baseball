from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

try:
    url = f"https://baseballsavant.mlb.com/gamefeed?date=6/21/2024&gamePk=744841&chartType=pitch&leg[%E2%80%A6]Filter=&resultFilter=&hf=winProbability&sportId=1&liveAb="
    print('###################################################')
    print('##                                               ')
    print(f'##   {url}                                      ')
    print('##                                               ')
    print('###################################################')
    driver.get(url)

    wait = WebDriverWait(driver, 15)
    wait.until(EC.presence_of_element_located((By.ID, 'tableWinProbability_744841')))
    # get_url = driver.current_url
    # wait.until(EC.url_to_be(url))

    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')
    table_data = soup.find('div', id='tableWinProbability_744841')
    tbody = table_data.find('tbody')

    if tbody:
        for tr in reversed(tbody.find_all('tr')):
            tds = tr.find_all('td')
            # for td in tds:
            linespan = tds[1].find('span')
            if linespan:
                awaywin = 0
                homewin = 0
                awayspan = tds[6].find('span')
                if awayspan:
                    awaywin = awayspan.get_text()
                else:
                    awaywin = awayspan.get_text()
                
                homespan = tds[5].find('span')

                if homespan:
                    homewin = homespan.get_text()
                else:
                    homewin = homespan.get_text()

                if(linespan.get_text() == 'B1'):
                    print('B1', homewin, '-', awaywin) 

                if(linespan.get_text() == 'B2'):
                    print('B2', homewin, '-', awaywin)

                if(linespan.get_text() == 'B3'):
                    print('B3', homewin, '-', awaywin)

                if(linespan.get_text() == 'B4'):
                    print('B4', homewin, '-', awaywin)
                if(linespan.get_text() == 'B5'):
                    print('B5', homewin, '-', awaywin)
                if(linespan.get_text() == 'B6'):
                    print('B6', homewin, '-', awaywin)
                if(linespan.get_text() == 'B7'):
                    print('B7', homewin, '-', awaywin)
                if(linespan.get_text() == 'B8'):
                    print('B8', homewin, '-', awaywin)
                if(linespan.get_text() == 'B9'):
                    print('B9', homewin, '-', awaywin)
            else:
                print("No span found in this td.")
    else:
        print("No tbody found in the HTML.")
    

except Exception as e:
    print(f"An error occurred: {e}")

finally:
    driver.close()