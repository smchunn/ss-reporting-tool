import os
import polars as pl
import math

# Define paths
input_folder = "/Users/silas.bash/Library/CloudStorage/OneDrive-MMC/SmartSheet_API/DEMO_interchangeability/interchangeability_reports"
output_folder = "/Users/silas.bash/Library/CloudStorage/OneDrive-MMC/SmartSheet_API/DEMO_interchangeability/split"

# Create the output directory if it doesn't exist
os.makedirs(output_folder, exist_ok=True)

# Max records per file
MAX_RECORDS = 5000

# Iterate over all Excel files in the input folder
for file_name in os.listdir(input_folder):
    if file_name.endswith(".xlsx"):
        input_file = os.path.join(input_folder, file_name)

        # Read the Excel file (first sheet)
        _, df = pl.read_excel(input_file, sheet_id=0).popitem()

        # Group the data by the 'CATEGORY' column
        grouped = df.group_by("CATEGORY")

        # Iterate over each group and save to new Excel files
        for category_value, group in grouped:
            # Handle tuple values (if group key is a tuple)
            if isinstance(category_value, tuple):
                category_value = category_value[0]

            # Calculate the number of splits needed
            num_rows = group.height
            num_files = math.ceil(num_rows / MAX_RECORDS)

            for i in range(num_files):
                start_idx = i * MAX_RECORDS
                end_idx = min((i + 1) * MAX_RECORDS, num_rows)
                chunk = group.slice(start_idx, end_idx - start_idx)

                # Format file counter as two digits
                file_counter = f"{i+1:02d}"

                # Construct output file name as requested
                output_file = os.path.join(
                    output_folder, 
                    f"INTERCHG_{category_value}_{file_counter}.xlsx"
                )

                # Write the chunk to Excel
                chunk.write_excel(output_file, include_header=True)

print("Splitting complete.")