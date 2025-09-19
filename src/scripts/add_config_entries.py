import os
import sys
import toml

def load_config(config_path):
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return toml.load(f)
    else:
        return {}

def save_config(config, config_path):
    with open(config_path, 'w') as f:
        toml.dump(config, f)

def get_sheet_files(input_dir):
    # Consider files with .xlsx extension as sheets
    return [f for f in os.listdir(input_dir) if f.endswith('.xlsx') and os.path.isfile(os.path.join(input_dir, f))]

def main():
    if len(sys.argv) != 3:
        print("Usage: python add_config_entries.py <input_directory> <config_path>")
        sys.exit(1)

    input_dir = sys.argv[1]
    config_path = sys.argv[2]

    if not os.path.isdir(input_dir):
        print(f"Error: Input directory '{input_dir}' does not exist or is not a directory.")
        sys.exit(1)

    config = load_config(config_path)

    if 'reports' not in config:
        config['reports'] = {}

    sheet_files = get_sheet_files(input_dir)

    added = False
    for sheet_file in sheet_files:
        sheet_name = os.path.splitext(sheet_file)[0]
        if sheet_name not in config['reports']:
            # Add new entry following the format in UPS/config/config.toml
            config['reports'][sheet_name] = {
                'id': "",
                'date': "",
                'primary_column': 7,
                'tags': [],
                'src': sheet_file
            }
            added = True
            print(f"Added config entry for sheet: {sheet_name}")

    if added:
        save_config(config, config_path)
        print(f"Config updated and saved to {config_path}")
    else:
        print("No new sheets to add. Config not modified.")

if __name__ == "__main__":
    main()
