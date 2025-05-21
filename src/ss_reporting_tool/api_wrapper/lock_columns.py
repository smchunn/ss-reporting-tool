from ss_reporting_tool.Config import Config
from ss_reporting_tool.Report import Report
from ss_reporting_tool.Utils import threader
import ss_api
import polars as pl
from polars import col, lit
from typing import List


def lock_columns(cfg: Config, tables: List):

    def _lock_columns(table):
        print(f"Locking columns for table: {table.name} (ID: {table.id})")

        # Retrieve the columns from the specified sheet
        columns = ss_api.get_columns(sheet_id=table.id)
        if isinstance(columns, dict):
            columns = columns.get("data", None)
        if not columns:
            print(f"Error getting columns for '{table.name} (ID: {table.id})'")
            return

        # Prepare updates for locking columns except for "Status," "Assignment," and "Notes"
        updates = {}
        excluded_columns = {
            "Status",
            "Assignment",
            "Notes",
        }  # Set of columns to exclude
        if isinstance(columns, list):
            for col in columns:
                if isinstance(col, dict) and "title" in col:
                    title = col["title"]
                    # Check if the column title is not in the excluded list
                    if title not in excluded_columns:
                        id = col["id"]
                        updates[id] = {
                            "title": title,
                            "locked": True,  # Set the locked attribute to True
                        }
                        print(f"Column '{title}' (ID: {id}) will be locked.")

        # Apply the updates to lock the specified columns
        for id, update in updates.items():
            ss_api.update_columns(sheet_id=table.id, column_id=id, column_update=update)

        print(f"Columns locked for table: {table.name}")

    print("Locking columns ...")
    threader(_lock_columns, tables, cfg.threadcount)
