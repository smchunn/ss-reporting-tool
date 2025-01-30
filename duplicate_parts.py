import pandas as pd

# Specify the path to your Excel file
file_path = 'Effectivity Reports/EFFECTIVITY_REPORT_STANDARD_A320_20250115.xlsx'

# Load the Excel file into a DataFrame
df = pd.read_excel(file_path)

# Check for duplicate rows based on columns 'AC' and 'PN'
duplicates = df[df.duplicated(subset=['AC', 'PN'], keep=False)]

# Specify the path for the new Excel file to save duplicates
output_file_path = 'Effectivity Reports/duplicate_rows.xlsx'

# Save the duplicate rows to a new Excel file
if not duplicates.empty:
    duplicates.to_excel(output_file_path, index=False)
    print(f"Duplicate rows have been saved to {output_file_path}")
else:
    print("No duplicate rows found based on columns 'AC' and 'PN'.")
