from ss_reporting_tool.Config import Config
from ss_reporting_tool.Report import Report
from ss_reporting_tool.Utils import threader
import ss_api
from typing import List

def add_cols(cfg: Config, tables: List):
    """
    Adds columns MFR, IPC_CHAPTER, IPC_SECTION, IPC_KWD
    as TEXT_NUMBER columns to each specified sheet.
    """
    print(12)
    def _add_cols(table: Report):
        print(f"Adding columns to table: {table.name} (ID: {table.id})")

        # Define the columns to add
        columns_to_add = [
            {"title": "MFR", "type": "TEXT_NUMBER"},
            {"title": "IPC_CHAPTER", "type": "TEXT_NUMBER"},
            {"title": "IPC_SECTION", "type": "TEXT_NUMBER"},
            {"title": "IPC_KWD", "type": "TEXT_NUMBER"},
        ]


        # Add new columns via ss_api
        result = ss_api.add_cols(sheet_id=table.id, columns=new_columns)
        if result and "data" in result:
            print(f"Added columns {[col['title'] for col in new_columns]} to table: {table.name}")
        else:
            print(f"Failed to add columns to table: {table.name}")

    print("Adding columns to sheets ...")
    threader(_add_cols, tables, cfg.threadcount)