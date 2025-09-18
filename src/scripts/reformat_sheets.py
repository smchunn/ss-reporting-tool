import os
import pandas as pd
import shutil

# Define the directories
data_dir = 'data'
working_dir = 'working'
import_dir = 'import'

# Step 1: Copy all xlsx files from "data" to "working"
if not os.path.exists(working_dir):
    os.makedirs(working_dir)

for file in os.listdir(data_dir):
    if file.endswith('.xlsx'):
        src = os.path.join(data_dir, file)
        dst = os.path.join(working_dir, file)
        shutil.copy(src, dst)

# Step 2: Create fleet_unsorted.xlsx with all rows from every xlsx file in "working"
all_data = []

for file in os.listdir(working_dir):
 if file.endswith('.xlsx'):
        df = pd.read_excel(os.path.join(working_dir, file))
        if not df.empty:
            all_data.append(df)
        else:
            print(f"Warning: {file} is empty and will be skipped.")

# Concatenate all dataframes
fleet_unsorted = pd.concat(all_data, ignore_index=True)

# Check for required columns
required_columns = ['Status', 'Created Date', 'Modified Date', 'CATEGORY', 'PN', 'MAIN_PN', 'AC', 'FLEET']
missing_columns = [col for col in required_columns if col not in fleet_unsorted.columns]

if missing_columns:
    raise KeyError(f"Missing columns in the data: {', '.join(missing_columns)}")

# Step 3: Set Status column to "Initial" where it's blank
fleet_unsorted['Status'] = fleet_unsorted['Status'].fillna('Initial')

# Step 4: Set Created Date and Modified Date columns to 02/18/25 as text
fleet_unsorted['Created Date'] = '02/18/25'
fleet_unsorted['Modified Date'] = '02/18/25'

# Save the unsorted data in the working directory
fleet_unsorted.to_excel(os.path.join(working_dir, 'fleet_unsorted.xlsx'), index=False)

# Step 5: Create fleet_sorted.xlsx ordered by CATEGORY, PN, MAIN_PN, AC
fleet_sorted = fleet_unsorted.sort_values(by=['CATEGORY', 'PN', 'MAIN_PN', 'AC'])
fleet_sorted.to_excel(os.path.join(working_dir, 'fleet_sorted.xlsx'), index=False)


# Step 6: Split fleet_sorted.xlsx into multiple sheets
if not os.path.exists(import_dir):
    os.makedirs(import_dir)

# Group by FLEET and CATEGORY
grouped = fleet_sorted.groupby(['FLEET', 'CATEGORY'])

# Iterate through each group
for (fleet, category), group in grouped:
    # Initialize a list to hold the current sheet's data
    current_sheet = []
    current_row_count = 0
    sheet_id = 1  # Start with the first sheet ID

    # Iterate through the group to ensure PN's are not split
    for pn, pn_group in group.groupby('PN'):
        # Check if adding this PN exceeds the limit
        if current_row_count + len(pn_group) > 19500:
            # Save the current sheet if it has data
            if current_sheet:
                combined_sheet = pd.concat(current_sheet, ignore_index=True)
                filename = f"{fleet}_{category}_{sheet_id:02d}.xlsx"
                combined_sheet.to_excel(os.path.join(import_dir, filename), index=False)
                sheet_id += 1  # Increment the sheet ID
            
            # Reset for the next sheet
            current_sheet = []
            current_row_count = 0
        
        # Add the current PN group to the current sheet
        current_sheet.append(pn_group)
        current_row_count += len(pn_group)

    # Save any remaining data in the current sheet
    if current_sheet:
        combined_sheet = pd.concat(current_sheet, ignore_index=True)
        filename = f"{fleet}_{category}_{sheet_id:02d}.xlsx"
        combined_sheet.to_excel(os.path.join(import_dir, filename), index=False)


# Step 7: Clear the working folder
if os.path.exists(working_dir):
    shutil.rmtree(working_dir)
