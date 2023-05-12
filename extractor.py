import requests
from bs4 import BeautifulSoup
import json
import re

####################
##  Sanitize Name ##
####################
def sanitize_name(name):
    name = name.replace(" ", "-").replace(".", "").replace(":", "").replace("♀", "-f").replace("♂", "-m")
    name = name.replace("é", "e")
    name = re.sub(r"[^a-zA-Z0-9\-]", "", name) 
    return name.lower()



####################
## GET MOVES FROM TABLE ##
####################
def get_moves_from_table(moves_table, level_key=None):
    move_rows = moves_table.find_all("tr")[1:]

    moves = []
    for row in move_rows:
        cells = row.find_all("td")
        level = int(cells[level_key].text) if level_key is not None else None
        move_link = cells[1].find("a", class_="ent-name")
        if not move_link:
            continue
        move = move_link.text
        move_type = cells[2].find("a", class_="type-icon").text
        power = cells[4].text
        accuracy = cells[5].text

        move_data = {
            "level": level,
            "move": move,
            "type": move_type,
            "power": int(power) if power.isdigit() else None,
            "accuracy": int(accuracy) if accuracy.isdigit() else None
        }
        moves.append(move_data)

    return moves


####################
##   GET MOVES    ##
####################
def get_moves(soup):
    level_up_table = soup.find_all("table", class_="data-table")[0]
    tm_table = soup.find_all("table", class_="data-table")[1]
    egg_moves_table = soup.find_all("table", class_="data-table")[2]

    level_up_moves = get_moves_from_table(level_up_table, level_key=0)
    tm_moves = get_moves_from_table(tm_table)
    egg_moves = get_moves_from_table(egg_moves_table)

    return level_up_moves + tm_moves + egg_moves




    
####################
##  GET DETAILS   ##
####################      
def get_pokemon_details(url):
    if '-' in url.split('/')[-1]:
        return None

    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    table = soup.find("table", class_="vitals-table")
    
    if not table:
        print(f"Error: Table not found for URL: {url}")
        return None

    rows = table.find_all("tr")
    local_no_row = table.find("th", string="Local №")
    if local_no_row:
        local_no_cell = local_no_row.find_next_sibling("td")
        local_nos = re.findall(r'\d+ .+?\)', local_no_cell.text)  
        local_no = '\n'.join(local_nos) 
    species = rows[2].find("td").text
    height = rows[3].find("td").text
    weight = rows[4].find("td").text
    abilities = [a.text for a in rows[5].find("td").find_all("a")]
    local_no = rows[6].find("td").text.strip()
    moves = get_moves(soup)

    details = {
        "species": species,
        "height": height,
        "weight": weight,
        "abilities": abilities,
        "local_no": local_no,
        "moves": moves  
    }

    return details

url = "https://pokemondb.net/pokedex/all"
response = requests.get(url)
soup = BeautifulSoup(response.text, "html.parser")

pokemon_list = []

table = soup.find("table", {"id": "pokedex"})
rows = table.find_all("tr")

for row in rows[1:]:
    cells = row.find_all("td")
    image_url = cells[0].find("img")["src"]
    dex_number = int(cells[0].find("span", class_="infocard-cell-data").text)
    name = cells[1].find("a", class_="ent-name").text
    form_name_element = cells[1].find("small", class_="text-muted")
    if form_name_element:
        name += f" ({form_name_element.text})"
    types = [typ.text for typ in cells[2].find_all("a")]
    total = int(cells[3].text)
    hp = int(cells[4].text)
    attack = int(cells[5].text)
    defense = int(cells[6].text)
    sp_atk = int(cells[7].text)
    sp_def = int(cells[8].text)
    speed = int(cells[9].text)

    pokemon = {
        "image": image_url,
        "dex_number": dex_number,
        "name": name,
        "type": types,
        "total": total,
        "hp": hp,
        "attack": attack,
        "defense": defense,
        "sp_atk": sp_atk,
        "sp_def": sp_def,
        "speed": speed,
    }

    pokemon_list.append(pokemon)


total_pokemon = len(pokemon_list)
completed_pokemon = 0

# Create an empty list to store completed Pokémon dictionaries.
completed_pokemon_list = []

with open("pokemon_data.json", "w") as outfile:
    for i, pokemon in enumerate(pokemon_list):
        name = pokemon["name"]
        sanitized_name = sanitize_name(name)
        pokedex_url = f"https://pokemondb.net/pokedex/{sanitized_name}"
        details = get_pokemon_details(pokedex_url)

        if details:
            pokemon.update(details)
    
            completed_pokemon_list.append(pokemon)
            completed_pokemon += 1
            percentage = (completed_pokemon / total_pokemon) * 100
            print(f"Progress: {completed_pokemon}/{total_pokemon} ({percentage:.2f}%) - {name}")

    # Dump the completed_pokemon_list into the JSON file.
    json.dump(completed_pokemon_list, outfile, indent=4)

    print("Data extraction completed.")

