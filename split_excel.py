import os
import pandas as pd

# Define paths
input_folder = 'Effectivity Reports'
output_folder = 'Effectivity_Reports_Split'

# Create the output directory if it doesn't exist
os.makedirs(output_folder, exist_ok=True)

# Iterate over all Excel files in the input folder
for file_name in os.listdir(input_folder):
    if file_name.endswith('.xlsx'):
        input_file = os.path.join(input_folder, file_name)
        
        # Load the Excel file and read the first sheet
        df = pd.read_excel(input_file, sheet_name=0)

        # Group the data by the 'AC' column
        grouped = df.groupby('AC')

        # Get the base name without extension
        base_name = os.path.splitext(file_name)[0]

        # Iterate over each group and save to a new Excel file
        for ac_value, group in grouped:
            output_file = os.path.join(output_folder, f'{base_name}_{ac_value}.xlsx')
            group.to_excel(output_file, index=False)

print("Splitting complete.")
