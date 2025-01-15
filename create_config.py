import os

# Define the paths
config_path = 'config.toml'
excel_folder_path = os.path.join('split_excel', 'Effectivity_Reports_Split')

# Read the existing config.toml content
with open(config_path, 'r') as file:
    config_content = file.readlines()

# Find the index where the table entries start
start_index = next((i for i, line in enumerate(config_content) if line.startswith("[tables.")), len(config_content))

# Keep only the header part of the config
header_content = config_content[:start_index]

# List all Excel files in the specified directory
excel_files = [f for f in os.listdir(excel_folder_path) if f.endswith('.xlsx')]

# Create new table entries for each Excel file
new_entries = []
for excel_file in excel_files:
    table_name = os.path.splitext(excel_file)[0].upper()
    new_entry = f"\n[tables.{table_name}]\nid = \"\"\nsrc = \"{excel_file}\"\n"
    new_entries.append(new_entry)

# Combine the header with the new entries
updated_content = header_content + new_entries

# Write the updated content back to config.toml
with open(config_path, 'w') as file:
    file.writelines(updated_content)

print(f"Updated {config_path} with {len(excel_files)} new table entries.")
