import requests
from bs4 import BeautifulSoup
import json

base_url = "https://esoitem.uesp.net/viewlog.php?"
records = []
examine_false = []


def get_int(value: str) -> int:
    try:
        return int(value)
    except ValueError as err:
        print(f'Error, ${value} isn\'t a number')
        print('args:', err.args)
        print(err)

def extract_data(page_content):
    soup = BeautifulSoup(page_content, 'html.parser')
    table = soup.find('table')
    for row in table.find_all('tr')[1:]:
        cells = row.find_all('td')
        if len(cells) <= 2:
            print(cells)
        if 'Yes' in cells[5]:
            record = {
                'categoryIndex': get_int(cells[8].text.strip()),
                'collectionIndex': get_int(cells[9].text.strip()),
                'bookIndex': get_int(cells[10].text.strip()),
                'bookID': get_int(cells[12].text.strip())
            }

            if (record['bookID'] != 0):
                records.append(record)

# Initial page
page_number = 0
print('Extracting Content From: ')
while True:
    url = f"{base_url}start={page_number * 1000}&record=book"
    
    response = requests.get(url)
    if response.status_code != 200:
        break
    
    page_content = response.content
    print(url)
    extract_data(page_content)
    
    soup = BeautifulSoup(page_content, 'html.parser')
    next_button = soup.find('a', string='Next')
    if not next_button:
        break
    page_number += 1


# Save records to a JSON file
with open('books.json', 'w', encoding='utf-8') as jsonfile:
    json.dump(records, jsonfile, ensure_ascii=False, indent=4)

print("Scraping complete. Data saved to books.json")
