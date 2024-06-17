import requests
from bs4 import BeautifulSoup
import json

base_url = "https://esoitem.uesp.net/viewlog.php?"
details_base_url = "https://esoitem.uesp.net/viewlog.php?action=view&record=book&id="
uesp_books_url = "https://en.uesp.net/wiki/Online:Books#Collections"
records = []

def get_int(value: str) -> int:
    try:
        return int(value)
    except ValueError as err:
        print(f'Error, {value} isn\'t a number')
        print('args:', err.args)
        print(err)
        return 0

def extract_lorebook_ids(page_content):
    soup = BeautifulSoup(page_content, 'html.parser')
    table = soup.find('table')
    for row in table.find_all('tr')[1:]:
        cells = row.find_all('td')
        game_id = get_int(cells[12].text.strip())
        if 'Yes' in cells[5] and game_id != 0:
            record = {
                'uesp_id': get_int(cells[1].text.strip()),
                'title': cells[2].text.strip(),
                'categoryIndex': get_int(cells[8].text.strip()),
                'collectionIndex': get_int(cells[9].text.strip()),
                'bookIndex': get_int(cells[10].text.strip()),
                'game_id': game_id,
                'author': '',
                'description': ''
            }
            records.append(record)

def extract_lorebook_content(uesp_id):
    url = f"{details_base_url}{uesp_id}"
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        content_div = soup.find('div', class_='elvLargeStringView')
        if content_div:
            return content_div.text.strip()
    return None

def extract_books_metadata():
    response = requests.get(uesp_books_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        collections = soup.find_all('table', class_='hiddentable vtop')
        for collection in collections:
            link = collection.find('a')
            if link:
                collection_url = f"https://en.uesp.net{link['href']}"
                extract_collection_details(collection_url)

def extract_collection_details(collection_url):
    response = requests.get(collection_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        tables = soup.find_all('table', class_='wikitable sortable collapsible striped')
        
        for table in tables:
            rows = table.find_all('tr')[1:]  # Skip header row
            for row in rows:
                cells = row.find_all('td')
                title = cells[1].text.strip()
                author = cells[2].text.strip()
                description = cells[3].text.strip() if len(cells) > 4 else ''
                
                print(f'{title} : {collection_url}')
                match = next((record for record in records if record['title'] == title), None)
                if match:
                    match['author'] = author
                    match['description'] = description

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
    extract_lorebook_ids(page_content)
    
    soup = BeautifulSoup(page_content, 'html.parser')
    next_button = soup.find('a', string='Next')
    if not next_button:
        break
    page_number += 1
    break

print(len(records))
count = 0
# Fetch body content for each lorebook
for record in records:
    book_content = extract_lorebook_content(record['uesp_id'])
    if book_content:
        record['content'] = book_content
    count += 1
    print(f'\r{count}/{len(records)}', end='', flush=True)
print()
    
# Extract authors and descriptions from UESP wiki
extract_books_metadata()

# Save records to a JSON file
with open('lorebooks.json', 'w', encoding='utf-8') as jsonfile:
    json.dump(records, jsonfile, ensure_ascii=False, indent=4)

print("Scraping complete. Data saved to lorebooks.json")
