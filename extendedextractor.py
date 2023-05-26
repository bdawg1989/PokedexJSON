import requests
from bs4 import BeautifulSoup
import json
import re
from tqdm import tqdm
import colorama
colorama.init()


####################
##  Sanitize Name ##
####################
def sanitize_name(name, is_alt_form=False):
    name = name.replace("♀", "-f").replace("♂", "-m")
    name = name.replace("é", "e")  # Replace "é" with "e"
    name = re.sub(r"[^a-zA-Z0-9\s-]", "", name)  # Remove any special characters except spaces and hyphens
    name = name.replace(" ", "-")  # Replace spaces with hyphens
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
    session = requests.Session()
    response = session.get(url)
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "lxml")

    tab_links = soup.find_all("a", class_="sv-tabs-tab")
    form_links = [link for link in tab_links if link.get("href").startswith("#tab-basic-")]
    abilities_map = {}

    for form_link in form_links:
        form_id = form_link["href"].replace("#tab-basic-", "")
        form_name = form_link.text
        form_tab = soup.find("div", id=f"tab-basic-{form_id}")
        abilities_row = form_tab.find("th", string="Abilities").find_next_sibling("td")
        abilities = [a.text for a in abilities_row.find_all("a")]
        abilities_map[form_name] = abilities

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
    local_no = rows[6].find("td").text.strip()
    moves = get_moves(name)
    gender = get_gender(soup)
    evolutions = get_evolutions(soup)

    details = {
        "species": species,
        "height": height,
        "weight": weight,
        "abilities": abilities_map,
        "local_no": local_no,
        "moves": moves,
        "gender": gender,
        "evolutions": evolutions
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

pokemon_forms_mapping = {
    "Flabébé": ["Flabebe-Orange", "Flabebe-Blue", "Flabebe-White", "Flabebe-Yellow"],
    "Vivillon": ["Vivillon-Archipelago", "Vivillon-Continental", "Vivillon-Elegant", "Vivillon-Garden", "Vivillon-High Plains", "Vivillon-Icy Snow", "Vivillon-Jungle", "Vivillon-Marine", "Vivillon-Meadow", "Vivillon-Modern", "Vivillon-Monsoon", "Vivillon-Ocean", "Vivillon-Polar", "Vivillon-River", "Vivillon-Sandstorm", "Vivillon-Savanna", "Vivillon-Sun", "Vivillon-Tundra"]
}

with open("pokemon_data.json", "w") as outfile:
    for i, pokemon in tqdm(
        enumerate(pokemon_list),
        total=total_pokemon,
        desc="Extracting Data",
        unit="pokemon",
        bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [Elapsed: {elapsed}, Remaining: {remaining}]",
        colour='green'
    ):
        name = pokemon["name"]
        base_name = get_base_name(name)
        sanitized_name = sanitize_name(base_name)         
        pokedex_url = f"https://pokemondb.net/pokedex/{sanitized_name}"
        details = get_pokemon_details(sanitized_name, pokedex_url)

        if details:
            # Handle Pokémon with forms
            forms = pokemon_forms_mapping.get(pokemon['name'])
            if forms:
                original_pokemon = pokemon.copy()
                original_pokemon.update(details)

                # Sanitize the original Pokémon's name
                sanitized_original_name = original_pokemon['name'].replace('é', 'e')

                # Change the name of the original Pokémon
                if original_pokemon['name'] != sanitized_original_name:
                    original_pokemon['name'] = sanitized_original_name
                    details['abilities'][sanitized_original_name] = details['abilities'].pop(pokemon['name'])

                completed_pokemon_list.append(original_pokemon)

                # Get the abilities of the original Pokémon
                original_abilities = details['abilities'].get(sanitized_original_name, [])

                # Handle Pokémon forms
                for form in forms:
                    pokemon_form = pokemon.copy()
                    pokemon_form['name'] = form

                    # Add the original abilities to the form
                    details['abilities'][form] = original_abilities

                    pokemon_form.update(details)
                    completed_pokemon_list.append(pokemon_form)
            else:
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
                "Wooper (Paldean Wooper)": "Wooper-Paldea",
				"Hoopa (Hoopa Confined)": "Hoopa",
				"Hoopa (Hoopa Unbound)": "Hoopa-Unbound",
				"Charizard (Mega Charizard X)": "Charizard-Mega-X",
				"Charizard (Mega Charizard Y)": "Charizard-Mega-Y",
				"Diancie (Mega Diancie)": "Diancie-Mega",
				"Landorus (Incarnate Forme)": "Landorus",
				"Landorus (Therian Forme)": "Landorus-Therian",
				"Lopunny (Mega Lopunny)": "Lopunny-Mega",
				"Scizor (Mega Scizor)": "Scizor-Mega",
				"Swampert (Mega Swampert)": "Swampert-Mega",
				"Tornadus (Incarnate Forme)": "Tornadus",
				"Tornadus (Therian Forme)": "Tornadus-Therian",
				"Urshifu (Single Strike Style)": "Urshifu",
				"Urshifu (Rapid Strike Style)": "Urshifu-Rapid-Strike",
				"Garchomp (Mega Garchomp)": "Garchomp-Mega",
				"Mawile (Mega Mawile)": "Mawile-Mega",
				"Medicham (Mega Medicham)": "Medicham-Mega",
				"Pinsir (Mega Pinsir)": "Pinsir-Mega",
				"Beedrill (Mega Beedrill)": "Beedrill-Mega",
				"Gardevoir (Mega Gardevoir)": "Gardevoir-Mega",
				"Gyarados (Mega Gyarados)": "Gyarados-Mega",
				"Latios (Mega Latios)": "Latios-Mega",
				"Latias (Mega Latias)": "Latias-Mega",
				"Ninetales (Alolan Ninetales)": "Ninetales-Alola",
				"Vulpix (Alolan Vulpix)": "Vulpix-Alola",
				"Sableye (Mega Sableye)": "Sableye-Mega",
				"Slowpoke (Galarian Slowpoke)": "Slowpoke-Galar",
				"Slowbro (Mega Slowbro)": "Slowbro-Mega",
				"Slowbro (Galarian Slowbro)": "Slowbro-Galar",
				"Slowking (Galarian Slowking)": "Slowking-Galar",
				"Tyranitar (Mega Tyranitar)": "Tyranitar-Mega",
				"Venusaur (Mega Venusaur)": "Venusaur-Mega",
				"Gallade (Mega Gallade)": "Gallade-Mega",
				"Moltres (Galarian Moltres)": "Moltres-Galar",
				"Zapdos (Galarian Zapdos)": "Zapdos-Galar",
				"Articuno (Galarian Articuno)": "Articuno-Galar",
				"Abomasnow (Mega Abomasnow)": "Abomasnow-Mega",
				"Absol (Mega Absol)": "Absol-Mega",
				"Aerodactyl (Mega Aerodactyl)": "Aerodactyl-Mega",
				"Aggron (Mega Aggron)": "Aggron-Mega",
				"Altaria (Mega Altaria)": "Altaria-Mega",
				"Ampharos (Mega Ampharos)": "Ampharos-Mega",
				"Audino (Mega Audino)": "Audino-Mega",
				"Banette (Mega Banette)": "Banette-Mega",
				"Camerupt (Mega Camerupt)": "Camerupt-Mega",
				"Deoxys (Normal Forme)": "Deoxys",
				"Deoxys (Attack Forme)": "Deoxys-Attack",
				"Deoxys (Defense Forme)": "Deoxys-Defense",
				"Deoxys (Speed Forme)": "Deoxys-Speed",
				"Dugtrio (Alolan Dugtrio)": "Dugtrio-Alola",
				"Exeggutor (Alolan Exeggutor)": "Exeggutor-Alola",
				"Glalie (Mega Glalie)": "Glalie-Mega",
				"Geodude (Alolan Geodude)": "Geodude-Alola",
				"Graveler (Alolan Graveler)": "Graveler-Alola",
				"Golem (Alolan Golem)": "Golem-Alola",
				"Pumpkaboo (Average Size)": "Pumpkaboo",
				"Pumpkaboo (Small Size)": "Pumpkaboo-Small",
				"Pumpkaboo (Large Size)": "Pumpkaboo-Large",
				"Pumpkaboo (Super Size)": "Pumpkaboo-Super",
				"Gourgeist (Average Size)": "Gourgeist",
				"Gourgeist (Small Size)": "Gourgeist-Small",
				"Gourgeist (Large Size)": "Gourgeist-Large",
				"Gourgeist (Super Size)": "Gourgeist-Super",
				"Heracross (Mega Heracross)": "Heracross-Mega",
				"Houndoom (Mega Houndoom)": "Houndoom-Mega",
				"Keldeo (Ordinary Form)": "Keldeo",
				"Keldeo (Resolute Form)": "Keldeo-Resolute",
				"Manectric (Mega Manectric)": "Manectric-Mega",
				"Marowak (Alolan Marowak)": "Marowak-Alola",
				"Meowstic (Male)": "Meowstic",
				"Meowstic (Female)": "Meowstic-F",
				"Meowth (Alolan Meowth)": "Meowth-Alola",
				"Meowth (Galarian Meowth)": "Meowth-Galar",
				"Persian (Alolan Persian)": "Persian-Alola",
				"Pidgeot (Mega Pidgeot)": "Pidgeot-Mega",
				"Raichu (Alolan Raichu)": "Raichu-Alola",
				"Ponyta (Galarian Ponyta)": "Ponyta-Galar",
				"Rapidash (Galarian Rapidash)": "Rapidash-Galar",
				"Rattata (Alolan Rattata)": "Rattata-Alola",
				"Raticate (Alolan Raticate)": "Raticate-Alola",
				"Sandshrew (Alolan Sandshrew)": "Sandshrew-Alola",
				"Sceptile (Mega Sceptile)": "Sceptile-Mega",
				"Sharpedo (Mega Sharpedo)": "Sharpedo-Mega",
				"Steelix (Mega Steelix)": "Steelix-Mega",
				"Stunfisk (Galarian Stunfisk)": "Stunfisk-Galar",
				"Thundurus (Incarnate Forme)": "Thundurus",
				"Thundurus (Therian Forme)": "Thundurus-Therian",
				"Weezing (Galarian Weezing)": "Weezing-Galar",
				"Burmy (Plant Cloak)": "Burmy",
				"Burmy (Sandy Cloak)": "Burmy-Sandy",
				"Burmy (Trash Cloak)": "Burmy-Trash",
				"Wormadam (Plant Cloak)": "Wormadam",
				"Wormadam (Sandy Cloak)": "Wormadam-Sandy",
				"Wormadam (Trash Cloak)": "Wormadam-Trash",
				"Zygarde (50% Forme)": "Zygarde",
				"Zygarde (10% Forme)": "Zygarde-10%",
				"Zygarde (Complete Forme)": "Zygarde-Complete",
				"Linoone (Galarian Linoone)": "Linoone-Galar",
				"Mr. Mime (Galarian Mr. Mime)": "Mr. Mime-Galar",
				"Corsola (Galarian Corsola)": "Corsola-Galar",
				"Darumaka (Galarian Darumaka)": "Darumaka-Galar",
				"Diglett (Alolan Diglett)": "Diglett-Alola",
				"Farfetch'd (Galarian Farfetch'd)": "Farfetch'd-Galar",
				"Grimer (Alolan Grimer)": "Grimer-Alola",
				"Nidoran\u2640": "Nidoran-M",
				"Nidoran\u2640": "Nidoran-F",
				"Yamask (Galarian Yamask)": "Yamask-Galar",
				"Zigzagoon (Galarian Zigzagoon)": "Zigzagoon-Galar",
				"Basculegion (Male)": "Basculegion",
				"Basculegion (Female)": "Basculegion-F",
				"Enamorus (Incarnate Forme)": "Enamorus",
				"Enamorus (Therian Forme)": "Enamorus-Therian",
				"Palafin (Zero Form)": "Palafin",
				"Palafin (Hero Form)": "Palafin-Hero",
				"Gimmighoul (Chest Form)": "Gimmighoul",
				"Gimmighoul (Roaming Form)": "Gimmighoul-Roaming",
				"Blastoise (Mega Blastoise)": "Blastoise-Mega",
				"Alakazam (Mega Alakazam)": "Alakazam-Mega",
				"Muk (Alolan Muk)": "Muk-Alola",
				"Gengar (Mega Gengar)": "Gengar-Mega",
				"Kangaskhan (Mega Kangaskhan)": "Kangaskhan-Mega",
				"Eevee (Partner Eevee)": "Eevee",
				"Mewtwo (Mega Mewtwo X)": "Mewtwo-Mega-X",
				"Mewtwo (Mega Mewtwo Y)": "Mewtwo-Mega-Y",
				"Sceptile (Mega Sceptile)": "Sceptile-Mega",
				"Blaziken (Mega Blaziken)": "Blaziken-Mega",
				"Castform (Sunny Form)": "Castform-Sunny",
				"Castform (Rainy Form)": "Castform-Rainy",
				"Castform (Snowy Form)": "Castform-Snowy",
				"Salamence (Mega Salamence)": "Salamence-Mega",
				"Metagross (Mega Metagross)": "Metagross-Mega",
				"Kyogre (Primal Kyogre)": "Kyogre-Primal",
				"Groudon (Primal Groudon)": "Groudon-Primal",
				"Rayquaza (Mega Rayquaza)": "Rayquaza-Mega",
				"Lucario (Mega Lucario)": "Lucario-Mega",
				"Dialga (Origin Forme)": "Dialga-Origin",
				"Palkia (Origin Forme)": "Palkia-Origin",
				"Giratina (Altered Forme)": "Giratina",
				"Giratina (Origin Forme)": "Giratina-Origin",
				"Shaymin (Land Forme)": "Shaymin",
				"Shaymin (Sky Forme)": "Shaymin-Sky",
				"Audino (Mega Audino)": "Audino-Mega",
				"Darmanitan (Standard Mode)": "Darmanitan",
				"Darmanitan (Zen Mode)": "Darmanitan-Zen",
				"Darmanitan (Galarian Standard Mode)": "Darmanitan-Galar",
				"Darmanitan (Galarian Zen Mode)": "Darmanitan-Galar-Zen",
				"Kyurem (White Kyurem)": "Kyurem-White",
				"Kyurem (Black Kyurem)": "Kyurem-Black",
				"Meloetta (Aria Forme)": "Meloetta",
				"Meloetta (Pirouette Forme)": "Meloetta-Pirouette",
				"Greninja (Ash-Greninja)": "Greninja-Ash",
				"Aegislash (Shield Forme)": "Aegislash",
				"Aegislash (Blade Forme)": "Aegislash-Blade",
				"Rockruff (Own Tempo Rockruff)": "Rockruff-Own-Tempo",
				"Wishiwashi (Solo Form)": "Wishiwashi",
				"Wishiwashi (School Form)": "Wishiwashi-School",
				"Minior (Meteor Form)": "Minior-Meteor",
				"Minior (Core Form)": "Minior",
				"Necrozma (Dusk Mane Necrozma)": "Necrozma-Dusk-Mane",
				"Necrozma (Dawn Wings Necrozma)": "Necrozma-Dawn-Wings",
				"Necrozma (Ultra Necrozma)": "Necrozma-Ultra",
				"Eiscue (Ice Face)": "Eiscue",
				"Eiscue (Noice Face)": "Eiscue-Noice",
				"Morpeko (Full Belly Mode)": "Morpeko",
				"Morpeko (Hangry Mode)": "Morpeko-Hangry",
				"Zacian (Hero of Many Battles)": "Zacian",
				"Zacian (Crowned Sword)": "Zacian-Crowned",
				"Zamazenta (Hero of Many Battles)": "Zamazenta",
				"Zamazenta (Crowned Shield)": "Zamazenta-Crowned",
				"Eternatus (Eternamax)": "Eternatus-Eternamax",
				"Calyrex (Ice Rider)": "Calyrex-Ice",
                "Sandslash (Alolan Sandslash)": "Sandslash-Alola",
				"Calyrex (Shadow Rider)": "Calyrex-Shadow"	
            }

            if name in custom_name_changes:
                pokemon["name"] = custom_name_changes[name]

            completed_pokemon_list.append(pokemon)

            for evolved_pokemon, level in details["evolutions"].items():
                for p in completed_pokemon_list:
                    if p["name"] == evolved_pokemon:
                        p["Evolves"] = level
                        break

            completed_pokemon += 1

    # Dump the completed_pokemon_list into the JSON file.
    json.dump([p for p in completed_pokemon_list if p['name'] != 'Palafin-Hero'], outfile, indent=4)

    print("Data extraction completed.")
