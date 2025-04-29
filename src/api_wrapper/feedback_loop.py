from src.Table import Table
from src.Config import Config, threader
import polars as pl
from polars import col, lit
from typing import List


def feedback_loop(tables: List, config: Config, columns: List):
    print("Starting ...")

    def _feedback_loop(table: Table):
        print(f"Getting {table.name} from smartsheet")

        table.load_from_ss()
        ss_df = table.data  # current smartsheet records

        # new records from trax refresh
        new_df = pl.read_excel(
            table.src,
            schema_overrides=ss_df.select(
                [col for col in ss_df.columns if not col.startswith("_")]
            ).collect_schema(),
        )

        # join the two sets
        existing_records_df = ss_df.join(
            new_df,
            # on=["AC", "FLEET", "MAIN_PN", "PN", "VENDOR"],
            on=columns,
            how="left",
            validate="1:1",
        )

        # Filter out NO_ACTION rows before determining new records
        new_records_df = new_df.filter(col("PROPOSED_ACTION") != lit("NO_ACTION")).join(
            ss_df,
            # on=["AC", "FLEET", "MAIN_PN", "PN", "VENDOR"],
            on=columns,
            how="anti"
        )

        full_set_df = pl.concat([existing_records_df, new_records_df], how="diagonal")

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
            # pl.when(update_row & ~insert_row)
            # .then(True)
            # .otherwise(False)
            # .alias("_UPDATE"),
            # pl.when(insert_row).then(True).otherwise(False).alias("_INSERT"),
        ).select([col for col in ss_df.columns] )
            # + ["_UPDATE"] + ["_INSERT"])

        table.data = df
        num_update = table.update_ss(rows=update_row & ~insert_row, cols=["Status"])
        num_insert = table.insert_ss(rows=insert_row)

        print(f"{table.name}: {num_update} updated rows | {num_insert} inserted rows")

    threader(_feedback_loop, tables, config.threadcount)
