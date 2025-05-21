from ss_reporting_tool.Config import Config
from ss_reporting_tool.Report import Report
from ss_reporting_tool.Utils import threader
import os, logging
import ss_api
import polars as pl
from polars import col, lit
from typing import List, Dict, Callable, Union


def get_sheet(cfg: Config, tables: List):

    def _get_sheet(table: Report):
        if not cfg.data_dir:
            logging.debug(f"failed attempt to load from file: {table.name} ")
            return
        print(f"Getting {table.name} as xlsx")
        save_path = os.path.join(cfg.data_dir, f"{table.name}.xlsx")
        ss_api.get_sheet_as_xlsx(table.id, save_path)
        print(f"Saved {table.name} to {save_path}")

    print("Starting ...")

    threader(_get_sheet, tables, cfg.threadcount)
