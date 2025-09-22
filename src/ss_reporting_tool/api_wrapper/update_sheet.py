from ss_reporting_tool.Config import Config
from ss_reporting_tool.Report import Report
from ss_reporting_tool.Utils import threader
import ss_api
import polars as pl
from polars import col, lit
from typing import List


def update_sheet(cfg: Config, tables: List):

    def _update_sheet(table):
        print(f"Updating columns for table: {table.name} (ID: {table.id})")
        column_updates = {
            "STATUS": {
                "type": "PICKLIST",
                "options": [
                    "INITIAL",
                    "ASSIGNED",
                    "IN-WORK",
                    "VALIDATED-NO ACTION",
                    "VALIDATED-ACTION ",
                    "APPROVAL-SECOND LEVEL",
                    "ESCALATED-CONFIG"
                    "COMPLETE",
                ],
            },
            "ACTION": {
                "type": "PICKLIST",
                "options": [
                    "BATCH-REMOVE EFFECTIVITY",
                    "BATCH-ADD EFFECTIVITY",
                    "SER-REMOVE EFFECTIVITY",
                    "SER-ADD EFFECTIVITY",
                    "TRK-REMOVE EFFECTIVITY",
                    "TRK-ADD EFFECTIVITY",
                    "INTERCHANGEABILITY ADD/REMOVE/CHANGE",
                    "ATA CHANGED",
                    "APPROVED/UNAPPROVED PART",
                    "MANUFACTURER CODE CHANGED",
                    "PART GROUP CHANGED",
                    "REMOVE/ADD POSITION/QUANTITY",
                    "NONE",
                ],
            },
            "PN EXISTS": {
                "type": "PICKLIST",
                "options": [
                    "MTX",
                    "IPC",
                    "BOTH",
                ],
            },
            "ASSIGNMENT": {"type": "CONTACT_LIST"},
            "APPROVAL/ESCALATED": {"type": "CONTACT_LIST"},
            #"CREATED DATE": {"type": "DATE"},
            "MODIFIED_DATE": {"type": "DATE"},
            #"COMPLETED DATE": {"type": "DATE"},
            #"IPC EFFECTIVITY MISSING FROM MTX": {"type": "MULTI_PICKLIST"},
            #"IFS EXISTING EFFECTIVITY VALIDATATION": {"type": "MULTI_PICKLIST"},
            "IPC_EFF_ALT": {"type": "MULTI_PICKLIST"},
            "IFS_EFF_ALT": {"type": "MULTI_PICKLIST"},
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
    threader(_update_sheet, tables, cfg.threadcount)
