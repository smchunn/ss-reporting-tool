from ss_reporting_tool.Config import Config
from ss_reporting_tool.Report import Report
from ss_reporting_tool.Utils import threader
import ss_api
import pandas as pd
import logging
import os
from typing import Optional
import json


def update_column(cfg: Config, reports):
    settings_dir = cfg.settings_dir
    json_path = os.path.join(settings_dir, "update_columns.json")
    try:
        with open(json_path, "r") as f:
            update_columns = json.load(f)
    except Exception as e:
        print(f"Error loading update columns from {json_path}: {e}")
        update_columns = []

    def _update_column(report, update_column_name):
        if not report.src or not os.path.exists(report.src):
            print(f"Excel file not found: {report.src}")
            return

        try:
            df = pd.read_excel(report.src, dtype=str)
        except Exception as e:
            print(f"Failed to read Excel file {report.src}: {e}")
            return

        if not report.match_column or not update_column_name:
            print(f"Report {report.name} missing match_column or update_column")
            return

        if report.match_column not in df.columns or update_column_name not in df.columns:
            print(f"Excel file must contain columns '{report.match_column}' and '{update_column_name}'")
            return

        excel_lookup = df.set_index(report.match_column)[update_column_name].to_dict()

        sheet = ss_api.get_sheet(report.id)
        if not sheet or "rows" not in sheet:
            print(f"Failed to retrieve sheet or no rows found for sheet ID {report.id}")
            return

        columns_data = ss_api.get_columns(report.id)
        if not columns_data or "data" not in columns_data:
            print(f"Failed to retrieve columns for sheet ID {report.id}")
            return

        column_name_to_id = {col["title"]: col["id"] for col in columns_data["data"]}
        if report.match_column not in column_name_to_id or update_column_name not in column_name_to_id:
            print(f"Sheet must contain columns '{report.match_column}' and '{update_column_name}'")
            return

        match_col_id = column_name_to_id[report.match_column]
        update_col_id = column_name_to_id[update_column_name]

        updates = []
        for row in sheet["rows"]:
            match_value = None
            for cell in row.get("cells", []):
                if cell.get("columnId") == match_col_id:
                    match_value = str(cell.get("value", "")).strip()
                    break

            if not match_value:
                continue

            if match_value in excel_lookup:
                new_value = excel_lookup[match_value]
                if pd.isna(new_value):
                    new_value = None
                update_row = {
                    "id": row["id"],
                    "cells": [
                        {
                            "columnId": update_col_id,
                            "value": new_value,
                        }
                    ],
                }
                updates.append(update_row)

        if not updates:
            print(f"No matching rows found to update for report {report.name} and column {update_column_name}.")
            return

        batch_size = 500
        for i in range(0, len(updates), batch_size):
            batch = updates[i : i + batch_size]
            ss_api.update_sheet(report.id, batch, batch_size=batch_size)
            print(f"Updated batch {i // batch_size + 1} with {len(batch)} rows for report {report.name} and column {update_column_name}.")

    print("Starting column update from Excel...")
    for update_col in update_columns:
        print(f"Updating column: {update_col}")
        threader(lambda report: _update_column(report, update_col), reports, cfg.threadcount)
