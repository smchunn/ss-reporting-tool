import pandas as pd
import sys
import os

if len(sys.argv) != 3:
    print("Usage: python normalize_ra.py <input_folder_path> <output_folder_path>")
    sys.exit(1)

input_folder = sys.argv[1]
output_folder = sys.argv[2]

# Check output folder exists
if not os.path.isdir(output_folder):
    print(f"Error: Output folder '{output_folder}' does not exist.")
    sys.exit(1)

# Define input and output file
input_file = os.path.join(input_folder, 'output.xlsx')      # You may change this if your input has a different name
output_file = os.path.join(output_folder, 'logs_pivot.xlsx')

print(f"Reading: {input_file}")

# Read input Excel
df = pd.read_excel(input_file, dtype=str)

# Prepare for normalization
normalized_records = []

for _, row in df.iterrows():
    # Gather all columns except the two effectivity columns
    base_data = {col: row[col] for col in df.columns if col not in ['ADD EFFECTIVITY', 'VALIDATE EFFECTIVITY']}
    
    # ADD EFFECTIVITY
    if pd.notnull(row.get('ADD EFFECTIVITY')):
        add_acs = [x.strip() for x in str(row['ADD EFFECTIVITY']).split('\n') if x.strip()]
        for ac in add_acs:
            rec = base_data.copy()
            rec['AC'] = ac
            rec['Action'] = 'ADD EFFECTIVITY'
            normalized_records.append(rec)
    
    # VALIDATE EFFECTIVITY
    if pd.notnull(row.get('VALIDATE EFFECTIVITY')):
        val_acs = [x.strip() for x in str(row['VALIDATE EFFECTIVITY']).split('\n') if x.strip()]
        for ac in val_acs:
            rec = base_data.copy()
            rec['AC'] = ac
            rec['Action'] = 'VALIDATE EFFECTIVITY'
            normalized_records.append(rec)

# Create normalized DataFrame
normalized_df = pd.DataFrame(normalized_records)

# Optional: Put 'AC' and 'Action' right after 'PN' for readability
cols = list(normalized_df.columns)
if 'PN' in cols:
    pn_idx = cols.index('PN') + 1
    for col in ['AC', 'Action']:
        if col in cols:
            cols.remove(col)
            cols.insert(pn_idx, col)
            pn_idx += 1
    normalized_df = normalized_df[cols]

print(f"Saving to: {output_file}")
normalized_df.to_excel(output_file, index=False)
print(f'Normalization complete. Output saved to {output_file}')