import requests
from bs4 import BeautifulSoup
import json
import re

####################
##  Sanitize Name ##
####################
def sanitize_name(name, is_alt_form=False):
    name = name.replace("♀", "-f").replace("♂", "-m")
    name = re.sub(r"[^a-zA-Z0-9\s-]", "", name)  # Remove any special characters except spaces and hyphens
    name = name.replace(" ", "-")  # Replace spaces with hyphens
    name = name.replace("é", "e")  # Replace "é" with "e"
    name = name.lower()
    return name

####################
##  Get Base Name ##
####################
def get_base_name(name):
    base_name = re.sub(r'\s\(.*\)', '', name)  # Remove form name from alternate forms
    return base_name
    
####################
## GET MOVES FROM TABLE ##
####################
def get_moves_from_table(moves_table):
    move_rows = moves_table.find_all("tr")[1:]
    header_row = moves_table.find("tr")
    headers = header_row.find_all("th")

    level_column_index = None
    for i, header in enumerate(headers):
        if "lvl" in header.text.lower() or "level" in header.text.lower():
            level_column_index = i
            break

    moves = []
    for row in move_rows:
        cells = row.find_all("td")
        move_link = cells[1].find("a", class_="ent-name")
        if not move_link:
            continue
        move = move_link.text
        move_type_element = cells[2].find("a", class_="type-icon")
        if not move_type_element:
            continue
        move_type = move_type_element.text
        power_cell = cells[4].text
        power = int(power_cell) if power_cell.isdigit() else None
        accuracy_cell = cells[5].text
        accuracy = int(accuracy_cell) if accuracy_cell.isdigit() else None

        level_cell = cells[0]
        level = int(level_cell.text) if level_cell.text.isdigit() else None

        move_data = {
            "level": level,
            "move": move,
            "type": move_type,
            "power": power,
            "accuracy": accuracy
        }
        moves.append(move_data)

    return moves




####################
##   GET MOVES    ##
####################
def get_moves(soup):
    moves_tables = soup.find_all("table", class_="data-table")

    moves = []
    for moves_table in moves_tables:
        move_rows = moves_table.find_all("tr")[1:]
        header_row = moves_table.find("tr")
        headers = header_row.find_all("th")

        # Check if the table has a "Level" column
        has_level_column = any("Lv." in header.get_text() for header in headers)
        if not has_level_column:
            # Check if the table has a "TM" column
            has_tm_column = any("TM" in cell.get_text() for cell in cells)
            if has_tm_column:
                continue  # Skip the table with "TM" column

        for row in move_rows:
            cells = row.find_all("td")
            move_link = cells[1].find("a", class_="ent-name")
            if not move_link:  # Skip rows without move name
                continue
            move = move_link.text
            move_type_element = cells[2].find("a", class_="type-icon")
            if not move_type_element:  # Skip rows without move type
                continue
            move_type = move_type_element.text
            power_cell = cells[4].text
            power = int(power_cell) if power_cell.isdigit() else None
            accuracy_cell = cells[5].text
            accuracy = int(accuracy_cell) if accuracy_cell.isdigit() else None

            level = None
            if has_level_column:
                level_cell = cells[0]
                if level_cell.text.isdigit():
                    level = int(level_cell.text)

            move_data = {
                "level": level,
                "move": move,
                "type": move_type,
                "power": power,
                "accuracy": accuracy
            }
            moves.append(move_data)

    return moves


####################
##  GET DETAILS   ##
####################      
def get_pokemon_details(url):

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
        local_nos = re.findall(r'\d+ .+?\)', local_no_cell.text)  # Find all sets of parentheses
        local_no = '\n'.join(local_nos)  # Join them with newline character
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
        "moves": moves  # Add the moves key
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
    name_element = cells[1].find("a", class_="ent-name")
    name = name_element.text
    form_name_element = cells[1].find("small", class_="text-muted")
    if form_name_element:
        form_name = form_name_element.text
        name += f" ({form_name})"
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
        base_name = get_base_name(name)
        sanitized_name = sanitize_name(base_name)
        pokedex_url = f"https://pokemondb.net/pokedex/{sanitized_name}"
        details = get_pokemon_details(pokedex_url)

        if details:
            if '(' in name:
                form_name = re.findall(r'\((.*?)\)', name)[0]
                pokemon['form_name'] = form_name

            pokemon.update(details)
            # Append the Pokémon dictionary to the completed_pokemon_list.
            completed_pokemon_list.append(pokemon)
            completed_pokemon += 1
            percentage = (completed_pokemon / total_pokemon) * 100
            print(f"Progress: {completed_pokemon}/{total_pokemon} ({percentage:.2f}%) - {name}")

    # Dump the completed_pokemon_list into the JSON file.
    json.dump(completed_pokemon_list, outfile, indent=4)

    print("Data extraction completed.")

