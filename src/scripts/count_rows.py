import os
import pandas as pd

def count_rows_in_excel_files(folder_path):
    category_count = 0
    ac_count = 0

    # Define the paths for Category and AC folders
    category_folder = os.path.join(folder_path, 'Category')
    ac_folder = os.path.join(folder_path, 'AC')

    # Function to count rows in Excel files in a given folder
    def count_rows_in_folder(folder):
        total_rows = 0
        try:
            for file_name in os.listdir(folder):
                if file_name.endswith('.xlsx'):
                    file_path = os.path.join(folder, file_name)
                    try:
                        # Read the Excel file
                        xls = pd.ExcelFile(file_path)
                        # Sum the rows in all sheets
                        for sheet_name in xls.sheet_names:
                            df = pd.read_excel(xls, sheet_name)
                            total_rows += df.shape[0]
                    except Exception as e:
                        print(f"Error reading {file_path}: {e}")
        except PermissionError:
            print(f"Permission denied: {folder}")
        except Exception as e:
            print(f"Error accessing {folder}: {e}")
        return total_rows

    # Count rows in Category and AC folders
    if os.path.exists(category_folder):
        category_count = count_rows_in_folder(category_folder)
    if os.path.exists(ac_folder):
        ac_count = count_rows_in_folder(ac_folder)

    return category_count, ac_count

def main():
    # Relative paths to each parent folder
    parent_folders = [
        os.path.join(os.getcwd(), './A319'),  # Replace with your folder name
        os.path.join(os.getcwd(), './A320'), # Replace with your folder name
        os.path.join(os.getcwd(), './A321')    # Replace with your folder name
    ]

    for folder in parent_folders:
        if os.path.exists(folder):
            category_count, ac_count = count_rows_in_excel_files(folder)
            print(f"Folder: {folder}")
            print(f"Total rows in 'Category': {category_count}")
            print(f"Total rows in 'AC': {ac_count}")
            print()
        else:
            print(f"Folder does not exist: {folder}")

if __name__ == "__main__":
    main()
