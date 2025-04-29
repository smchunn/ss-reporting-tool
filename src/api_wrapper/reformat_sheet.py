from src.Table import Table
from src.Config import Config, threader
from src.api_wrapper.set_sheet import set_sheet
import ss_api
import polars as pl
from polars import col, lit
from typing import List



def reformat_sheet(tables: List, config: Config):
    def _reformat_sheet(table: Table):
        def _clear_sheet(table: Table):
            print(f"clearing {table.target_id}...")
            ss_api.delete_all_rows(table.target_id)
            print("done...")


        def _move_sheet(table: Table):
            print(f"moving {table.name}...")
            ss_api.move_rows(table.target_id, table.id)
            print("done...")


        def _delete_sheet(table: Table):
            print(f"deleting {table.name}...")
            ss_api.delete_sheet(table.id)
            print("done...")


        def _rename_sheet(table: Table):
            print(f"renaming {table.target_id}...")
            ss_api.rename_sheet(table.target_id, table.name)
            print("done...")
        set_sheet([table], config)
        _clear_sheet(table)
        _move_sheet(table)
        _delete_sheet(table)
        _rename_sheet(table)

    print("Starting ...")
    set_sheet(tables, config)

    threader(_reformat_sheet, tables, config.threadcount)
