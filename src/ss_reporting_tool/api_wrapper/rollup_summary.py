from ss_reporting_tool.Config import Config
from ss_reporting_tool.Summary import Summary
from ss_reporting_tool.Utils import threader
import os
import json
from typing import List
import ss_api

def rollup_summary(cfg: Config, tables: List[Summary]):
    """
    Wrapper function to create summary sheets in Smartsheet with each of the combinations
    in summary_settings.json. For each combination, creates a table where columns and rows
    correspond to the group_by fields, and cells contain counts (formulas left blank for now).

    Args:
        cfg (Config): Configuration object containing settings_dir and other config.
        tables (List[Summary]): List of Summary objects or tables to process.

    Returns:
        None
    """

    settings_path = os.path.join(cfg.settings_dir, "summary_settings.json")
    try:
        with open(settings_path, "r") as f:
            summary_settings = json.load(f)
    except Exception as e:
        print(f"Failed to load summary settings from {settings_path}: {e}")
        summary_settings = {}

    def _rollup_summary(table: Summary):
        if not hasattr(table, "metadata") or not isinstance(table.metadata, dict):
            table.metadata = {}
        table.metadata["settings_path"] = settings_path
        table.settings = summary_settings

        # Create or update the summary sheet in Smartsheet
        if not table.id:
            # Create new sheet with name and empty columns initially
            result = ss_api.create_sheet(table.name, [])
            if result and "result" in result:
                table.id = result["result"]["id"]
                print(f"Created new summary sheet with ID {table.id}")
            else:
                print("Failed to create summary sheet.")
                return
        else:
            print(f"Using existing summary sheet with ID {table.id}")

        # For each filter combination, create a section in the sheet
        for combo in summary_settings.get("filter_combinations", []):
            group_by = combo.get("group_by", [])
            metrics = combo.get("metrics", [])

            # Build columns: one for each group_by field value plus a header column
            columns = [{"title": group_by[0], "type": "TEXT_NUMBER"}] if group_by else []
            # For simplicity, assume first group_by field values come from parameters
            if group_by:
                first_group_values = summary_settings.get("parameters", {}).get(group_by[0], [])
                for val in first_group_values:
                    columns.append({"title": val, "type": "TEXT_NUMBER"})

            # Create or update columns in the sheet (placeholder, actual API calls needed)
            print(f"Creating columns for group_by {group_by}: {[col['title'] for col in columns]}")

            # Build rows: one for each value of second group_by field if exists
            rows = []
            if len(group_by) > 1:
                second_group_values = summary_settings.get("parameters", {}).get(group_by[1], [])
                for val in second_group_values:
                    # Each row starts with the row header (second group value)
                    row = {"cells": [{"columnId": None, "value": val}]}
                    # Add empty cells for each column (formulas to be added later)
                    for _ in first_group_values:
                        row["cells"].append({"columnId": None, "value": None})
                    rows.append(row)

            # Placeholder: Insert rows and columns into sheet via API (not implemented)
            print(f"Prepared {len(rows)} rows for group_by {group_by}")

        table.build_and_refresh()

    threader(_rollup_summary, tables, cfg.threadcount)
