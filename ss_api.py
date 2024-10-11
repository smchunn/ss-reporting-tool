import smartsheet
import pandas as pd
import sys
import logging
import os
import toml
import time

from smartsheet.smartsheet import Smartsheet

CONFIG = None
_dir_in = os.path.join(os.path.dirname(os.path.abspath(__file__)), "in/")
_dir_out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out/")
_conf = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.toml")

# The API identifies columns by Id, but it's more convenient to refer to column names. Store a map here
column_map = {}


# Helper function to find cell in a row
def get_cell_by_column_name(row, column_name):
    column_id = column_map[column_name]
    return row.get_column(column_id)


def get_sheet():

    smart = smartsheet.Smartsheet()
    smart.errors_as_exceptions(True)

    if type(CONFIG) == dict:
        if "verbose" in CONFIG and CONFIG["verbose"] == True:
            logging.basicConfig(filename="sheet.log", level=logging.INFO)
        for k, v in CONFIG["tables"].items():
            table_id = v["id"]
            table_src = v["src"]
            table_name = k
            smart.Sheets.get_sheet_as_excel(table_id, _dir_out)


def set_sheet():
    print("Starting ...")

    smart: smartsheet.Smartsheet = smartsheet.Smartsheet()
    smart.errors_as_exceptions(True)

    if type(CONFIG) == dict:
        if "verbose" in CONFIG and CONFIG["verbose"] == True:
            logging.basicConfig(filename="sheet.log", level=logging.INFO)
        for k, v in CONFIG["tables"].items():
            table_id = v["id"]
            table_src = v["src"]
            table_name = k
            print(f"starting {table_name}...")

            if len(table_id) == 0:
                result = smart.Sheets.import_xlsx_sheet(
                    _dir_in + table_src,
                    sheet_name=table_name,
                    header_row_index=0,
                    primary_column_index=0,
                )
                table_id = str(result.data.id)

                print(f"  {table_name}({table_id}): new table loaded")

                CONFIG["tables"][k]["id"] = table_id
            else:

                result = smart.Sheets.import_xlsx_sheet(
                    os.path.join(_dir_in, table_src),
                    sheet_name=f"TMP_{table_name}",
                    header_row_index=0,
                    primary_column_index=0,
                )

                import_sheet = smart.Sheets.get_sheet(result.data.id)
                target_sheet = smart.Sheets.get_sheet(table_id)

                print(
                    f"  {table_name}({table_id}): replacing {str(len(target_sheet.rows))} rows with {str(len(target_sheet.rows))} rows from {table_src}"
                )

                for column in target_sheet.columns:
                    column_map[column.title] = column.id

                rowsToDelete = [row.id for row in target_sheet.rows]

                # Batch deletion
                batch_size = 100
                for i in range(0, len(rowsToDelete), batch_size):
                    batch = rowsToDelete[i : i + batch_size]
                    response = smart.Sheets.delete_rows(table_id, batch)

                rowsToTransfer = [row.id for row in import_sheet.rows]
                if rowsToTransfer:
                    response = smart.Sheets.move_rows(
                        import_sheet.id,
                        smartsheet.models.CopyOrMoveRowDirective(
                            {
                                "row_ids": rowsToTransfer,
                                "to": smartsheet.models.CopyOrMoveRowDestination(
                                    {"sheet_id": target_sheet.id}
                                ),
                            }
                        ),
                    )
                print("  done...\ndeleting tmp sheet...")

                smart.Sheets.delete_sheet(import_sheet.id)  # sheet_id
            time.sleep(30)
            print("done...")


print("Done")
if __name__ == "__main__":
    with open(_conf, "r") as conf:
        CONFIG = toml.load(conf)
        for k, v in CONFIG["env"].items():
            os.environ[k] = v

        if sys.argv[1] == "get":
            get_sheet()
        elif sys.argv[1] == "set":
            set_sheet()

    with open(_conf, "w") as conf:
        toml.dump(CONFIG, conf)
