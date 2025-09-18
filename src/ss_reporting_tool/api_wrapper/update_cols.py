from ss_reporting_tool.Config import Config
from ss_reporting_tool.Utils import threader
import ss_api
import polars as pl
from typing import List

def update_cols(cfg: Config, tables: List):
    """
    Updates the columns MFR, IPC_CHAPTER, IPC_SECTION, IPC_KWD in each sheet
    with values from an Excel file, joining on PNR (Excel) and PN (Smartsheet).
    Excel columns: MFR, CHAPNBR, SECTNBR, KWD
    Smartsheet columns: MFR, IPC_CHAPTER, IPC_SECTION, IPC_KWD
    """

    # Read Excel into Polars DataFrame
    excel_df = pl.read_excel('/Users/silas.bash/Library/CloudStorage/OneDrive-MMC/SmartSheet_API/ACA/data/IPC_PN_DATA.xlsx')
    # Rename for consistency
    excel_df = excel_df.rename({
        "PNR": "PNR",
        "MFR": "MFR",
        "CHAPNBR": "CHAPNBR",
        "SECTNBR": "SECTNBR",
        "KWD": "KWD"
    })

    def _update_cols(table):
        print(f"Updating table: {table.name} (ID: {table.id})")

        # Get columns metadata
        columns = ss_api.get_columns(sheet_id=table.id)
        if isinstance(columns, dict):
            columns = columns.get("data", None)
        if not columns:
            print(f"Error getting columns for '{table.name} (ID: {table.id})'")
            return

        # Build mapping from title to id
        col_title_to_id = {col['title']: col['id'] for col in columns if 'title' in col and 'id' in col}
        required_cols = ["PN", "MFR", "IPC_CHAPTER", "IPC_SECTION", "IPC_KWD"]
        missing = [c for c in required_cols if c not in col_title_to_id]
        if missing:
            print(f"Missing columns {missing} in '{table.name}'")
            return

        # Get sheet rows
        rows = ss_api.get_rows(sheet_id=table.id)
        if isinstance(rows, dict):
            rows = rows.get("data", None)
        if not rows:
            print(f"Error getting rows for '{table.name} (ID: {table.id})'")
            return

        # Build a DataFrame from Smartsheet rows
        smartsheet_data = []
        for row in rows:
            row_data = {"row_id": row["id"]}
            for cell in row.get("cells", []):
                col_id = cell.get("column_id")
                if col_id in col_title_to_id.values():
                    # Find the title for this column id
                    title = [k for k, v in col_title_to_id.items() if v == col_id][0]
                    row_data[title] = cell.get("value")
            smartsheet_data.append(row_data)
        if not smartsheet_data:
            print(f"No data rows in '{table.name}'")
            return
        ss_df = pl.DataFrame(smartsheet_data)

        # Join on PN (Smartsheet) and PNR (Excel)
        if "PN" not in ss_df.columns:
            print(f"PN column missing in Smartsheet data for '{table.name}'")
            return
        join_df = ss_df.join(
            excel_df,
            left_on="PN",
            right_on="PNR",
            how="inner"
        )

        # Prepare updates per row
        updates = []
        for row in join_df.iter_rows(named=True):
            update_cells = []
            # Only update if Excel value is not null
            if row.get("MFR") is not None:
                update_cells.append({
                    "column_id": col_title_to_id["MFR"],
                    "value": row["MFR"]
                })
            if row.get("CHAPNBR") is not None:
                update_cells.append({
                    "column_id": col_title_to_id["IPC_CHAPTER"],
                    "value": row["CHAPNBR"]
                })
            if row.get("SECTNBR") is not None:
                update_cells.append({
                    "column_id": col_title_to_id["IPC_SECTION"],
                    "value": row["SECTNBR"]
                })
            if row.get("KWD") is not None:
                update_cells.append({
                    "column_id": col_title_to_id["IPC_KWD"],
                    "value": row["KWD"]
                })
            if update_cells:
                updates.append({
                    "row_id": row["row_id"],
                    "cells": update_cells
                })

        # Apply updates via ss_api
        for upd in updates:
            ss_api.update_row(
                sheet_id=table.id,
                row_id=upd["row_id"],
                cells=upd["cells"]
            )

        print(f"Updated {len(updates)} rows in '{table.name}'")

    print("Updating columns from Excel ...")
    threader(_update_cols, tables, cfg.threadcount)