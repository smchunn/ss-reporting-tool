import os
import toml

# Define the paths
import_folder = 'import'
reformat_config_path = './data/reformat_config.toml'
a320_config_path = './data/A319_A321_config.toml'

# Read the existing reformat_config.toml file
if os.path.exists(reformat_config_path):
    config = toml.load(reformat_config_path)
else:
    raise FileNotFoundError(f"{reformat_config_path} does not exist.")

# Read the A320_config.toml file to get target_ids
a320_config = toml.load(a320_config_path)

# Extract target_ids from A320_config.toml, skipping entries with blank id
target_ids = []
for table in a320_config.get('tables', {}).values():
    if table.get('id', ''):  # Only add target_id if id is not blank
        target_ids.append(table.get('id', ''))

# Clear existing table entries
config['tables'] = {}

# Iterate through Excel files in the import folder
excel_files = [f for f in os.listdir(import_folder) if f.endswith('.xlsx')]
for index, excel_file in enumerate(excel_files):
    table_name = os.path.splitext(excel_file)[0]  # Get the name without extension
    if index < len(target_ids):  # Only create entries if there are valid target_ids
        config['tables'][table_name] = {
            'id': "",  # Leave id blank
            'target_id': target_ids[index],  # Use target_id from A320_config
            'src': f"../import/{excel_file}",  # Correctly format the src path
            # 'date' is left out as per the requirement
        }

# Write the updated config back to reformat_config.toml
with open(reformat_config_path, 'w') as f:
    toml.dump(config, f)

print(f"Configuration file '{reformat_config_path}' updated successfully.")
