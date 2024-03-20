import json

# Load the JSON file
with open('paper_ids.json', 'r') as file:
    data = json.load(file)

# Create a set to store unique abstract values
unique_abstracts = set()

# Create a new list to store the updated data
updated_data = []

# Iterate through the JSON data and remove duplicate abstracts
for item in data:
    if 'abstract' in item:
        abstract = item['abstract']
        if abstract not in unique_abstracts:
            unique_abstracts.add(abstract)
            updated_data.append(item)
# Write the updated JSON data to a new file
with open('output.json', 'w') as file:
    json.dump(updated_data, file, indent=2)