import pandas as pd
import os

# Define the input and output folders
input_folder = 'Effectivity Reports Engine'
output_folder = 'Effectivity_Reports_Mod'

# Get the list of files in the input folder
files = os.listdir(input_folder)

# Assume there is only one file in the input folder
if len(files) != 1:
    raise Exception("The input folder should contain exactly one file.")

# Get the file name
original_file_name = files[0]
original_file_path = os.path.join(input_folder, original_file_name)

# Load the original Excel file
df = pd.read_excel(original_file_path)

# Update the status to 'Validated' if 'FEEDBACK' column has a non-blank value
df.loc[df['FEEDBACK'].notna() & (df['FEEDBACK'] != ''), 'Status'] = 'Validated'

# Filter out rows where the status is 'Validated' or 'Complete'
open_parts_df = df[~df['Status'].isin(['Validated', 'Complete'])]

# Ensure the output folder exists
os.makedirs(output_folder, exist_ok=True)

# Summary for all records by Action
all_action_summary_df = pd.DataFrame()
all_action_summary_df['AC'] = open_parts_df['AC'].unique()

def count_action(ac_value):
    return len(open_parts_df[(open_parts_df['AC'] == ac_value) & (open_parts_df['PROPOSED_ACTION'] == 'UPDATE_EFFECTIVITY')])

all_action_summary_df['Update Effectivity'] = all_action_summary_df['AC'].apply(count_action)
all_action_summary_df['TOTAL'] = all_action_summary_df['Update Effectivity']

all_action_summary_file_path = os.path.join(output_folder, original_file_name.split('.')[0] + '_all_action.xlsx')
all_action_summary_df.to_excel(all_action_summary_file_path, index=False)

# Summary for all records by Status
status_categories = ['Initial', 'In-Work', 'Issue', 'Updated', 'Re-Opened', 'Validated', 'Complete']
all_status_summary_df = df.groupby(['AC', 'Status']).size().unstack(fill_value=0).reindex(columns=status_categories, fill_value=0).reset_index()

all_status_summary_file_path = os.path.join(output_folder, original_file_name.split('.')[0] + '_all_status.xlsx')
all_status_summary_df.to_excel(all_status_summary_file_path, index=False)

# Totals Sheet
total_update = df[df['PROPOSED_ACTION'] == 'UPDATE_EFFECTIVITY'].shape[0]
total_status = df['Status'].value_counts().reindex(status_categories, fill_value=0).to_dict()

totals_df = pd.DataFrame({
    'Update Effectivity': [total_update]
})

for status in status_categories:
    totals_df[status] = [total_status[status]]

totals_file_path = os.path.join(output_folder, original_file_name.split('.')[0] + '_totals.xlsx')
totals_df.to_excel(totals_file_path, index=False)

print(f"Summary files have been created in the '{output_folder}' folder:")
print(f" - {all_action_summary_file_path}")
print(f" - {all_status_summary_file_path}")
print(f" - {totals_file_path}")
