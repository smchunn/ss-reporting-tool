import pandas as pd
import sys
import os

if len(sys.argv) != 3:
    print("Usage: python merge_logs.py <input_folder_path> <output_folder_path>")
    sys.exit(1)

input_folder = sys.argv[1]
output_folder = sys.argv[2]

# Ensure the output folder exists
if not os.path.isdir(output_folder):
    print(f"Error: Output folder '{output_folder}' does not exist.")
    sys.exit(1)

# Define input file names
smartsheet_file = os.path.join(input_folder, 'OTHER.xlsx')
excel_table_file = os.path.join(input_folder, 'logs.xlsx')

# Define output file name (always output.xlsx in output folder)
output_file = os.path.join(output_folder, 'output.xlsx')

# Load data
smartsheet_df = pd.read_excel(smartsheet_file)
excel_df = pd.read_excel(excel_table_file)

# Insert 'Cleared By' as the 19th column (index 18)
col_position = 18
smartsheet_cols = list(smartsheet_df.columns)
if 'Cleared By' not in smartsheet_cols:
    smartsheet_cols.insert(col_position, 'Cleared By')
    smartsheet_df = smartsheet_df.reindex(columns=smartsheet_cols)
else:
    # If already present, just reindex to keep order
    smartsheet_df = smartsheet_df.reindex(columns=smartsheet_cols)

# Prepare the Excel table for merging
merge_cols = ['PN', 'DoneBy', 'SubmittedDate(EST)']
excel_df_subset = excel_df[merge_cols]

# Merge: left join to preserve Smartsheet order
merged_df = pd.merge(
    smartsheet_df,
    excel_df_subset,
    on='PN',
    how='left',
    suffixes=('', '_excel')
)

# Update columns as specified
merged_df['ASSIGNMENT'] = merged_df['DoneBy']
merged_df['STATUS'] = merged_df.apply(
    lambda row: 'Complete' if pd.notnull(row['DoneBy']) else row['STATUS'],
    axis=1
)
merged_df['Cleared By'] = merged_df.apply(
    lambda row: 'Request App' if pd.notnull(row['DoneBy']) else row['Cleared By'],
    axis=1
)
merged_df['COMPLETED DATE'] = merged_df['SubmittedDate(EST)']

# Drop helper columns
merged_df = merged_df.drop(['DoneBy', 'SubmittedDate(EST)'], axis=1)

# Reorder columns to match original Smartsheet export plus 'Cleared By'
final_cols = smartsheet_cols
final_cols = [col for col in final_cols if col in merged_df.columns]
remaining_cols = [col for col in merged_df.columns if col not in final_cols]
final_cols += remaining_cols
merged_df = merged_df[final_cols]

print(f"Saving to: {output_file}")
merged_df.to_excel(output_file, index=False)
print(f'Merge complete. Output saved to {output_file}')