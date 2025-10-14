from ss_reporting_tool.Config import Config
from ss_reporting_tool.Summary import Summary
import os
import json
from typing import List
import ss_api

def create_summary(cfg: Config, tables: List[Summary]):
    """
    Creates empty summary sheets in Smartsheet for each summary sheet defined in the summary config.

    Args:
        cfg (Config): Configuration object containing settings_dir and other config.
        tables (List[Summary]): List of Summary objects or tables to process.

    Returns:
        None
    """
    print("reached")
    rollup_path = os.path.join(cfg.settings_dir, "rollup_summary.json")
    try:
        with open(rollup_path, "r") as f:
            rollup_settings = json.load(f)
    except Exception as e:
        print(f"Failed to load rollup summary settings from {rollup_path}: {e}")
        rollup_settings = {}

    for table in tables:
        if not table.id:
            folder_id = getattr(table, "target_folder", None)
            if folder_id is None:
                print(f"Missing target_folder for summary sheet {table.name}, cannot create sheet.")
                return
            sheet_definition = {
                "name": table.name,
                "columns": rollup_settings.get("columns", [])
            }
            print(f"Sending create_sheet request with folder_id={folder_id} and sheet_definition={sheet_definition}")
            result = ss_api.create_sheet(folder_id, sheet_definition)
            if result and "result" in result:
                table.id = result["result"]["id"]
                print(f"Created new empty summary sheet with ID {table.id}")
                cfg.serialize()
            else:
                print(f"Failed to create summary sheet for {table.name}")
        else:
            print(f"Summary sheet {table.name} already exists with ID {table.id}")
