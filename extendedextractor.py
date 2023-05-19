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
##  GET GENDER    ##
####################
def get_gender(soup):
    breeding_section = soup.find("h2", string="Breeding")
    
    if not breeding_section:
        return ["Genderless"]

    table = breeding_section.find_next("table", class_="vitals-table")

    if not table:
        return ["Genderless"]

    gender_row = table.find("th", string="Gender")

    if not gender_row:
        return ["Genderless"]

    gender_info = gender_row.find_next_sibling("td")

    if not gender_info:
        return ["Genderless"]

    gender_text = gender_info.get_text(strip=True)
    
    if "Genderless" in gender_text:
        return ["Genderless"]
    
    genders = []

    if "male" in gender_text.lower():
        genders.append("Male")
    if "female" in gender_text.lower():
        genders.append("Female")

    return genders

####################
##  Get Base Name ##
####################
def get_base_name(name):
    base_name = re.sub(r'\s\(.*\)', '', name)  # Remove form name from alternate forms
    return base_name
    
##########################
## GET MOVES FROM TABLE ##
##########################
def get_moves_from_table(moves_table, gen):
    move_rows = moves_table.find_all("tr")[1:]
    header_row = moves_table.find("tr")
    headers = header_row.find_all("th")

    level_column_index = None
    for i, header in enumerate(headers):
        header_text = header.find("div", class_="sortwrap")
        if header_text and "lv." in header_text.text.lower():
            level_column_index = i
            break

    moves = {}
    for row in move_rows:
        cells = row.find_all("td")

        move_link = None
        move_type_element = None

        for cell in cells:
            if not move_link:
                move_link = cell.find("a", class_="ent-name")
            if not move_type_element:
                move_type_element = cell.find("a", class_="type-icon")
            if move_link and move_type_element:
                break

        if move_link and move_type_element:
            move = move_link.text
            move_type = move_type_element.text

            if level_column_index is not None:
                level_cell = cells[level_column_index]
                level = int(level_cell.text.strip()) if level_cell.text.strip().isdigit() else None
            else:
                level = None

            power_cell = cells[-2].text
            power = int(power_cell) if power_cell.isdigit() else None

            accuracy_cell = cells[-1].text
            accuracy = int(accuracy_cell) if accuracy_cell.isdigit() else None

            move_data = {
                "level": level,
                "move": move,
                "type": move_type,
                "power": power,
                "accuracy": accuracy,
                "generations": [gen]
            }

            # Check if the move already exists in the moves dictionary.
            if move in moves:
                # If it does, just append the current generation to the "generations" list.
                moves[move]["generations"].append(gen)
            else:
                # If not, add the new move to the dictionary.
                moves[move] = move_data

    return moves



####################
##   GET MOVES    ##
####################
def get_moves(name):
    all_moves = {}
    for i in range(1, 10):  # Iterating through generations 1 to 9
        response = requests.get(f"https://pokemondb.net/pokedex/{name}/moves/{i}")
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            moves_tables = soup.find_all("table", class_="data-table")
            for moves_table in moves_tables:
                gen_moves = get_moves_from_table(moves_table, i)
                # Iterate over the gen_moves dictionary
                for move, move_data in gen_moves.items():
                    # Check if the move already exists in the all_moves dictionary.
                    if move in all_moves:
                        # If it does, append the current generation to the "generations" list.
                        if i not in all_moves[move]["generations"]:
                            all_moves[move]["generations"].append(i)
                    else:
                        # If not, add the new move to the dictionary.
                        all_moves[move] = move_data
        else:
            print(f"Skipping Generation {i} for {name}")
    return all_moves


####################
##  Get EVOLUTION ##
####################  
def get_evolutions(soup):
    evolutions = {}
    infocard_list_evo = soup.find("div", class_="infocard-list-evo")
    if infocard_list_evo:
        infocard_arrows = infocard_list_evo.find_all("span", class_="infocard-arrow")
        for arrow in infocard_arrows:
            level_text = arrow.find("small").text
            level = int(re.search(r'\d+', level_text).group()) if re.search(r'\d+', level_text) else None
            next_pokemon = arrow.find_next("span", class_="infocard-lg-data").find("a", class_="ent-name").text
            evolutions[next_pokemon] = level
    return evolutions
    
####################
##  GET DETAILS   ##
####################      
def get_pokemon_details(name, url):
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
    moves = get_moves(name)  # Get moves
    gender = get_gender(soup)
    evolutions = get_evolutions(soup)  # Retrieve evolution information
    
    details = {
        "species": species,
        "height": height,
        "weight": weight,
        "abilities": abilities,
        "local_no": local_no,
        "moves": moves,  # Include moves in the details
        "gender": gender,
        "evolutions": evolutions  # Include evolutions in the details
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
        details = get_pokemon_details(sanitized_name, pokedex_url)  # Provide name and URL


        if details:
            if '(' in name:
                form_name = re.findall(r'\((.*?)\)', name)[0]
                pokemon['form_name'] = form_name

            pokemon.update(details)
            # Custom name changes
            custom_name_changes = {
                "Tauros (Combat Breed)": "Tauros-Paldea-Combat",
                "Tauros (Blaze Breed)": "Tauros-Paldea-Blaze",
                "Tauros (Aqua Breed)": "Tauros-Paldea-Aqua",
                "Tatsugiri (Curly Form)": "Tatsugiri",
                "Tatsugiri (Droopy Form)": "Tatsugiri-Droopy",
                "Tatsugiri (Stretchy Form)": "Tatsugiri-Stretchy",
                "Lycanroc (Midday Form)": "Lycanroc",
                "Lycanroc (Dusk Form)": "Lycanroc-Dusk",
                "Lycanroc (Midnight Form)": "Lycanroc-Midnight",
                "Oricorio (Baile Style)": "Oricorio",
                "Oricorio (Pom-Pom Style)": "Oricorio-Pom-Pom",
                "Oricorio (Pa'u Style)": "Oricorio-Pa'u",
                "Oricorio (Sensu Style)": "Oricorio-Sensu",
                "Toxtricity (Amped Form)": "Toxtricity",
                "Toxtricity (Low Key Form)": "Toxtricity-Low-Key",
                "Maushold (Family of Three)": "Maushold",
                "Maushold (Family of Four)": "Maushold-Four",
                "Dudunsparce (Three-Segment Form)": "Dudunsparce-Three-Segment",
                "Dudunsparce (Two-Segment Form)": "Dudunsparce",
                "Flabébé": "Flabebe",
                "Zoroark (Hisuian Zoroark)": "Zoroark-Hisui",
                "Braviary (Hisuian Braviary)": "Braviary-Hisui",
                "Arcanine (Hisuian Arcanine)": "Arcanine-Hisui",
                "Avalugg (Hisuian Avalugg)": "Avalugg-Hisui",
                "Decidueye (Hisuian Decidueye)": "Decidueye-Hisui",
                "Electrode (Hisuian Electrode)": "Electrode-Hisui",
                "Goodra (Hisuian Goodra)": "Goodra-Hisui",
                "Growlithe (Hisuian Growlithe)": "Growlithe-Hisui",
                "Lilligant (Hisuian Lilligant)": "Lilligant-Hisui",
                "Qwilfish (Hisuian Qwilfish)": "Qwilfish-Hisui",
                "Samurott (Hisuian Samurott)": "Samurott-Hisui",
                "Sliggoo (Hisuian Sliggoo)": "Sliggoo-Hisui",
                "Sneasel (Hisuian Sneasel)": "Sneasel-Hisui",
                "Typhlosion (Hisuian Typhlosion)": "Typhlosion-Hisui",
                "Voltorb (Hisuian Voltorb)": "Voltorb-Hisui",
                "Zorua (Hisuian Zorua)": "Zorua-Hisui",
                "Rotom (Heat Rotom)": "Rotom-Heat",
                "Rotom (Mow Rotom)": "Rotom-Mow",
                "Rotom (Fan Rotom)": "Rotom-Fan",
                "Rotom (Frost Rotom)": "Rotom-Frost",
                "Rotom (Wash Rotom)": "Rotom-Wash",
                "Basculin (Red-Striped Form)": "Basculin",
                "Basculin (Blue-Striped Form)": "Basculin-Blue-Striped",
                "Basculin (White-Striped Form)": "Basculin-White-Striped",
                "Indeedee (Male)": "Indeedee",
                "Indeedee (Female)": "Indeedee-F",
                "Squawkabilly (Green Plumage)": "Squawkabilly",
                "Squawkabilly (Blue Plumage)": "Squawkabilly-Blue",
                "Squawkabilly (Yellow Plumage)": "Squawkabilly-Yellow",
                "Squawkabilly (White Plumage)": "Squawkabilly-White",
                "Oinkologne (Female)": "Oinkologne-F",
                "Oinkologne (Male)": "Oinkologne",
                "Wooper (Paldean Wooper)": "Wooper-Paldea"
            }

            if name in custom_name_changes:
                pokemon["name"] = custom_name_changes[name]
            # Append the Pokémon dictionary to the completed_pokemon_list.
            completed_pokemon_list.append(pokemon)
            # Handle evolutions
            for evolved_pokemon, level in details["evolutions"].items():
                for p in completed_pokemon_list:
                    if p["name"] == evolved_pokemon:
                        p["Evolves"] = level
                        break

            completed_pokemon += 1
            percentage = (completed_pokemon / total_pokemon) * 100
            print(f"Progress: {completed_pokemon}/{total_pokemon} ({percentage:.2f}%) - {name}")

    # Dump the completed_pokemon_list into the JSON file.
    json.dump(completed_pokemon_list, outfile, indent=4)

    print("Data extraction completed.")


