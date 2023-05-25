import json
from tqdm import tqdm

def rename_abilities(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)

    for entry in tqdm(data, desc="Processing entries", unit="entry"):
        if "abilities" in entry:
            abilities = entry["abilities"]
            name = entry["name"]

            # Rename form_name in abilities to name
            if "form_name" in entry and entry["form_name"] in abilities:
                abilities[name] = abilities[entry["form_name"]]
                del abilities[entry["form_name"]]

            # Delete abilities that do not match the 'name' key
            keys_to_delete = [key for key in abilities if key != name]
            for key in keys_to_delete:
                del abilities[key]

            # Convert "abilities" dictionary to a list
            if name in abilities:
                entry["abilities"] = abilities[name]

    with open(json_file, 'w') as f:
        json.dump(data, f, indent=4)

rename_abilities('pokemon_data.json')
