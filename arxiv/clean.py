import json

def strip_escapes(abstract):
    # Remove '\n' characters
    abstract = abstract.replace('\\n', '')

    # Remove trailing characters '\\n'
    abstract = abstract[9:]

    # Remove front characters '\\n \\u25b3 Less\\n'
    abstract = abstract[:-22]

    return abstract

# Read the JSON file
with open('badcase-full-41-s.json', 'r') as file:
    json_data = file.read()

# Parse the JSON string into a list of dictionaries
data = json.loads(json_data)

# Iterate over each dictionary in the list
for item in data:
    # Strip escape characters from the abstract
    item['abstract'] = strip_escapes(item['abstract'])

# Write the updated data to a new JSON file
with open('badcase-large-full41.json', 'w') as file:
    json.dump(data, file, indent=4)

print("New JSON file 'output.json' created with stripped data.")