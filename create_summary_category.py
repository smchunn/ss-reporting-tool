import pandas as pd
import os

# Define the input and output folders
input_folder = './data'
output_folder = './import'

# Get the list of Excel files in the input folder
files = [f for f in os.listdir(input_folder) if f.endswith('.xlsx')]

# Check if there are any files in the input folder
if not files:
    raise Exception("The input folder should contain at least one Excel file.")

# Load and concatenate all Excel files into a single DataFrame
df_list = []
for file in files:
    file_path = os.path.join(input_folder, file)
    df = pd.read_excel(file_path)
    df_list.append(df)

# Concatenate all DataFrames
df = pd.concat(df_list, ignore_index=True)

# Update the status to 'Validated' if 'FEEDBACK' column has a non-blank value
df.loc[df['FEEDBACK'].notna() & (df['FEEDBACK'] != ''), 'Status'] = 'Validated'

# Filter out rows where the status is 'Validated' or 'Complete'
open_parts_df = df[~df['Status'].isin(['Validated', 'Complete'])]

# Ensure the output folder exists
os.makedirs(output_folder, exist_ok=True)

# Get unique fleets from the DataFrame
fleets = df['FLEET'].unique()

# Define categories and group specific ones into "OTHER"
categories = df['CATEGORY'].unique()
other_categories = ['GEN-CON', 'KIT', 'SOFTWARE']
categories = [cat if cat not in other_categories else 'OTHER' for cat in categories]

# Function to create summaries for each fleet and category
def create_fleet_category_summaries(fleet, category):
    fleet_category_df = df[(df['FLEET'] == fleet) & (df['CATEGORY'] == category)]
    open_fleet_category_df = open_parts_df[(open_parts_df['FLEET'] == fleet) & (open_parts_df['CATEGORY'] == category)]

    # First Summary: Summary by Action (only for open parts)
    action_summary_df = pd.DataFrame()
    action_summary_df['AC'] = open_fleet_category_df['AC'].unique()

    def count_action(ac_value, action):
        return len(open_fleet_category_df[(open_fleet_category_df['AC'] == ac_value) & (open_fleet_category_df['PROPOSED_ACTION'] == action)])

    action_summary_df['Add Effectivity'] = action_summary_df['AC'].apply(lambda x: count_action(x, 'ADD_EFFECTIVITY'))
    action_summary_df['Validate Effectivity'] = action_summary_df['AC'].apply(lambda x: count_action(x, 'VALIDATE_EFFECTIVITY'))
    action_summary_df['TOTAL'] = action_summary_df['Add Effectivity'] + action_summary_df['Validate Effectivity']

    action_summary_file_path = os.path.join(output_folder, f"{fleet}_{category}_ACTION.xlsx")
    action_summary_df.to_excel(action_summary_file_path, index=False)

    # Second Summary: Summary by Status
    status_categories = ['Initial', 'In-Work', 'Issue', 'Updated', 'Re-Opened', 'Validated', 'Complete']
    status_summary_df = fleet_category_df.groupby(['AC', 'Status']).size().unstack(fill_value=0).reindex(columns=status_categories, fill_value=0).reset_index()

    status_summary_file_path = os.path.join(output_folder, f"{fleet}_{category}_STATUS.xlsx")
    status_summary_df.to_excel(status_summary_file_path, index=False)

    # Totals Summary for the fleet and category
    total_validate = fleet_category_df[fleet_category_df['PROPOSED_ACTION'] == 'VALIDATE_EFFECTIVITY'].shape[0]
    total_add = fleet_category_df[fleet_category_df['PROPOSED_ACTION'] == 'ADD_EFFECTIVITY'].shape[0]
    total_status = fleet_category_df['Status'].value_counts().reindex(status_categories, fill_value=0).to_dict()

    totals_df = pd.DataFrame({
        'Add Effectivity': [total_add],
        'Validate Effectivity': [total_validate]
    })

    for status in status_categories:
        totals_df[status] = [total_status[status]]

    category_totals_file_path = os.path.join(output_folder, f"{fleet}_{category}_TOTALS.xlsx")
    totals_df.to_excel(category_totals_file_path, index=False)

    return action_summary_file_path, status_summary_file_path, category_totals_file_path

# Create summaries for each fleet and category
for fleet in fleets:
    for category in set(categories):  # Use set to avoid duplicates
        create_fleet_category_summaries(fleet, category)

# Delete the original Excel files in the input folder
for file in files:
    file_path = os.path.join(input_folder, file)
    os.remove(file_path)
    print(f"Deleted file: {file_path}")

print(f"All summary files have been created in the '{output_folder}' folder, and original files have been deleted from '{input_folder}'.")
