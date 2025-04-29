import src.Config
import os, logging
import toml, json
import ss_api
import concurrent.futures, threading
import polars as pl
from datetime import datetime
from os.path import isfile
from polars import Config, col, lit
from datetime import datetime, timezone
from typing import List, Dict, Callable, Union
class Table:
    config: src.Config.Config = src.Config.Config()
    def __init__(
        self, id, parent_id, target_id, name, src, data_dir, last_update
    ) -> None:
        self.name = name
        self.id = id
        self.parent_id = parent_id
        self.target_id = target_id
        self.src = src
        self.data_dir = data_dir
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
        if logging.getLogger().getEffectiveLevel() == logging.DEBUG:
            with open(os.path.join(self.data_dir, f"{self.name}.json"), "w") as file:
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
            for cell in row["cells"]:
                column_title = self.sheet_id_to_col_map[cell["columnId"]]
                row_data[column_title] = cell.get("value", None)
            data.append(row_data)

        self.data = pl.DataFrame(data, infer_schema_length=None)
        # .filter(col("AC").is_not_null())

    def load_from_file(self) -> None:
        self.data = pl.read_csv(self.src, separator=chr(31))

    def export_to_excel(self) -> None:
        excel_fp = os.path.join(self.data_dir, f"{self.name}.xlsx")
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

    def update_ss(self, rows=None, cols=None) -> int:
        if not rows:
            rows = pl.lit(True)
        if isinstance(self.sheet_col_to_id_map, dict) and isinstance(
            self.sheet_id_to_col_map, dict
        ):
            if not cols:
                cols = list(self.sheet_col_to_id_map.keys())
            data = [
                {
                    "id": row["_id"],
                    "cells": [
                        {"columnId": self.sheet_col_to_id_map[col], "value": val}
                        for col, val in row.items()
                        if col in cols
                    ],
                }
                for row in self.data.filter(rows).iter_rows(named=True)
            ]
            if data:
                print(f"exporting {self.name}({self.id})")
                ss_api.update_sheet(self.id, data)
                Table.config.serialize()
                return len(data)
        return 0

    def insert_ss(self, rows=None) -> int:
        if (
            isinstance(self.sheet_col_to_id_map, dict)
            and isinstance(self.sheet_id_to_col_map, dict)
            and isinstance(rows, pl.Expr)
        ):

            data = [
                {
                    "toTop": "true",
                    "cells": [
                        {"columnId": self.sheet_col_to_id_map[col], "value": val}
                        for col, val in row.items()
                        if col in self.sheet_col_to_id_map and val
                    ],
                }
                for row in self.data.filter(rows).iter_rows(named=True)
            ]
            if data:
                print(f"exporting {self.name}({self.id})")
                ss_api.add_rows(self.id, data)
                Table.config.serialize()
                return len(data)
        return 0

    def delete_ss(self, rows=None) -> int:
        if (
            isinstance(self.sheet_col_to_id_map, dict)
            and isinstance(self.sheet_id_to_col_map, dict)
            and isinstance(rows, pl.Expr)
        ):

            data = [row["_id"] for row in self.data.filter(rows).iter_rows(named=True)]
            if data:
                print(f"deleting from {self.name}({self.id})")
                ss_api.delete_rows(self.id, data)
                self.data.remove(rows)
                Table.config.serialize()
                return len(data)
        return 0
