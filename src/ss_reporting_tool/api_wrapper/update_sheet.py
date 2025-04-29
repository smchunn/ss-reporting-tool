from ss_reporting_tool.Table import Table
from ss_reporting_tool.Config import CFG, threader
import ss_api
import polars as pl
from polars import col, lit
from typing import List


def update_sheet(tables: List):
    """
    Updates the columns in the specified sheets to set "Status" as a dropdown
    and "Created Date" and "Modified Date" as date columns.
    """

    def _update_sheet(table):
        print(f"Updating columns for table: {table.name} (ID: {table.id})")
        column_updates = {
            "Status": {
                "type": "PICKLIST",
                "options": [
                    "Initial",
                    "Assigned",
                    "In-Work",
                    "Issue",
                    "Updated",
                    "Re-Opened",
                    "Validated",
                    "Complete",
                ],
            },
            "Created Date": {"type": "DATE"},
            "Modified Date": {"type": "DATE"},
        }
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
    threader(_update_sheet, tables, CFG.threadcount)
