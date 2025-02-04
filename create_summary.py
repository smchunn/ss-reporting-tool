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

# Update the status to 'Validated' if 'FEEDBACK' column has a non-blank value
df.loc[df['FEEDBACK'].notna() & (df['FEEDBACK'] != ''), 'Status'] = 'Validated'

# Filter out rows where the status is 'Validated' or 'Complete'
open_parts_df = df[~df['Status'].isin(['Validated', 'Complete'])]

# Ensure the output folder exists
os.makedirs(output_folder, exist_ok=True)

# Define the categories
categories = ['XPENDBL', 'SER', 'NON-SER', 'REPSER', 'REP-FA', 'ENGINES', 'CON-RAW', 'TOOL-SER']

# Function to create summaries for each category
def create_category_summaries(category):
    # Filter the DataFrame for the current category
    category_df = df[df['CATEGORY'] == category]
    open_category_df = open_parts_df[open_parts_df['CATEGORY'] == category]

    # First Summary: Summary by Action (only for open parts)
    action_summary_df = pd.DataFrame()
    action_summary_df['AC'] = open_category_df['AC'].unique()

    def count_action(ac_value, action):
        return len(open_category_df[(open_category_df['AC'] == ac_value) & (open_category_df['PROPOSED_ACTION'] == action)])

    action_summary_df['Add Effectivity'] = action_summary_df['AC'].apply(lambda x: count_action(x, 'ADD_EFFECTIVITY'))
    action_summary_df['Validate Effectivity'] = action_summary_df['AC'].apply(lambda x: count_action(x, 'VALIDATE_EFFECTIVITY'))
    action_summary_df['TOTAL'] = action_summary_df['Add Effectivity'] + action_summary_df['Validate Effectivity']

    action_summary_file_path = os.path.join(output_folder, f"{original_file_name.split('.')[0]}_{category}_action.xlsx")
    action_summary_df.to_excel(action_summary_file_path, index=False)

    # Second Summary: Summary by Status
    status_categories = ['Initial', 'In-Work', 'Issue', 'Updated', 'Re-Opened', 'Validated', 'Complete']
    status_summary_df = category_df.groupby(['AC', 'Status']).size().unstack(fill_value=0).reindex(columns=status_categories, fill_value=0).reset_index()

    status_summary_file_path = os.path.join(output_folder, f"{original_file_name.split('.')[0]}_{category}_status.xlsx")
    status_summary_df.to_excel(status_summary_file_path, index=False)

    # Totals Summary for the category
    total_validate = category_df[category_df['PROPOSED_ACTION'] == 'VALIDATE_EFFECTIVITY'].shape[0]
    total_add = category_df[category_df['PROPOSED_ACTION'] == 'ADD_EFFECTIVITY'].shape[0]
    total_status = category_df['Status'].value_counts().reindex(status_categories, fill_value=0).to_dict()

    totals_df = pd.DataFrame({
        'Add Effectivity': [total_add],
        'Validate Effectivity': [total_validate]
    })

    for status in status_categories:
        totals_df[status] = [total_status[status]]

    category_totals_file_path = os.path.join(output_folder, f"{original_file_name.split('.')[0]}_{category}_totals.xlsx")
    totals_df.to_excel(category_totals_file_path, index=False)

    return action_summary_file_path, status_summary_file_path, category_totals_file_path

# Create summaries for each category
for category in categories:
    action_summary_file_path, status_summary_file_path, category_totals_file_path = create_category_summaries(category)
    print(f"Summary files for category '{category}' have been created:")
    print(f" - {action_summary_file_path}")
    print(f" - {status_summary_file_path}")
    print(f" - {category_totals_file_path}")

# Summary for all records by Action
all_action_summary_df = pd.DataFrame()
all_action_summary_df['AC'] = open_parts_df['AC'].unique()

def count_action(ac_value, action):
    return len(open_parts_df[(open_parts_df['AC'] == ac_value) & (open_parts_df['PROPOSED_ACTION'] == action)])

all_action_summary_df['Add Effectivity'] = all_action_summary_df['AC'].apply(lambda x: count_action(x, 'ADD_EFFECTIVITY'))
all_action_summary_df['Validate Effectivity'] = all_action_summary_df['AC'].apply(lambda x: count_action(x, 'VALIDATE_EFFECTIVITY'))
all_action_summary_df['TOTAL'] = all_action_summary_df['Add Effectivity'] + all_action_summary_df['Validate Effectivity']

all_action_summary_file_path = os.path.join(output_folder, original_file_name.split('.')[0] + '_all_action.xlsx')
all_action_summary_df.to_excel(all_action_summary_file_path, index=False)

# Summary for all records by Status
status_categories = ['Initial', 'In-Work', 'Issue', 'Updated', 'Re-Opened', 'Validated', 'Complete']
all_status_summary_df = df.groupby(['AC', 'Status']).size().unstack(fill_value=0).reindex(columns=status_categories, fill_value=0).reset_index()

all_status_summary_file_path = os.path.join(output_folder, original_file_name.split('.')[0] + '_all_status.xlsx')
all_status_summary_df.to_excel(all_status_summary_file_path, index=False)

# Totals Sheet
total_validate = df[df['PROPOSED_ACTION'] == 'VALIDATE_EFFECTIVITY'].shape[0]
total_add = df[df['PROPOSED_ACTION'] == 'ADD_EFFECTIVITY'].shape[0]
total_status = df['Status'].value_counts().reindex(status_categories, fill_value=0).to_dict()

# Count each category in the 'CATEGORY' column
category_counts = df['CATEGORY'].value_counts().reindex(categories, fill_value=0).to_dict()

totals_df = pd.DataFrame({
    'Add Effectivity': [total_add],
    'Validate Effectivity': [total_validate]
})

for status in status_categories:
    totals_df[status] = [total_status[status]]

for category in categories:
    totals_df[category] = [category_counts[category]]

totals_file_path = os.path.join(output_folder, original_file_name.split('.')[0] + '_totals.xlsx')
totals_df.to_excel(totals_file_path, index=False)

print(f"Summary files have been created in the '{output_folder}' folder:")
print(f" - {all_action_summary_file_path}")
print(f" - {all_status_summary_file_path}")
print(f" - {totals_file_path}")
