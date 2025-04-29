from ss_reporting_tool.Table import Table
from ss_reporting_tool.Config import CFG, threader
import os
import ss_api
import polars as pl
from polars import col, lit
from typing import List, Dict, Callable, Union


def get_sheet(tables: List):

    def _get_sheet(table: Table):
        print(f"Getting {table.name} as xlsx")
        save_path = os.path.join(table.data_dir, f"{table.name}.xlsx")
        ss_api.get_sheet_as_xlsx(table.id, save_path)
        print(f"Saved {table.name} to {save_path}")

    print("Starting ...")

    threader(_get_sheet, tables, CFG.threadcount)
