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
        
        # Create new columns with default values
        df.insert(0, 'Status', 'Initial')
        df.insert(1, 'Assignment', '')
        df.insert(2, 'Notes', '')
        df.insert(3, 'Created Date', today_date)
        df.insert(4, 'Modified Date', today_date)
        
        # Save the modified DataFrame to a new Excel file in the output directory
        output_file_path = os.path.join(output_dir, filename)
        df.to_excel(output_file_path, index=False)

print("Files have been processed and saved to the output directory.")
