import os
import polars as pl
from polars import col, lit

from datetime import datetime

from polars.selectors import by_index

# Define input and output directories
input_dir = "smartsheet_split"
output_dir = "smartsheet_mod"

# Ensure the output directory exists
os.makedirs(output_dir, exist_ok=True)

# Get today's date in the desired format
today_date = datetime.now().strftime("%Y-%m-%d")

# Iterate over all Excel files in the input directory
for filename in os.listdir(input_dir):
    if filename.endswith(".xlsx"):
        # Read the Excel file
        file_path = os.path.join(input_dir, filename)
        df = pl.read_excel(file_path)


        # Delete the first column
        df = df.drop(by_index(0))  # Keep all columns except the first one

        # Insert new columns after the first column (now the original second column)
        df.insert_column(1, lit("Initial").alias("Status"))  # Insert at index 1
        df.insert_column(2, lit("").alias("Assignment"))
        df.insert_column(3, lit("").alias("Notes"))
        df.insert_column(4, lit(today_date).alias("Created Date"))
        df.insert_column(5, lit(today_date).alias("Modified Date"))

        # Update 'Status' to 'Validated' if 'FEEDBACK' column is not blank
        df = df.with_columns(
            pl.when((df["FEEDBACK"].is_not_null()) & (df["FEEDBACK"] != ""))
            .then(lit("Validated"))
            .otherwise(col("Status"))
            .alias("Status")
        )


        # Save the modified DataFrame to a new Excel file in the output directory
        output_file_path = os.path.join(output_dir, filename)
        df.write_excel(output_file_path, include_header=True)

print("Files have been processed and saved to the output directory.")

