from os.path import isfile

import os, logging
import toml, json
from datetime import datetime
import ss_api
import concurrent.futures

import polars as pl
from polars import col, lit
from datetime import datetime, timezone
from typing import List, Dict, Callable, Union


start_time = datetime.now()


logging.basicConfig(level=logging.INFO)

class TomlLineBreakPreservingEncoder(toml.TomlEncoder):
    def __init__(self, _dict=dict, preserve=False):
        super(TomlLineBreakPreservingEncoder, self).__init__(_dict, preserve)


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
        argparser.add_argument("--debug", action="store_true")
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
                table_id = v.get("id", None)
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
                        if not table_dict[k2].refresh:
                            table_dict[k2].update_refresh
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

        self.data = pl.DataFrame(data, infer_schema_length=None).filter(
            col("AC").is_not_null()
        )

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
        result = ss_api.import_xlsx_sheet(self.name, self.src, self.parent_id)
        if result:
            self.id = str(result["result"]["id"])
            self.update_refresh()
            print(f"  {self.name}({self.id}): new table loaded")
        Table.config.serialize()

    def update_ss(self, cols: list) -> int:
        if isinstance(self.sheet_col_to_id_map, dict) and isinstance(
            self.sheet_id_to_col_map, dict
        ):
            data = [
                {
                    "id": row["_id"],
                    "cells": [
                        {"columnId": self.sheet_col_to_id_map[col], "value": val}
                        for col, val in row.items()
                        if col in cols
                    ],
                }
                for row in self.data.filter("_UPDATE").iter_rows(named=True)
            ]
            if data:
                print(f"exporting {self.name}({self.id})")
                ss_api.update_sheet(self.id, data)
                Table.config.serialize()
                return len(data)
        return 0

    def insert_ss(self) -> int:
        if isinstance(self.sheet_col_to_id_map, dict) and isinstance(
            self.sheet_id_to_col_map, dict
        ):
            for row in self.data.filter(col("_INSERT")).iter_rows(named=True):
                print(row)

            data = [
                {
                    "toTop": "true",
                    "cells": [
                        {"columnId": self.sheet_col_to_id_map[col], "value": val}
                        for col, val in row.items()
                        if col in self.sheet_col_to_id_map and val
                    ],
                }
                for row in self.data.filter(col("_INSERT")).iter_rows(named=True)
            ]
            if data:
                print(f"exporting {self.name}({self.id})")
                ss_api.add_rows(self.id, data)
                Table.config.serialize()
                return len(data)
        return 0

    def delete_ss(self) -> int:
        if isinstance(self.sheet_col_to_id_map, dict) and isinstance(
            self.sheet_id_to_col_map, dict
        ):

            data = [
                row["_id"]
                for row in self.data.filter(col("_DELETE")).iter_rows(named=True)
            ]
            if data:
                print(f"deleting from {self.name}({self.id})")
                ss_api.delete_rows(self.id, data)
                Table.config.serialize()
                return len(data)
        return 0

def get_sheet():
    print("Starting ...")

    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Submit all table processing tasks to the executor
        futures = [
            executor.submit(get_single_sheet, table) for table in Table.config.tables
        ]


        # Collect results as they complete
        for x, _ in enumerate(concurrent.futures.as_completed(futures)):
            print(f"thread no. {x} returned")


def get_single_sheet(table: Table):
    print(f"Getting {table.name} as xlsx")
    save_path = os.path.join(Table.config.config_dir, f"{table.name}.xlsx")  # Use config_dir
    ss_api.get_sheet_as_xlsx(table.id, save_path)
    print(f"Saved {table.name} to {save_path}")


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
        # if table id not set in config
        print(
            f"No existing table, uploading {table.src} to {table.name} in folder {table.parent_id}"
        )
        table.export_to_ss()

    else:
        result = ss_api.import_xlsx_sheet(
            sheet_name=f"TMP_{table.name}", filepath=table.src, sheet_id = table.id
        )
        
        if not result:
            return
        print(314)
        if "message" in result and result["message"] != "SUCCESS":
            print(result["message"])
            return
        print(318)
        import_sheet_id = result["result"]["id"]
        target_sheet_id = table.id
        print(321)
        if not import_sheet_id or not target_sheet_id:
            return
        print(324)
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

            executor.submit(update_single_sheet, table) for table in Table.config.tables

        ]

        # Collect results as they complete
        for x, _ in enumerate(concurrent.futures.as_completed(futures)):
            pass
            print(f"thread no. {x} returned")

def remove_dupes():
    '''Remove duplicates from smartsheet reports'''
    print("Removing smartsheet duplicates")

    def dedupe_single_sheet(table: Table):
        print(f"Getting {table.name} from smartsheet")
        table.load_from_ss()
        print(table.data.shape)
        ss_df = table.data  # current smartsheet records
        logging.debug(f"\n--ss data--\n{ss_df.head()}")
    
        # Create a new column "_DELETE" initialized to False
        ss_df = ss_df.with_columns(pl.lit(False).alias("_DELETE"))
        
        # Use the .with_columns method to conditionally set "_DELETE" to True
        ss_df = ss_df.with_columns(
            pl.struct("AC", "FLEET", "PN","MAIN_PN", "VENDOR").is_first_distinct()
            .not_()
            .alias("_DELETE")
        )
    
        table.data = ss_df
        num_delete = table.delete_ss()
        print(f"{table.name} Deleted rows: {num_delete}")

    if logging.getLogger().getEffectiveLevel() == logging.DEBUG:
        for table in Table.config.tables:
            dedupe_single_sheet(table)
        pass
    else:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Submit all table processing tasks to the executor
            futures = [
                executor.submit(dedupe_single_sheet, table)
                for table in Table.config.tables
            ]

            # Collect results as they complete
            for x, _ in enumerate(concurrent.futures.as_completed(futures)):
                print(f"thread no. {x} returned")   

def remove_dupes_engine():
    '''Remove duplicates from smartsheet reports'''
    print("Removing smartsheet duplicates")

    def dedupe_single_sheet_engine(table: Table):
        print(f"Getting {table.name} from smartsheet")
        table.load_from_ss()
        print(table.data.shape)
        ss_df = table.data  # current smartsheet records
        logging.debug(f"\n--ss data--\n{ss_df.head()}")
    
        # Create a new column "_DELETE" initialized to False
        ss_df = ss_df.with_columns(pl.lit(False).alias("_DELETE"))
        
        # Use the .with_columns method to conditionally set "_DELETE" to True
        ss_df = ss_df.with_columns(
            pl.struct("AC", "FLEET", "PN", "NHA", "TOP", "LEVEL").is_first_distinct()
            .not_()
            .alias("_DELETE")
        )
    
        table.data = ss_df
        num_delete = table.delete_ss()
        print(f"{table.name} Deleted rows: {num_delete}")

    if logging.getLogger().getEffectiveLevel() == logging.DEBUG:
        for table in Table.config.tables:
            dedupe_single_sheet_engine(table)
        pass
    else:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Submit all table processing tasks to the executor
            futures = [
                executor.submit(dedupe_single_sheet_engine, table)
                for table in Table.config.tables
            ]

            # Collect results as they complete
            for x, _ in enumerate(concurrent.futures.as_completed(futures)):
                print(f"thread no. {x} returned")   


def update_single_sheet(table):
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


def make_summary():
    print("Creating blank summary sheet in folder...")
    # ss_api.create_blank_summary_sheet_in_folder(folder_id)
    print("Blank summary sheet created in folder.")



def feedback_loop():
    print("Starting ...")

    def feedback_single_sheet(table: Table):
        print(f"Getting {table.name} from smartsheet")
        table.load_from_ss()
        print(table.data.shape)
        ss_df = table.data  # current smartsheet records
        logging.debug(f"\n--ss data--\n{ss_df.head()}")
        # new records from trax refresh
        new_df = pl.read_excel(
            table.src,
            schema_overrides=ss_df.select(
                [col for col in ss_df.columns if not col.startswith("_")]
            ).collect_schema(),
        )
        logging.debug(f"\n--excel data--\n{new_df.head()}")

        # join the two sets
        existing_records_df = ss_df.join(
            new_df,
            on=["AC", "FLEET", "MAIN_PN", "PN", "VENDOR"],
            how="left",
            validate="1:1",
        )
        logging.debug(
            f"\n--existing records({existing_records_df.shape})--\n{existing_records_df.head()}"
        )

        # Filter out NO_ACTION rows before determining new records
        new_records_df = new_df.filter(
            col("PROPOSED_ACTION") != lit("NO_ACTION")
        ).join(
            ss_df, on=["AC", "FLEET", "MAIN_PN", "PN", "VENDOR"], how="anti"
        )
        logging.debug(
            f"\n--new records (filtered)({new_records_df.shape})--\n{new_records_df.head()}"
        )

        full_set_df = pl.concat([existing_records_df, new_records_df], how="diagonal")
        logging.debug(f"\n--full set--({full_set_df.shape})\n{full_set_df.head()}")

        # Status conditions
        status_initial = col("_id").is_null()

        status_reopen = (col("Status") == lit("Updated")) & (
            col("PROPOSED_ACTION_right") != lit("NO_ACTION")
        )

        status_complete = (
            col("Status").is_in(
                ["Initial", "Assigned", "In-Work", "Issue", "Updated", "Re-Opened"]
            )
        ) & (col("PROPOSED_ACTION_right") == lit("NO_ACTION"))

        status_err = col("PROPOSED_ACTION_right").is_null()

        update_row = status_reopen | status_complete | status_err
        insert_row = status_initial

        df = full_set_df.with_columns(
            pl.when(status_initial)
            .then(col("Status"))
            .when(status_reopen)
            .then(lit("Re-Opened"))
            .when(status_complete)
            .then(lit("Complete"))
            .when(status_err)
            .then(lit("Error"))
            .otherwise(col("Status"))
            .alias("Status"),
            pl.when(update_row & ~insert_row)
            .then(True)
            .otherwise(False)
            .alias("_UPDATE"),
            pl.when(insert_row).then(True).otherwise(False).alias("_INSERT"),
        ).select([col for col in ss_df.columns] + ["_UPDATE"] + ["_INSERT"])
        logging.debug(f"\n--table data--\n{df.head()}")

        table.data = df
        num_update = table.update_ss(["Status"])
        num_insert = table.insert_ss()

        print(f"{table.name}: {num_update} updated rows | {num_insert} inserted rows")

    if logging.getLogger().getEffectiveLevel() == logging.DEBUG:
        for table in Table.config.tables:
            feedback_single_sheet(table)
        pass
    else:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Submit all table processing tasks to the executor
            futures = [
                executor.submit(feedback_single_sheet, table)
                for table in Table.config.tables
            ]

            # Collect results as they complete
            for x, _ in enumerate(concurrent.futures.as_completed(futures)):
                print(f"thread no. {x} returned")


def feedback_loop_engine():
    print("Starting ...")

    def feedback_single_sheet_engine(table: Table):
        print(f"Getting {table.name} from smartsheet")
        table.load_from_ss()
        print(table.data.shape)
        ss_df = table.data  # current smartsheet records
        logging.debug(f"\n--ss data--\n{ss_df.head()}")
        # new records from trax refresh
        print(570)
        new_df = pl.read_excel(
            table.src,
            schema_overrides=ss_df.select(
                [col for col in ss_df.columns if not col.startswith("_")]
            ).collect_schema(),
        )
        logging.debug(f"\n--excel data--\n{new_df.head()}")
        print(new_df)
        print(ss_df)
        print(577)
        # join the two sets
        duplicate_rows = ss_df.filter(
            ss_df.select(["AC", "FLEET", "PN", "NHA", "TOP", "LEVEL"]).is_duplicated()
                )
        duplicate_pk_columns = duplicate_rows.select(["AC", "FLEET", "PN", "NHA", "TOP", "LEVEL"])

        # Print the duplicate primary key columns
        print(duplicate_pk_columns)
        
        try:
            existing_records_df = ss_df.join(
                new_df,
                on=["AC", "FLEET", "PN", "NHA", "TOP", "LEVEL"],
                validate="1:1",
            )
        except Exception as e:
            print(e)
        print(existing_records_df)
        logging.debug(
            f"\n--existing records({existing_records_df.shape})--\n{existing_records_df.head()}"
        )
        print(588)
        # Filter out NO_ACTION rows before determining new records
        new_records_df = new_df.filter(
            col("PROPOSED_ACTION") != lit("NO_ACTION")
        ).join(
            ss_df, on=["AC", "FLEET", "PN", "NHA", "TOP"], how="anti"
        )
        logging.debug(
            f"\n--new records (filtered)({new_records_df.shape})--\n{new_records_df.head()}"
        )

        full_set_df = pl.concat([existing_records_df, new_records_df], how="diagonal")
        logging.debug(f"\n--full set--({full_set_df.shape})\n{full_set_df.head()}")

        # Status conditions
        status_initial = col("_id").is_null()

        status_reopen = (col("Status") == lit("Updated")) & (
            col("PROPOSED_ACTION_right") != lit("NO_ACTION")
        )
        print(607)
        status_complete = (
            col("Status").is_in(
                ["Initial", "Assigned", "In-Work", "Issue", "Updated", "Re-Opened"]
            )
        ) & (col("PROPOSED_ACTION_right") == lit("NO_ACTION"))

        status_err = col("PROPOSED_ACTION_right").is_null()

        update_row = status_reopen | status_complete | status_err
        insert_row = status_initial

        df = full_set_df.with_columns(
            pl.when(status_initial)
            .then(col("Status"))
            .when(status_reopen)
            .then(lit("Re-Opened"))
            .when(status_complete)
            .then(lit("Complete"))
            .when(status_err)
            .then(lit("Error"))
            .otherwise(col("Status"))
            .alias("Status"),
            pl.when(update_row & ~insert_row)
            .then(True)
            .otherwise(False)
            .alias("_UPDATE"),
            pl.when(insert_row).then(True).otherwise(False).alias("_INSERT"),
        ).select([col for col in ss_df.columns] + ["_UPDATE"] + ["_INSERT"])
        logging.debug(f"\n--table data--\n{df.head()}")

        table.data = df
        num_update = table.update_ss(["Status"])
        num_insert = table.insert_ss()

        print(f"{table.name}: {num_update} updated rows | {num_insert} inserted rows")

    if logging.getLogger().getEffectiveLevel() == logging.DEBUG:
        for table in Table.config.tables:
            feedback_single_sheet_engine(table)
        pass
    else:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Submit all table processing tasks to the executor
            futures = [
                executor.submit(feedback_single_sheet_engine, table)
                for table in Table.config.tables
            ]

            # Collect results as they complete
            for x, _ in enumerate(concurrent.futures.as_completed(futures)):
                print(f"thread no. {x} returned")


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
    elif Table.config.function == "dedupe":
        remove_dupes()
    elif Table.config.function == "dedupe_engine":
        remove_dupes_engine()
    elif Table.config.function == "feedback":
        feedback_loop()
    elif Table.config.function == "feedback_engine":
        feedback_loop_engine()



if __name__ == "__main__":

    main()


end_time = datetime.now()
print("Duration: {}".format(end_time - start_time))
