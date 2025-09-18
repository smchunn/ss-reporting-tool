import sys
import os
import pandas as pd

# --- ARGUMENTS ---
if len(sys.argv) < 3:
    print("Usage: python combine_logs.py <input_folder> <output_folder>")
    sys.exit(1)

input_folder = sys.argv[1]
output_folder = sys.argv[2]
output_file = os.path.join(output_folder, "logs.xlsx")

fleets_in_scope = {'A320', 'A319', 'A321'}

def fleet_in_scope(fleet_str):
    if not isinstance(fleet_str, str):
        return False
    fleets = set(fleet_str.split())
    return bool(fleets_in_scope & fleets)

# --- PROCESS FILES ---
all_rows = []

for file in os.listdir(input_folder):
    if file.endswith('.csv'):
        file_path = os.path.join(input_folder, file)
        try:
            df = pd.read_csv(
                file_path,
                sep='\t',  # Use tab as the delimiter
                encoding='utf-16',
                on_bad_lines='skip'
            )
            df.columns = df.columns.str.strip()
            print(f"Columns in {file_path}: {df.columns.tolist()}")
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            continue

        required_cols = ['Reason for Request', 'Fleet(s)', 'PN', 'SubmittedDate(EST)']
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            print(f"Skipping {file_path}: missing required columns: {missing}")
            continue

        df = df[df['Reason for Request'].astype(str).str.strip() == 'Effectivity']
        df = df[df['Fleet(s)'].apply(fleet_in_scope)]
        all_rows.append(df)

if not all_rows:
    print("No matching records found.")
    sys.exit(0)

combined_df = pd.concat(all_rows, ignore_index=True)

# --- PARSE DATE AND DEDUPLICATE ---
combined_df['SubmittedDate(EST)'] = pd.to_datetime(
    combined_df['SubmittedDate(EST)'],
    errors='coerce'
)
combined_df = combined_df.sort_values('SubmittedDate(EST)', ascending=False)
combined_df = combined_df.drop_duplicates(subset='PN', keep='first')

# --- OUTPUT ---
combined_df.to_excel(output_file, index=False)
print(f"Combined file saved to {output_file}")