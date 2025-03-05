import os
import polars as pl

# Define paths
input_folder = "smartsheet"
output_folder = "smartsheet_split"

# Create the output directory if it doesn't exist
os.makedirs(output_folder, exist_ok=True)

# Iterate over all Excel files in the input folder
for file_name in os.listdir(input_folder):
    if file_name.endswith(".xlsx"):
        input_file = os.path.join(input_folder, file_name)

        _, df = pl.read_excel(input_file, sheet_id=0).popitem()

        # Group the data by the 'AC' column
        grouped = df.group_by("AC")

        # Get the base name without extension
        base_name = os.path.splitext(file_name)[0]

        # Iterate over each group and save to a new Excel file
        for ac_value, group in grouped:
            # Check if ac_value is a tuple and extract the first element
            if isinstance(ac_value, tuple):
                ac_value = ac_value[0]

            output_file = os.path.join(output_folder, f"{base_name}_AC{ac_value}.xlsx")
            group.write_excel(output_file, include_header=True)

print("Splitting complete.")
