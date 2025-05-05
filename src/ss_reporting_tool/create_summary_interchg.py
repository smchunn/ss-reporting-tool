import os
import pandas as pd

def summarize_excel_folder(input_folder, output_folder):
    # Ensure output folder exists
    os.makedirs(output_folder, exist_ok=True)
    
    # Collect all Excel files in the input folder
    excel_files = [f for f in os.listdir(input_folder) if f.endswith('.xlsx') or f.endswith('.xls')]
    
    # Read and concatenate all data
    all_data = []
    for file in excel_files:
        file_path = os.path.join(input_folder, file)
        df = pd.read_excel(file_path, dtype=str)
        all_data.append(df[['CATEGORY', 'PROPOSED_ACTION', 'STATUS']])
    
    data = pd.concat(all_data, ignore_index=True)
    data.fillna('MISSING', inplace=True)
    
    # Define the desired status order
    status_order = [
        'Initial', 'Assigned', 'In-Work', 'Issue', 'Updated', 'Re-Opened', 'Validated', 'Complete'
    ]
    
    # Action Summary: Pivot table (CATEGORY x PROPOSED_ACTION)
    action_summary = pd.pivot_table(
        data,
        index='CATEGORY',
        columns='PROPOSED_ACTION',
        aggfunc='size',
        fill_value=0
    )
    action_summary.reset_index(inplace=True)
    action_summary.columns.name = None
    
    # Status Summary: Pivot table (CATEGORY x STATUS)
    status_summary = pd.pivot_table(
        data,
        index='CATEGORY',
        columns='STATUS',
        aggfunc='size',
        fill_value=0
    )
    # Reindex columns to match desired status order, fill missing with 0
    status_columns = [col for col in status_order if col in status_summary.columns]
    status_summary = status_summary.reindex(columns=status_columns, fill_value=0)
    status_summary.reset_index(inplace=True)
    status_summary.columns.name = None
    
    # Write Action Summary to its own workbook
    action_output_path = os.path.join(output_folder, 'SUMMARY_ACTION.xlsx')
    with pd.ExcelWriter(action_output_path, engine='xlsxwriter') as writer:
        action_summary.to_excel(writer, sheet_name='Action_Summary', index=False)
    
    # Write Status Summary to its own workbook
    status_output_path = os.path.join(output_folder, 'SUMMARY_STATUS.xlsx')
    with pd.ExcelWriter(status_output_path, engine='xlsxwriter') as writer:
        status_summary.to_excel(writer, sheet_name='Status_Summary', index=False)
    
    # Prepare Totals Summary
    unique_actions = sorted(data['PROPOSED_ACTION'].unique())
    # Use only statuses present in the data and in the desired order
    unique_statuses = [status for status in status_order if status in data['STATUS'].unique()]
    
    action_counts = data['PROPOSED_ACTION'].value_counts().reindex(unique_actions, fill_value=0)
    status_counts = data['STATUS'].value_counts().reindex(unique_statuses, fill_value=0)
    
    # Build the totals DataFrame
    columns = ['Type'] + unique_actions + unique_statuses
    # Row for actions
    action_row = ['PROPOSED_ACTION'] + list(action_counts.values) + [0]*len(unique_statuses)
    # Row for statuses
    status_row = ['STATUS'] + [0]*len(unique_actions) + list(status_counts.values)
    
    totals_data = [action_row, status_row]
    totals_df = pd.DataFrame(totals_data, columns=columns)
    
    # Write Totals Summary to its own workbook
    totals_output_path = os.path.join(output_folder, 'SUMMARY_TOTALS.xlsx')
    with pd.ExcelWriter(totals_output_path, engine='xlsxwriter') as writer:
        totals_df.to_excel(writer, sheet_name='Totals_Summary', index=False)

# Example usage:
input_folder = r'/Users/silas.bash/Library/CloudStorage/OneDrive-MMC/SmartSheet_API/DEMO_interchangeability/data'   # Replace with your input folder path
output_folder = r'/Users/silas.bash/Library/CloudStorage/OneDrive-MMC/SmartSheet_API/DEMO_interchangeability/summary' # Replace with your output folder path

summarize_excel_folder(input_folder, output_folder)