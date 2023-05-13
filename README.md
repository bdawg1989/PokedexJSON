# Pokédex JSON

Pokédex in JSON format with extractor to always have it updated
---

#### Features:

- All Pokémon are present

- Each Pokémon contains:
  
  - Number
  - Name
  - Sprite image url
  - Learned Moves
  - Egg Moves
  - TM's
  - Gender
  - Abilities
  - Stats - HP, Atk, Def, SpA, SpD, and Spe.

- There is an extractor in Python that generates an always updated JSON

###### Items:

- All Items from Gen 3 - Gen 9 are included in items.json
  - Item Image
  - Generation
  - Item Name

- There is an extractor (item.py) that can be ran to extract all items from Bulbapedia.net

###### Note:

The data is extracted from [PokemonDB](https://pokemondb.net/)
