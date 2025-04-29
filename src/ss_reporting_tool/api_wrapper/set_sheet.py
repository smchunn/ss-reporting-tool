from ss_reporting_tool.Table import Table
from ss_reporting_tool.Config import CFG, threader
import os, logging
import ss_api
import concurrent.futures, threading
from typing import List


def set_sheet(tables: List):
    def _set_sheet(table: Table):
        print(f"starting {table.name}...")

        if not table.id:
            print(f"No existing table, uploading {table.src} to {table.name}")
            result = ss_api.import_xlsx_sheet(
                sheet_name=table.name,
                filepath=os.path.join(table.src),
                folder_id=table.parent_id if table.parent_id else None,
            )

            if result:
                table.id = str(result["result"]["id"])
                print(f"  {table.name}({table.id}): new table loaded")
                return ("new_id", table.name, table.id)

        else:
            result = ss_api.import_xlsx_sheet(
                sheet_name=f"TMP_{table.name}",
                filepath=table.src,
                folder_id=table.parent_id if table.parent_id else None,
            )

            if not result:
                return
            if "message" in result and result["message"] != "SUCCESS":
                print(result["message"])
                return
            import_sheet_id = result["result"]["id"]
            target_sheet_id = table.id
            if not import_sheet_id or not target_sheet_id:
                return
            ss_api.clear_sheet(target_sheet_id)
            ss_api.move_rows(target_sheet_id, import_sheet_id)
            ss_api.delete_sheet(import_sheet_id)
        CFG.serialize()
        print("done...")

    print("Starting ...")

    threader(_set_sheet, tables, CFG.threadcount)
