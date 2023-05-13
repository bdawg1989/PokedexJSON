import requests
from bs4 import BeautifulSoup
import json
import re
import unidecode

# Function to replace non-alphabetic characters
def clean_item_name(item_name):
    return unidecode.unidecode(item_name.strip())  # Add .strip() to remove newline and extra spaces


# Function to extract items from the wiki page
def extract_items(url, generation):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    tables = soup.find_all("table", lambda value: value and "sortable" in value and "roundy" in value)

    target_table = None
    for table in tables:
        header_row = table.find("tr")
        if header_row and (len(header_row.find_all("th")) == 4 or len(header_row.find_all("th")) == 5):
            target_table = table
            break

    if target_table is None:
        print(f"Table not found for {generation}")
        return {}

    items = {}
    rows = target_table.find_all("tr")

    for row in rows[1:]: 
        cols = row.find_all("td")
        item_image = cols[2].find("img")["src"]
        item_name = clean_item_name(cols[3].text)

        if item_name in all_items: 

            if generation not in all_items[item_name]["Generation"]:
                all_items[item_name]["Generation"].append(generation)
        else:
            items[item_name] = {
                "Image": item_image,
                "Generation": [generation]
            }
    return items


# Extract items from the specified URLs
urls = [
    {
        "url": "https://bulbapedia.bulbagarden.net/wiki/List_of_items_by_index_number_(Generation_IX)",
        "generation": "Gen9"
    },
    {
        "url": "https://bulbapedia.bulbagarden.net/wiki/List_of_items_by_index_number_(Generation_VIII)",
        "generation": "Gen8"
    },
    {
        "url": "https://bulbapedia.bulbagarden.net/wiki/List_of_items_by_index_number_(Generation_VII)",
        "generation": "Gen7"
    },   
    {
        "url": "https://bulbapedia.bulbagarden.net/wiki/List_of_items_by_index_number_(Generation_VI)",
        "generation": "Gen6"
    },
    {
        "url": "https://bulbapedia.bulbagarden.net/wiki/List_of_items_by_index_number_(Generation_V)",
        "generation": "Gen5"
    },    
    {
        "url": "https://bulbapedia.bulbagarden.net/wiki/List_of_items_by_index_number_(Generation_IV)",
        "generation": "Gen4"
    }, 
    {
        "url": "https://bulbapedia.bulbagarden.net/wiki/List_of_items_by_index_number_(Generation_III)",
        "generation": "Gen3"
    } 
]

all_items = {}
total_urls = len(urls)
for index, url_info in enumerate(urls, start=1):
    items = extract_items(url_info["url"], url_info["generation"])
    all_items.update(items)
    progress = (index / total_urls) * 100
    print(f"Processed {url_info['generation']} ({index}/{total_urls}): {progress:.2f}%")

# Save items to a JSON file
with open("items.json", "w") as file:
    json.dump(all_items, file, indent=4)
