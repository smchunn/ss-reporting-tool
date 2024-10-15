import smartsheet
import sys
import logging
import os
import openpyxl
import toml
from datetime import datetime

start_time = datetime.now()

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


def delete_all_rows(smart, sheet):
    if sheet.rows:
        rowsToUpdate = []
        for i, row in enumerate(sheet.rows):
            if i > 0:
                tmp_row = smart.models.Row()
                tmp_row.id = row.id
                tmp_row.parentId = sheet.rows[0].id
                rowsToUpdate.append(tmp_row)

        _ = smart.Sheets.update_rows(sheet.id, rowsToUpdate)

        response = smart.Sheets.delete_rows(sheet.id, [sheet.rows[0].id])


def get_sheet():

    smart = smartsheet.Smartsheet()
    smart.errors_as_exceptions(True)

    if type(CONFIG) == dict:
        print("Starting ...")
        if "verbose" in CONFIG and CONFIG["verbose"] == True:
            logging.basicConfig(filename="sheet.log", level=logging.INFO)
        for k, v in CONFIG["tables"].items():
            table_id = v["id"]
            table_src = v["src"]
            table_name = k
            smart.Sheets.get_sheet_as_excel(table_id, _dir_out)

            workbook = openpyxl.load_workbook(
                os.path.join(_dir_out, f"{table_name}.xlsx")
            )
            worksheet = workbook[table_name]
            worksheet.title = "AUDIT"
            workbook.save(os.path.join(_dir_out, f"{table_name}.xlsx"))


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

                print(f"  uploading sheet:", end="")
                upload_start = datetime.now()
                result = smart.Sheets.import_xlsx_sheet(
                    os.path.join(_dir_in, table_src),
                    sheet_name=f"TMP_{table_name}",
                    header_row_index=0,
                    primary_column_index=0,
                )
                print(f"{datetime.now()-upload_start}")

                import_sheet = smart.Sheets.get_sheet(result.data.id)
                target_sheet = smart.Sheets.get_sheet(table_id)

                print(
                    f"  {table_name}({table_id}): replacing {str(len(target_sheet.rows))} rows with {str(len(target_sheet.rows))} rows from {table_src}"
                )

                for column in target_sheet.columns:
                    column_map[column.title] = column.id

                print(f"  deleting rows:", end="")
                delete_start = datetime.now()
                delete_all_rows(smart, target_sheet)
                print(f"{datetime.now()-delete_start}")

                print(f"  inserting rows:", end="")
                insert_start = datetime.now()

                rowsToInsert = [row.id for row in import_sheet.rows]
                batch = 500
                if rowsToInsert:
                    for i in range(0, len(rowsToInsert), batch):
                        response = smart.Sheets.move_rows(
                            import_sheet.id,
                            smartsheet.models.CopyOrMoveRowDirective(
                                {
                                    "row_ids": rowsToInsert[i : batch + i],
                                    "to": smartsheet.models.CopyOrMoveRowDestination(
                                        {"sheet_id": target_sheet.id}
                                    ),
                                }
                            ),
                        )
                    print(f"{datetime.now()-insert_start}")
                    # print(f"  insert result: {response}")

                print("  done...\ndeleting tmp sheet...")

                smart.Sheets.delete_sheet(import_sheet.id)  # sheet_id
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

end_time = datetime.now()
print("Duration: {}".format(end_time - start_time))
