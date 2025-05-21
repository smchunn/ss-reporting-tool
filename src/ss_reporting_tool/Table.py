# ss_reporting_tool/src/ss_reporting_tool/Table.py
import os, logging
import toml, json
import ss_api
import polars as pl
from datetime import datetime, timezone
from typing import List, Dict, Callable, Union, Set, Optional, TYPE_CHECKING


class Table:

    def __init__(self, cfg, name, id, folder_id, last_update, tags, metadata) -> None:
        from ss_reporting_tool.Config import Config

        self.cfg: Config = cfg
        self.name: str = name
        self.id: str = id
        self.folder_id: str = folder_id
        self.last_update = last_update
        self.tags: Set = tags
        self.metadata: Dict = metadata

        self.data: pl.DataFrame = pl.DataFrame()
        self.sheet_id_to_col_map = None
        self.sheet_col_to_id_map = None

    def __repr__(self) -> str:
        return f"{self.name}::{self.id or "***"}"

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
        if (
            logging.getLogger().getEffectiveLevel() == logging.DEBUG
            and self.cfg.data_dir
        ):
            with open(
                os.path.join(self.cfg.data_dir, f"{self.name}.json"), "w"
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
            for cell in row["cells"]:
                column_title = self.sheet_id_to_col_map[cell["columnId"]]
                row_data[column_title] = cell.get("value", None)
            data.append(row_data)

        self.data = pl.DataFrame(data, infer_schema_length=None)
        # .filter(col("AC").is_not_null())

    def export_to_excel(self) -> None:
        if not self.cfg.data_dir:
            return
        excel_fp = os.path.join(self.cfg.data_dir, f"{self.name}.xlsx")
        self.data.write_excel(
            workbook=excel_fp,
            worksheet="audit",
            table_name="audit_table",
            table_style="Table Style Medium 9",
            autofit=True,
            freeze_panes=(1, 0),
        )

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
                self.cfg.serialize()
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
                self.cfg.serialize()
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
                self.data = self.data.filter(rows)
                self.cfg.serialize()
                return len(data)
        return 0

    def to_dict(self) -> Dict:
        table_dict = {
            "id": self.id,
            "date": (
                self.last_update.strftime("%Y-%m-%d")
                if isinstance(self.last_update, datetime)
                else str(self.last_update)
            ),
            "tags": list(self.tags) if self.tags else [],
            "metadata": self.metadata if self.metadata else {},
        }
        return table_dict

    def get(self, key: str):
        metadata = self.metadata
        while "." in key and isinstance(metadata, dict):
            i = key.index(".")
            metadata = metadata.get(key[0:i])
            key = key[i + 1 :]
        if not isinstance(metadata, dict):
            return None

        return metadata.get(key)
