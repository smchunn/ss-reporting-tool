from ss_reporting_tool.Config import Config
from ss_reporting_tool.Report import Report
from ss_reporting_tool.Utils import threader
from ss_reporting_tool.api_wrapper.set_sheet import set_sheet
import ss_api
import polars as pl
from polars import col, lit
from typing import List


def reformat_sheet(cfg: Config, tables: List):
    def _reformat_sheet(table: Report):
        def _clear_sheet(table: Report):
            print(f"clearing {table.target_id}...")
            ss_api.delete_all_rows(table.target_id)
            print("done...")

        def _move_sheet(table: Report):
            print(f"moving {table.name}...")
            ss_api.move_rows(table.target_id, table.id)
            print("done...")

        def _delete_sheet(table: Report):
            print(f"deleting {table.name}...")
            ss_api.delete_sheet(table.id)
            print("done...")

        def _rename_sheet(table: Report):
            print(f"renaming {table.target_id}...")
            ss_api.rename_sheet(table.target_id, table.name)
            print("done...")

        set_sheet(cfg, [table])
        _clear_sheet(table)
        _move_sheet(table)
        _delete_sheet(table)
        _rename_sheet(table)

    print("Starting ...")

    threader(_reformat_sheet, tables, cfg.threadcount)
