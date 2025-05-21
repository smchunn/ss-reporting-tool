from ss_reporting_tool.Config import Config
from ss_reporting_tool.Report import Report
from ss_reporting_tool.Utils import threader
import os, logging
import ss_api
from typing import List


def set_sheet(cfg: Config, tables: List):
    def _set_sheet(table: Report):
        print(f"starting {table.name}...")

        if not table.src:
            logging.debug(f"failed attempt to load from file: {table.name} ")
            return

        if not table.id:
            print(f"No existing table, uploading {table.src} to {table.name}")
            result = ss_api.import_xlsx_sheet(
                sheet_name=table.name,
                filepath=os.path.join(table.src),
                folder_id=table.folder_id if table.folder_id else None,
            )

            if result:
                table.id = str(result["result"]["id"])
                print(f"  {table.name}({table.id}): new table loaded")
                return ("new_id", table.name, table.id)

        else:
            result = ss_api.import_xlsx_sheet(
                sheet_name=f"TMP_{table.name}",
                filepath=table.src,
                folder_id=table.folder_id if table.folder_id else None,
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
        cfg.serialize()
        print("done...")

    print("Starting ...")

    threader(_set_sheet, tables, cfg.threadcount)
