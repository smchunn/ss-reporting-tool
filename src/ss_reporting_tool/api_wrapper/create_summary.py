from ss_reporting_tool.Config import Config
from ss_reporting_tool.Summary import Summary
import os
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

    for table in tables:
        if not table.id:
            result = ss_api.create_sheet(table.name, [])
            if result and "result" in result:
                table.id = result["result"]["id"]
                print(f"Created new empty summary sheet with ID {table.id}")
            else:
                print(f"Failed to create summary sheet for {table.name}")
        else:
            print(f"Summary sheet {table.name} already exists with ID {table.id}")
