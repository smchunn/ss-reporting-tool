from ss_reporting_tool.Config import Config
from ss_reporting_tool.Report import Report
from ss_reporting_tool.Utils import threader
import ss_api
import polars as pl
from polars import col, lit
from typing import List
import json
import os


def update_col_desc(cfg: Config, tables: List):

    def _update_col_desc(table):
        print(f"Updating column descriptions for table: {table.name} (ID: {table.id})")

        settings_dir = cfg.settings_dir
        json_path = os.path.join(settings_dir, "column_descriptions.json")
        try:
            with open(json_path, "r") as f:
                column_descriptions = json.load(f)
        except Exception as e:
            print(f"Error loading column descriptions from {json_path}: {e}")
            column_descriptions = {}

        columns = ss_api.get_columns(sheet_id=table.id)
        if isinstance(columns, dict):
            columns = columns.get("data", None)
        if not columns:
            print(f"Error getting columns for '{table.name} (ID: {table.id})'")
            return

        for col in columns:
            if isinstance(col, dict) and "title" in col:
                title = col["title"]
                col_id = col["id"]
                if title in column_descriptions:
                    new_description = column_descriptions[title]
                    ss_api.update_column_description(
                        sheet_id=table.id,
                        column_id=col_id,
                        new_description=new_description,
                    )

        print(f"Column descriptions updated for table: {table.name}")

    print("Updating column descriptions ...")
    threader(_update_col_desc, tables, cfg.threadcount)
