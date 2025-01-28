import pandas as pd
import os

# Define the input and output folders
input_folder = 'Effectivity Reports'
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

# Ensure the output folder exists
os.makedirs(output_folder, exist_ok=True)

# First Summary: Summary by Action
summary_df = pd.DataFrame()
summary_df['AC'] = df['AC'].unique()

def count_action(ac_value, action):
    return len(df[(df['AC'] == ac_value) & (df['PROPOSED_ACTION'] == action)])

summary_df['ADD_EFFECTIVITY'] = summary_df['AC'].apply(lambda x: count_action(x, 'ADD_EFFECTIVITY'))
summary_df['VALIDATE_EFFECTIVITY'] = summary_df['AC'].apply(lambda x: count_action(x, 'VALIDATE_EFFECTIVITY'))
summary_df['TOTAL'] = summary_df['ADD_EFFECTIVITY'] + summary_df['VALIDATE_EFFECTIVITY']

summary_file_path = os.path.join(output_folder, original_file_name.split('.')[0] + '_summary_by_action.xlsx')
summary_df.to_excel(summary_file_path, index=False)

# Second Summary: Summary by Status
status_categories = ['Initial', 'In-Work', 'Issue', 'Updated', 'Re-Opened', 'Validated', 'Complete']
status_summary_df = df.groupby(['AC', 'Status']).size().unstack(fill_value=0).reindex(columns=status_categories, fill_value=0).reset_index()

status_summary_file_path = os.path.join(output_folder, original_file_name.split('.')[0] + '_summary_by_status.xlsx')
status_summary_df.to_excel(status_summary_file_path, index=False)

# Totals Sheet
total_validate = summary_df['VALIDATE_EFFECTIVITY'].sum()
total_add = summary_df['ADD_EFFECTIVITY'].sum()
total_status = df['Status'].value_counts().reindex(status_categories, fill_value=0).to_dict()

totals_df = pd.DataFrame({
    'Total Validate': [total_validate],
    'Total Add': [total_add]
})

for status in status_categories:
    totals_df[status] = [total_status[status]]

totals_file_path = os.path.join(output_folder, original_file_name.split('.')[0] + '_totals.xlsx')
totals_df.to_excel(totals_file_path, index=False)

print(f"Summary files have been created in the '{output_folder}' folder:")
print(f" - {summary_file_path}")
print(f" - {status_summary_file_path}")
print(f" - {totals_file_path}")
