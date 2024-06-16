import requests
from bs4 import BeautifulSoup
import json

base_url = "https://esoitem.uesp.net/viewlog.php?"
details_base_url = "https://esoitem.uesp.net/viewlog.php?action=view&record=book&id="
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
        if 'Yes' in cells[5] and '0' == cells[12].text.strip():
            book_id = cells[1].text.strip()
            lorebook_id = get_int(book_id)
            if lorebook_id:
                record = {
                    'categoryIndex': get_int(cells[8].text.strip()),
                    'collectionIndex': get_int(cells[9].text.strip()),
                    'bookIndex': get_int(cells[10].text.strip()),
                    'bookID': lorebook_id
                }
                records.append(record)

def extract_lorebook_content(book_id):
    url = f"{details_base_url}{book_id}"
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        content_div = soup.find('div', class_='elvLargeStringView')  # Adjust if the actual content div has a different class or id
        if content_div:
            return content_div.text.strip()
    return None

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

# Fetch body content for each lorebook
for record in records:
    book_content = extract_lorebook_content(record['bookID'])
    print(book_content)
    if book_content:
        record['content'] = book_content

# Save records to a JSON file
with open('lorebooks.json', 'w', encoding='utf-8') as jsonfile:
    json.dump(records, jsonfile, ensure_ascii=False, indent=4)

print("Scraping complete. Data saved to books.json")
