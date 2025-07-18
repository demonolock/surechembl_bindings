import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

url = "https://www.surechembl.org/patent/EP-2810938-A1"

# Optional: run Chrome in headless mode (no GUI)
chrome_options = Options()
chrome_options.add_argument("--headless")

# Start the browser
driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
driver.get(url)
# Ничего надежнее не придумалось. Ожидание по xpath не сработало и ожидание прогрузки js тоже execute_script('return document.readyState') == 'complete
time.sleep(5)

html = driver.page_source
driver.quit()

soup = BeautifulSoup(html, "html.parser")

# 4 - Title
title = soup.find(class_='patent-title')
title_text = title.get_text(strip=True) if title else None

# 3 - Abstract
abstract_section = None
for el in soup.find_all(class_=lambda c: c and 'abstract' in c):
    sec = el.find(class_='section')
    if sec:
        abstract_section = sec.get_text(strip=True)
        break

# 2 - Claims
claims_section = None
for el in soup.find_all(class_=lambda c: c and 'claims' in c):
    sec = el.find(class_='section')
    if sec:
        claims_section = sec.get_text(strip=True)
        break

# 1 - Description
description_section = None
for el in soup.find_all(class_=lambda c: c and 'description' in c):
    sec = el.find(class_='section')
    if sec:
        description_section = sec.get_text(strip=True)
        break

# 5,6 - Images/attachments
images = []
for vwin in soup.find_all(class_=lambda c: c and 'v-window ' in c):
    for img in vwin.find_all('img', src=True):
        images.append(img['src'])


print("=========Title=========")
print(title_text)
print("=========Abstract=========")
print(abstract_section)
print("=========Claims=========")
print(claims_section)
print("=========Description last 500=========")
print(description_section[-500:-1] if description_section else None)
print("=========Images=========")
print(images)
