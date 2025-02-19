from os.path import isfile
import sys, os, logging
import toml, json
from datetime import datetime
import ss_api
import concurrent.futures, threading
import polars as pl
from polars import col, lit
from datetime import datetime, timezone
from typing import List, Dict, Callable, Union


start_time = datetime.now()


class TomlLineBreakPreservingEncoder(toml.TomlEncoder):
    def __init__(self, _dict=dict, preserve=False):
        super(TomlLineBreakPreservingEncoder, self).__init__(_dict, preserve)

    def dump_list(self, v):
        retval = "[\n"
        for u in v:
            if isinstance(u, str) and "\n" in u:
                retval += (
                    '  """' + u.replace('"""', '\\"""').replace("\\", "\\\\") + '""",\n'
                )
            else:
                retval += " " + str(self.dump_value(u)) + ","
        retval += " ]"
        return retval


class Config:

    def __init__(self) -> None:
        import argparse

        argparser = argparse.ArgumentParser(add_help=True)
        argparser.add_argument("func", type=str, help="function to run: ")
        argparser.add_argument(
            "-c",
            "--config",
            type=str,
            help="path/to/config.toml",
            default="./config.toml",
        )
        argparser.add_argument("--verbose", action="store_true")
        argparser.add_argument("--threadcount", help="set # of threads", default=None)
        args = argparser.parse_args()

        self.function = args.func

        self.path = os.path.abspath(os.path.expanduser(args.config))

        with open(args.config, "r") as conf:
            self._config = toml.load(conf)

        self.tables = []

        if isinstance(self._config, dict):
            for k, v in self._config["env"].items():
                os.environ[k] = v
            if self._config.get("verbose", False):
                self.verbose = True
            self.data_dir = self._config.get("data_dir", "./data")
            if not os.path.exists(self.data_dir):
                os.mkdir(self.data_dir)
            elif os.path.isfile(self.data_dir):
                print(f"Error: data dir exists as file")
                exit()

            self.target_folder = self._config.get("target_folder", None)
            for k, v in self._config["tables"].items():
                table_id = v["id"]
                table_src = (
                    os.path.join(self.data_dir, v["src"])
                    if os.path.isfile(os.path.join(self.data_dir, v["src"]))
                    else ""
                )
                table_name = k
                table_refresh = v.get("date", datetime.now())
                self.tables.append(
                    Table(
                        table_id,
                        self.target_folder,
                        table_name,
                        table_src,
                        table_refresh,
                    )
                )
        self.verbose = self.verbose or args.verbose

        if self.verbose:
            logging.basicConfig(
                filename=os.path.join(self.data_dir, "sheet.log"),
                filemode="w",
                level=logging.INFO,
            )

    def serialize(self) -> None:
        table_dict = {table.name: table for table in self.tables}
        for k1, v1 in self._config.items():
            if k1 == "tables":
                for k2, v2 in v1.items():
                    if k2 in table_dict:
                        v2["id"] = table_dict[k2].id
                        v2["date"] = table_dict[k2].refresh

        with open(self.path, "w") as conf:
            encoder = TomlLineBreakPreservingEncoder()
            toml.dump(self._config, conf, encoder=encoder)


class Table:
    config: Config

    def __init__(self, id, parent_id, name, src, last_update) -> None:
        self.name = name
        self.id = id
        self.parent_id = parent_id
        self.src = src
        self.last_update = last_update
        self.data: pl.DataFrame = pl.DataFrame()
        self.sheet_id_to_col_map = None
        self.sheet_col_to_id_map = None

    def __bool__(self) -> bool:
        return not self.data.is_empty()

    def __hash__(self) -> int:
        return hash(self.name)

    def update_refresh(self) -> None:
        self.refresh = str(datetime.now(timezone.utc).isoformat(timespec="seconds"))

    def load_from_ss(self) -> None:
        sheet_json = ss_api.get_sheet(self.id)
        self.update_refresh()
        if not isinstance(sheet_json, Dict):
            return
        with open(
            os.path.join(Table.config.data_dir, f"{self.name}.json"), "w"
        ) as file:
            json.dump(sheet_json, file)

        self.sheet_id_to_col_map = {
            col["id"]: col["title"] for col in sheet_json["columns"]
        }
        self.sheet_col_to_id_map = {
            col["title"]: col["id"] for col in sheet_json["columns"]
        }

        data = []
        for row in sheet_json["rows"]:
            row_data = {}
            row_data["_id"] = row["id"]
            row_data["_created"] = row["createdAt"]
            row_data["_modified"] = row["modifiedAt"]
            # row_data["AUDIT_BY"] = row["modifiedBy"]
            for cell in row["cells"]:
                column_title = self.sheet_id_to_col_map[cell["columnId"]]
                row_data[column_title] = cell.get("value", None)
            data.append(row_data)

        self.data = pl.DataFrame(data, infer_schema_length=None)

    def load_from_file(self) -> None:
        self.data = pl.read_csv(self.src, separator=chr(31))

    def export_to_excel(self) -> None:
        excel_fp = os.path.join(Table.config.data_dir, f"{self.name}.xlsx")
        self.data.write_excel(
            workbook=excel_fp,
            worksheet="audit",
            table_name="audit_table",
            table_style="Table Style Medium 9",
            autofit=True,
            freeze_panes=(1, 0),
        )

    def export_to_ss(self) -> None:
        excel_fp = os.path.join(Table.config.data_dir, f"{self.name}.xlsx")
        ss_target_folder = Table.config.target_folder
        result = ss_api.import_xlsx_sheet(self.name, excel_fp, ss_target_folder)
        if result:
            self.id = str(result["result"]["id"])
            self.update_refresh()
            print(f"  {self.name}({self.id}): new table loaded")
        Table.config.serialize()

    def update_ss(self) -> None:
        if isinstance(self.sheet_col_to_id_map, dict) and isinstance(
            self.sheet_id_to_col_map, dict
        ):
            data = [
                {
                    "id": row["_id"],
                    "cells": [
                        {"columnId": self.sheet_col_to_id_map[col], "value": val}
                        for col, val in row.items()
                        if col
                        in [
                            "USER_STATUS",
                            "AUDIT_BY",
                            "EPICC_STATUS",
                            "MXI_REMAINING",
                            "TRAX_REMAINING",
                            "_MXI_BASELINE",
                        ]
                    ],
                }
                for row in self.data.filter("_UPDATE").iter_rows(named=True)
            ]
            print(f"exporting {self.name}({self.id})")
            ss_api.update_sheet(self.id, data)
        Table.config.serialize()


def get_sheet():
    print("Starting ...")

    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Submit all table processing tasks to the executor
        futures = [
            executor.submit(get_single_sheet, table) for table in Table.config.tables
        ]

        # Collect results as they complete
        for x, _ in enumerate(concurrent.futures.as_completed(futures)):
            pass
            print(f"thread no. {x} returned")


def get_single_sheet(table: Table):
    print(f"Getting {table.name} as xslx")
    ss_api.get_sheet_as_xlsx(
        table.id, os.path.join(Table.config.path, f"{table.name}.xlsx")
    )


def set_sheet():
    print("Starting ...")

    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Submit all table processing tasks to the executor
        futures = [
            executor.submit(set_single_sheet, table) for table in Table.config.tables
        ]

        # Collect results as they complete
        for x, _ in enumerate(concurrent.futures.as_completed(futures)):
            print(f"thread no. {x} returned")


def set_single_sheet(table: Table):
    print(f"starting {table.name}...")

    if not table.id:
        print(f"No existing table, uploading {table.src} to {table.name} in folder {table.parent_id}")
        result = ss_api.import_xlsx_sheet(
            sheet_name=table.name, filepath=table.src, folder_id=table.parent_id
        )
        if result:
            table.id = str(result["result"]["id"])
            print(f"  {table.name}({table.id}): new table loaded")
    else:
        result = ss_api.import_xlsx_sheet(
            sheet_name=f"TMP_{table.name}", filepath=table.src
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
    Table.config.serialize()
    print("done...")


def update_sheet():
    """
    Updates the columns in the specified sheets to set "Status" as a dropdown
    and "Created Date" and "Modified Date" as date columns.
    """
    print("Updating columns ...")
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Submit all table processing tasks to the executor
        futures = [
            executor.submit(update_single_sheet, table["id"], table_name)
            for table_name, table in Table.config.tables
        ]

        # Collect results as they complete
        for x, _ in enumerate(concurrent.futures.as_completed(futures)):
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
                    updates[id] = {"title": title}
                    updates[id].update(column_updates[title])

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
    # ss_api.create_blank_summary_sheet_in_folder(folder_id)
    print("Blank summary sheet created in folder.")


def main():
    Table.config = Config()
    if Table.config.function == "get":
        get_sheet()
    elif Table.config.function == "set":
        set_sheet()
    elif Table.config.function == "update":
        update_sheet()
    elif Table.config.function == "summary":
        make_summary()


if __name__ == "__main__":

    main()


end_time = datetime.now()
print("Duration: {}".format(end_time - start_time))
