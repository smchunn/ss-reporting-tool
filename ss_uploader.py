import sys, os, logging
import toml, openpyxl
from datetime import datetime
import ss_api
import concurrent.futures, threading


start_time = datetime.now()

CONFIG = None
_dir_in = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "Effectivity_Reports_Mod/"
)
_dir_out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out/")
_conf = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.toml")


def get_sheet():
    if isinstance(CONFIG, dict):
        print("Starting ...")
        if "verbose" in CONFIG and CONFIG["verbose"] == True:
            logging.basicConfig(filename="sheet.log", level=logging.INFO)

        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Submit all table processing tasks to the executor
            futures = [
                executor.submit(get_single_sheet, table["id"], table_name)
                for table_name, table in CONFIG["tables"].items()
            ]

            # Collect results as they complete
            for x, future in enumerate(concurrent.futures.as_completed(futures)):
                pass
                print(f"thread no. {x} returned")

        # for k, v in CONFIG["tables"].items():
        #     table_id = v["id"]
        #     table_src = v["src"]
        #     table_name = k
        #     # Pass the folder_id to the get_sheet_as_excel function
        #     ss_api.get_sheet_as_xlsx(
        #         table_id, os.path.join(_dir_out, f"{table_name}.xlsx")
        #     )


def get_single_sheet(table_id, table_name):
    print(f"Getting {table_name} as xslx")
    ss_api.get_sheet_as_xlsx(table_id, os.path.join(_dir_out, f"{table_name}.xlsx"))


def set_sheet():
    print("Starting ...")
    if isinstance(CONFIG, dict):
        target_workspace_id = CONFIG.get("env", {}).get("target_workspace")
        target_folder_id = CONFIG.get("env", {}).get("target_folder")

        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Submit all table processing tasks to the executor
            futures = [
                executor.submit(
                    set_single_sheet,
                    table["id"],
                    table_name,
                    table["src"],
                    target_folder_id,
                )
                for table_name, table in CONFIG["tables"].items()
            ]

            # Collect results as they complete
            for x, future in enumerate(concurrent.futures.as_completed(futures)):
                result = future.result()
                if isinstance(result, tuple) and result[0] == "new_id":
                    CONFIG["tables"][result[1]]["id"] = result[2]
                print(f"thread no. {x} returned")

        # for k, v in CONFIG["tables"].items():
        #     table_id = v["id"]
        #     table_src = v["src"]
        #     table_name = k


def set_single_sheet(table_id, table_name, table_src, target_folder_id):
    print(f"starting {table_name}...")

    if not table_id:
        print(f"No existing table, uploading {table_src} to {table_name}")
        result = ss_api.import_xlsx_sheet(
            sheet_name=table_name,
            filepath=os.path.join(_dir_in, table_src),
            folder_id=target_folder_id if target_folder_id else None,
        )
        if result:
            table_id = str(result["result"]["id"])
            print(f"  {table_name}({table_id}): new table loaded")
            return ("new_id", table_name, table_id)
    else:
        result = ss_api.import_xlsx_sheet(
            sheet_name=f"TMP_{table_name}",
            filepath=os.path.join(_dir_in, table_src),
        )
        if not result:
            return

        if "message" in result and result["message"] != "SUCCESS":
            print(result["message"])
            return

        import_sheet_id = result["result"]["id"]
        target_sheet_id = table_id

        if not import_sheet_id or not target_sheet_id:
            return

        ss_api.clear_sheet(target_sheet_id)
        ss_api.move_rows(target_sheet_id, import_sheet_id)
        ss_api.delete_sheet(import_sheet_id)
    print("done...")


def update_sheet():
    """
    Updates the columns in the specified sheets to set "Status" as a dropdown
    and "Created Date" and "Modified Date" as date columns.
    """
    print("Updating columns ...")
    if isinstance(CONFIG, dict):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Submit all table processing tasks to the executor
            futures = [
                executor.submit(update_single_sheet, table["id"], table_name)
                for table_name, table in CONFIG["tables"].items()
            ]

            # Collect results as they complete
            for x, future in enumerate(concurrent.futures.as_completed(futures)):
                pass
                print(f"thread no. {x} returned")


def update_single_sheet(table_id, table_name):
    print(f"Updating columns for table: {table_name} (ID: {table_id})")
    column_updates = {
        "Status": {
            "type": "PICKLIST",
            "options": [
                "Initial",
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
    columns = ss_api.get_columns(sheet_id=table_id)
    if isinstance(columns, dict):
        columns = columns.get("data", None)
    if not columns:
        print(f"error getting columns for '{table_name} (ID: {table_id})'")

    updates = {}
    if isinstance(columns, list):
        for col in columns:
            if isinstance(col, dict) and "title" in col:
                id = col["id"]
                title = col["title"]
                # use specific update if it exists
                if title in column_updates:
                    updates[id] = {"title": title}.update(column_updates[title])

                # Default update to TEXT_NUMBER
                else:
                    updates[id] = {
                        "title": title,
                        "type": "TEXT_NUMBER",
                    }
    for id, update in updates.items():
        ss_api.update_columns(sheet_id=table_id, column_id=id, column_update=update)

    print(f"Columns updated for table: {table_name}")


def make_summary():
    print("Creating blank summary sheet in folder...")
    if isinstance(CONFIG, dict):
        folder_id = CONFIG.get("env", {}).get("target_folder")
        # ss_api.create_blank_summary_sheet_in_folder(folder_id)
        print("Blank summary sheet created in folder.")


if __name__ == "__main__":
    with open(_conf, "r") as conf:
        CONFIG = toml.load(conf)
        if isinstance(CONFIG, dict):
            for k, v in CONFIG["env"].items():
                os.environ[k] = v
            print(CONFIG.get("verbose"))
            if CONFIG.get("verbose", False):
                logging.basicConfig(
                    filename="sheet.log", filemode="w", level=logging.INFO
                )

            # Check the command-line argument and call the appropriate function
            if sys.argv[1] == "get":
                get_sheet()
            elif sys.argv[1] == "set":
                set_sheet()
            elif sys.argv[1] == "update":
                update_sheet()
            elif sys.argv[1] == "summary":
                make_summary()

    if isinstance(CONFIG, dict):
        with open(_conf, "w") as conf:
            toml.dump(CONFIG, conf)


end_time = datetime.now()
print("Duration: {}".format(end_time - start_time))
