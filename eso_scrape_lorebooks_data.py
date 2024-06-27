import requests
from bs4 import BeautifulSoup
import json

base_url = "https://esoitem.uesp.net/viewlog.php?"
details_base_url = "https://esoitem.uesp.net/viewlog.php?action=view&record=book&id="
uesp_books_url = "https://en.uesp.net/wiki/Online:Books#Collections"
booksDataIndexed = {}
bookIndices = {}

def print_counter(completed, total): print(f'\r{completed}/{total}', end='', flush=True)

def get_int(value: str) -> int:
    try:
        return int(value)
    except ValueError as err:
        print(f'Error, {value} isn\'t a number')
        print('args:', err.args)
        print(err)
        raise err

def fetch_game_id(book_link) -> bool:
    url = f"https://en.uesp.net{book_link}"
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        book_id_element = soup.find('table', class_="wikitable infobox"
                                    ).find_all('tr')[1].find('td')
        if book_id_element:
            game_id_str = book_id_element.text.strip()
            if ',' in game_id_str:
                game_id_str = game_id_str.split(',')[0]
                
            return get_int(game_id_str)

def extract_lorebook_ids(page_content):
    soup = BeautifulSoup(page_content, 'html.parser')
    table = soup.find('table')
    for row in table.find_all('tr')[1:]:
        cells = row.find_all('td')
        game_id = get_int(cells[12].text.strip())
        if 'Yes' in cells[5] and game_id != 0:
            bookData = {
                'uesp_id': get_int(cells[1].text.strip()),
                'title': cells[2].text.strip(),
                'categoryIndex': get_int(cells[8].text.strip()),
                'collectionIndex': get_int(cells[9].text.strip()),
                'bookIndex': get_int(cells[10].text.strip()),
                'game_id': game_id,
                'img' : cells[4].find('img')['src'],
                'author': '',
                'description': '',
                'subjects': '',
            }
            booksDataIndexed[game_id] = bookData
            bookIndices[game_id] = {
                'categoryIndex' : bookData['categoryIndex'],
                'collectionIndex' : bookData['collectionIndex'],
                'bookIndex' : bookData['bookIndex']
            }
def extract_lorebook_content(uesp_id):
    url = f"{details_base_url}{uesp_id}"
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        content_div = soup.find('div', class_='elvLargeStringView')
        if content_div:
            return content_div.text.strip()
    return None

def extract_collection_details(collection_url, titleIndex = 1, authorIndex = 2, descriptionIndex = 3):
    response = requests.get(collection_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        tables = soup.find_all('table', class_='wikitable sortable collapsible striped')
        for table in tables:
            rows = table.find_all('tr')[1:]  # Skip header row
            for row in rows:
                cells = row.find_all('td') 
                book_link = cells[titleIndex].find('a')['href']
                game_id = fetch_game_id(book_link)
                if game_id in booksDataIndexed:
                    booksDataIndexed[game_id]['author'] = cells[authorIndex].text.strip()
                    booksDataIndexed[game_id]['description'] = cells[descriptionIndex].text.strip()

def extract_books_metadata():
    print("Aquiring the descriptions and authors of books")
    response = requests.get(uesp_books_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        collections = soup.find_all('table', class_='hiddentable vtop')
        print("Categories to search:", len(collections))
        count = 1
        for collection in collections:
            titleIndex, authorIndex, descriptionIndex = 1, 2, 3
            if count == 1 or count  == 2:
                links = collection.find_all('a')
                category_name = 'Crafting Motifs'
            if count == 1:
                titleIndex, authorIndex, descriptionIndex = 0, 1, 2
                category_name = 'Eidetic Memory'
            if count == 3:
                links = [collection.find('a')]
                category_name = 'Shalidor\'s Library'           
            print(category_name)
            for link in links:
                if link:
                    collection_url = f"https://en.uesp.net{link['href']}"
                    print(collection_url)
                    extract_collection_details(collection_url, titleIndex, authorIndex, descriptionIndex)
            count += 1
    print()



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

print(f"Fetching content for: {len(booksDataIndexed)} books")
count = 0
# Fetch body content for each lorebook
for game_id in booksDataIndexed:
    book_content = extract_lorebook_content(booksDataIndexed[game_id]['uesp_id'])
    if book_content:
        booksDataIndexed[game_id]['content'] = book_content
    count += 1
    print_counter(count, len(booksDataIndexed))
print()
    
# Extract authors and descriptions from UESP wiki
extract_books_metadata()

count = 1
booksData = []
for bookIndex in booksDataIndexed:
    print_counter(count, len(booksDataIndexed))
    booksData.append(booksDataIndexed[bookIndex])
    count += 1

# Save records to a JSON file
with open('eso_books_data.json', 'w', encoding='utf-8') as jsonfile:
    json.dump(booksData, jsonfile, ensure_ascii=False, indent=4)
print("Scraping complete. Data saved to eso_books_data.json")

with open('eso_books_indices.json', 'w', encoding='utf-8') as jsonfile:
    json.dump(bookIndices, jsonfile, ensure_ascii=False, indent=4)
print("Scraping complete. Data saved to eso_books_indices.json")
