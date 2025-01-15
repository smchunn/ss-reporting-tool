import os
import pandas as pd

# Define paths
input_folder = 'Effectivity Reports'
output_folder = 'Effectivity_Reports_Split'
input_file = os.path.join(input_folder, 'EFFECTIVITY_REPORT_STANDARD_A320_20250114.xlsx')
sheet_name = 'EFFECTIVITY'

# Create the output directory if it doesn't exist
os.makedirs(output_folder, exist_ok=True)

# Load the Excel file
df = pd.read_excel(input_file, sheet_name=sheet_name)

# Group the data by the 'AC' column
grouped = df.groupby('AC')

# Iterate over each group and save to a new Excel file
for ac_value, group in grouped:
    output_file = os.path.join(output_folder, f'ERS_A320_{ac_value}_20250114.xlsx')
    group.to_excel(output_file, index=False, sheet_name=sheet_name)

print("Splitting complete.")
