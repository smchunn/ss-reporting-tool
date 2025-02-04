import os
import pandas as pd
from datetime import datetime

# Define input and output directories
input_dir = 'Effectivity_Reports_Split'
output_dir = 'Effectivity_Reports_Mod'

# Ensure the output directory exists
os.makedirs(output_dir, exist_ok=True)

# Get today's date in the desired format
today_date = datetime.now().strftime('%Y-%m-%d')

# Iterate over all Excel files in the input directory
for filename in os.listdir(input_dir):
    if filename.endswith('.xlsx'):
        # Read the Excel file
        file_path = os.path.join(input_dir, filename)
        df = pd.read_excel(file_path)
        
        # Delete the first column
        df = df.iloc[:, 1:]  # Keep all columns except the first one
        
        # Insert new columns after the first column (now the original second column)
        df.insert(1, 'Status', 'Initial')  # Insert at index 1
        df.insert(2, 'Assignment', '')    # Insert at index 2
        df.insert(3, 'Notes', '')         # Insert at index 3
        df.insert(4, 'Created Date', today_date)  # Insert at index 4
        df.insert(5, 'Modified Date', today_date)  # Insert at index 5
        
        # Update 'Status' to 'Complete' if 'FEEDBACK' column is not blank
        df.loc[df['FEEDBACK'].notna() & (df['FEEDBACK'] != ''), 'Status'] = 'Validated'
        
        # Save the modified DataFrame to a new Excel file in the output directory
        output_file_path = os.path.join(output_dir, filename)
        df.to_excel(output_file_path, index=False)

print("Files have been processed and saved to the output directory.")
