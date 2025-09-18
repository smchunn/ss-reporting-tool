import pandas as pd
import sys
import os

if len(sys.argv) != 3:
    print("Usage: python trax_refresh.py <input_folder_path> <output_folder_path>")
    sys.exit(1)

input_folder = sys.argv[1]
output_folder = sys.argv[2]

# Ensure output folder exists
if not os.path.isdir(output_folder):
    print(f"Error: Output folder '{output_folder}' does not exist.")
    sys.exit(1)

# File paths
logspivot_file = os.path.join(input_folder, 'logs_pivot.xlsx')
rpt_file = os.path.join(input_folder, 'rpt_epr_std.xlsx')
output_file = os.path.join(output_folder, 'merged_normal.xlsx')

# Load data
logs_df = pd.read_excel(logspivot_file, dtype=str)
rpt_df = pd.read_excel(rpt_file, dtype=str)

# Only bring in columns from rpt that are already in logs_pivot
shared_cols = [col for col in rpt_df.columns if col in logs_df.columns]

# Setup columns order, enforcing add/validate effectivity at 10th & 11th
logs_cols = list(logs_df.columns)
for col in ["ADD EFFECTIVITY", "VALIDATE EFFECTIVITY"]:
    if col in logs_cols:
        logs_cols.remove(col)
logs_cols.insert(9, "ADD EFFECTIVITY")
logs_cols.insert(10, "VALIDATE EFFECTIVITY")

# Create comparison keys
logs_df['_key'] = logs_df['PN'].astype(str) + '||' + logs_df['AC'].astype(str) + '||' + logs_df['Action'].astype(str)
rpt_df['_key'] = rpt_df['PN'].astype(str) + '||' + rpt_df['AC'].astype(str) + '||' + rpt_df['Action'].astype(str)

logs_keys = set(logs_df['_key'])
rpt_keys = set(rpt_df['_key'])

# 1. Add new rows from rpt that don't exist in logs, STATUS must always be "Initial"
new_keys = rpt_keys - logs_keys
new_rows = rpt_df[rpt_df['_key'].isin(new_keys)]
if len(new_rows) > 0:
    append_df = pd.DataFrame(columns=logs_cols)
    for idx, row in new_rows.iterrows():
        row_dict = {}
        for col in logs_cols:
            if col == 'STATUS':
                row_dict[col] = 'Initial'
            elif col in shared_cols:
                row_dict[col] = row[col]
            else:
                row_dict[col] = ''
        append_df = pd.concat([append_df, pd.DataFrame([row_dict])], ignore_index=True)
    logs_df = pd.concat([logs_df, append_df], ignore_index=True)

# 2. Mark as "Complete" if exists in logs and not in rpt
removed_keys = logs_keys - rpt_keys
logs_df.loc[logs_df['_key'].isin(removed_keys), 'STATUS'] = 'Complete'

# 3. Update status for shared rows
overlap_keys = rpt_keys & logs_keys
subset = logs_df['_key'].isin(overlap_keys)
def update_status(status):
    if str(status).strip() == 'Complete':
        return 'Re-Opened'
    elif str(status).strip() == 'Updated':
        return 'Initial'
    else:
        return status

logs_df.loc[subset, 'STATUS'] = logs_df.loc[subset, 'STATUS'].apply(update_status)

# Remove helper key
logs_df = logs_df.drop(columns=['_key'])

# Ensure columns order and presence of ADD EFFECTIVITY/VALIDATE EFFECTIVITY
for col in ["ADD EFFECTIVITY", "VALIDATE EFFECTIVITY"]:
    if col not in logs_df.columns:
        logs_df[col] = ""
for col in logs_cols:
    if col not in logs_df.columns:
        logs_df[col] = ""
logs_df = logs_df[logs_cols + [c for c in logs_df.columns if c not in logs_cols]]

print(f"Saving to: {output_file}")
logs_df.to_excel(output_file, index=False)
print(f'Update/merge complete. Output saved to {output_file}')