import os

# Define the paths
config_path = "/Users/silas.bash/Library/CloudStorage/OneDrive-MMC/SmartSheet_API/DEMO_interchangeability/config/report_config.toml"
# Get the current directory where the script is located
current_directory = os.path.dirname(os.path.abspath(__file__))

# Define the path to the Excel folder (absolute path)
excel_folder_path = "/Users/silas.bash/Library/CloudStorage/OneDrive-MMC/SmartSheet_API/DEMO_interchangeability/split"

# Read the existing config.toml content
with open(config_path, 'r') as file:
    config_content = file.readlines()

# Find the index where the table entries start
start_index = next((i for i, line in enumerate(config_content) if line.startswith("[reports.")), len(config_content))

# Keep only the header part of the config
header_content = config_content[:start_index]

# List all Excel files in the specified directory
excel_files = [f for f in os.listdir(excel_folder_path) if f.endswith('.xlsx')]

# Create new table entries for each Excel file
new_entries = []
for excel_file in excel_files:
    table_name = os.path.splitext(excel_file)[0].upper()
    # Get the absolute path for the src entry
    absolute_src = os.path.abspath(os.path.join(excel_folder_path, excel_file))
    new_entry = f"\n[reports.{table_name}]\nid = \"\"\nsrc = \"{absolute_src}\"\n"
    new_entries.append(new_entry)

# Sort the new entries alphabetically by table name
new_entries.sort(key=lambda entry: entry.split('.')[1].strip())

# Combine the header with the new entries
updated_content = header_content + new_entries

# Write the updated content back to config.toml
with open(config_path, 'w') as file:
    file.writelines(updated_content)

print(f"Updated {config_path} with {len(excel_files)} new table entries.")