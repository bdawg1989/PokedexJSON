import json

def minify_json(input_filename, output_filename):
    # Read the JSON file
    with open(input_filename, 'r') as f:
        data = json.load(f)

    # Write the JSON file back out with no extra whitespace
    with open(output_filename, 'w') as f:
        json.dump(data, f, separators=(',', ':'))

# Call the function with the names of the input and output JSON files
minify_json('pokedex.json', 'minified_pokedex.json')
