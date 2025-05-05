from ss_reporting_tool.Table import Table
from ss_reporting_tool.Config import CFG, threader
import polars as pl
from os.path import isfile
from polars import col, lit
from typing import List


def refresh_summary(tables: List[Table]):
    """
    make smartsheet table match newly generated excel table without changing _id's
    """
    print("Starting summary feedback ...")

    def _refresh_summary(table: Table):
        print(f"Getting {table.name} from Smartsheet")
        table.load_from_ss()
        ss_df = table.data  # current Smartsheet records
        print(ss_df.head())
        # Load new records from Excel
        new_df = pl.read_excel(
            table.src,
            schema_overrides=ss_df.select(
                [col for col in ss_df.columns if not col.startswith("_")]
            ).collect_schema(),
        )
        print(new_df.head())
        if ss_df.shape[0] == 1 and ss_df.shape[0] == new_df.shape[0]:
            joined_df = new_df.join(ss_df, on=pl.lit(True), how="full")
            cols_to_drop = [col for col in joined_df.columns if col.endswith("_right")]
            filtered_df = joined_df.drop(cols_to_drop)
            table.data = filtered_df
            table.update_ss()
        else:
            joined_df = new_df.join(ss_df, on=["AC"], how="full")
            cols_to_drop = [col for col in joined_df.columns if col.endswith("_right")]
            filtered_df = joined_df.drop(cols_to_drop)
            table.data = filtered_df
            table.update_ss()

    threader(_refresh_summary, tables, CFG.threadcount)
