import sys
import os
import pandas as pd

# Usage: python join_pn_data.py /path/to/folder


folder = sys.argv[1]
input_files = [
    'OTHER.xlsx',
    'XPENDBL_ATA_00_26.xlsx',
    'XPENDBL_ATA_27_99.xlsx'
]
ipc_file = 'IPC_PN_DATA.xlsx'



# Load and prepare IPC PN DATA
ipc_path = os.path.join(folder, ipc_file)
ipc_df = pd.read_excel(ipc_path, dtype=str)  # Force all columns as string
ipc_df = ipc_df.rename(columns={
    'PNR': 'PN',
    'CHAPNBR': 'IPC_CHAPTER',
    'SECTNBR': 'IPC_SECTION',
    'KWD': 'IPC_KWD'
})
ipc_df = ipc_df[['PN', 'MFR', 'IPC_CHAPTER', 'IPC_SECTION', 'IPC_KWD']]


df_csv = pd.read_excel(ipc_path, dtype=str)
print(df_csv['KWD'].head(10))


for fname in input_files:
    in_path = os.path.join(folder, fname)
    out_path = os.path.join(folder, fname.replace('.xlsx', '_with_ipc_data.xlsx'))
    df = pd.read_excel(in_path, dtype=str)  # Force all columns as string
    merged = pd.merge(df, ipc_df, how='left', on='PN')
    merged.to_excel(out_path, index=False, engine='openpyxl')
    print(f"Output saved to {out_path}")