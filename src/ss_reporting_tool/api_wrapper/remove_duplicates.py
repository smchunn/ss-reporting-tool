from ss_reporting_tool.Table import Table
from ss_reporting_tool.Config import CFG, threader
import polars as pl
from polars import col, lit
from typing import List


def remove_duplicates(tables: List, columns: List):
    """Remove duplicates from smartsheet reports"""
    print("Removing smartsheet duplicates")

    def _remove_dupes(table: Table):
        print(f"Getting {table.name} from smartsheet")
        table.load_from_ss()
        print(table.data.shape)
        ss_df = table.data  # current smartsheet records

        rows_to_delete = (
            # pl.struct("AC", "FLEET", "PN", "NHA", "TOP", "LEVEL")
            pl.struct(columns)
            .is_first_distinct()
            .not_()
        )

        table.data = ss_df
        num_delete = table.delete_ss(rows=rows_to_delete)
        print(f"{table.name} Deleted rows: {num_delete}")

    threader(_remove_dupes, tables, CFG.threadcount)
