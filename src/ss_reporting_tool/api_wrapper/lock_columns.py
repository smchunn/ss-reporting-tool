from ss_reporting_tool.Config import Config
from ss_reporting_tool.Report import Report
from ss_reporting_tool.Utils import threader
import ss_api
import polars as pl
from polars import col, lit
from typing import List
import json
import os

def lock_columns(cfg: Config, tables: List):

    def _lock_columns(table):
        print(f"Locking columns for table: {table.name} (ID: {table.id})")

        settings_dir = cfg.settings_dir
        json_path = os.path.join(settings_dir, "lock_columns_excluded.json")
        try:
            with open(json_path, "r") as f:
                excluded_columns = set(json.load(f))
        except Exception as e:
            print(f"Error loading excluded columns from {json_path}: {e}")
            excluded_columns = set()

        # Retrieve the columns from the specified sheet
        columns = ss_api.get_columns(sheet_id=table.id)
        if isinstance(columns, dict):
            columns = columns.get("data", None)
        if not columns:
            print(f"Error getting columns for '{table.name} (ID: {table.id})'")
            return

        updates = {}
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
