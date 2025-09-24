from ss_reporting_tool.Config import Config
from ss_reporting_tool.Report import Report
from ss_reporting_tool.Utils import threader
import ss_api
import polars as pl
from polars import col, lit
from typing import List
import json
import os

def update_col_type(cfg: Config, tables: List):

    def _update_col_type(table):
        print(f"Updating columns for table: {table.name} (ID: {table.id})")

        settings_dir = cfg.settings_dir
        json_path = os.path.join(settings_dir, "column_types.json")
        try:
            with open(json_path, "r") as f:
                column_updates = json.load(f)
        except Exception as e:
            print(f"Error loading column types from {json_path}: {e}")
            column_updates = {}

        columns = ss_api.get_columns(sheet_id=table.id)
        if isinstance(columns, dict):
            columns = columns.get("data", None)
        if not columns:
            print(f"error getting columns for '{table.name} (ID: {table.id})'")

        updates = {}
        if isinstance(columns, list):
            for col in columns:
                if isinstance(col, dict) and "title" in col:
                    id = col["id"]
                    title = col["title"]
                    # use specific update if it exists
                    if title in column_updates:
                        updates[id] = {"title": title}
                        updates[id].update(column_updates[title])

                    # Default update to TEXT_NUMBER
                    else:
                        updates[id] = {
                            "title": title,
                            "type": "TEXT_NUMBER",
                        }
        for id, update in updates.items():
            ss_api.update_columns(sheet_id=table.id, column_id=id, column_update=update)

        print(f"Columns updated for table: {table.name}")

    print("Updating columns ...")
    threader(_update_col_type, tables, cfg.threadcount)
