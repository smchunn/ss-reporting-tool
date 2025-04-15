import os

# Define the paths
config_path = './data/A319_config_category.toml'

# Get the current directory where the script is located
current_directory = os.path.dirname(os.path.abspath(__file__))

# Define the path to the Excel folder in the current directory
excel_folder_path = os.path.join(current_directory, './A319/Category')

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
    # Create a relative path for the src entry and prepend './'
    relative_src = os.path.relpath(os.path.join(excel_folder_path, excel_file), current_directory)
    new_entry = f"\n[tables.{table_name}]\nid = \"\"\nsrc = \"../{relative_src}\"\n"
    new_entries.append(new_entry)

# Sort the new entries alphabetically by table name
new_entries.sort(key=lambda entry: entry.split('.')[1].strip())

# Combine the header with the new entries
updated_content = header_content + new_entries

# Write the updated content back to config.toml
with open(config_path, 'w') as file:
    file.writelines(updated_content)

print(f"Updated {config_path} with {len(excel_files)} new table entries.")
