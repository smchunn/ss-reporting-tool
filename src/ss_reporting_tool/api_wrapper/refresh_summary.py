from ss_reporting_tool.Config import Config
from ss_reporting_tool.Report import Report
from ss_reporting_tool.Summary import Summary
from ss_reporting_tool.Utils import threader, log
import polars as pl
from polars import col, lit
from typing import List, Dict, Optional, Callable, Tuple, Any




def refresh_summary(cfg: Config, summaries: List[Summary]):
    """
    make smartsheet table match newly generated excel table without changing _id's
    """
    print("Starting summary feedback ...")
    reports = []
    for summary in summaries:
        for table in cfg.tables:
            if isinstance(table, Report):
                for tag in summary.tags:
                    if tag not in table.tags:
                        return
                reports.append(table)


    threader(lambda x: x.load_from_ss(), reports, cfg.threadcount)

    return
    if not reports:
        return
    df = reports[0].data
    for table in reports[1:]:
        df.vstack(table.data)

    for summary in summaries:
        pivot_index = summary.get("pivot_index")
        pivot_column = summary.get("pivot_columns")
        filter = summary.get("filter")
        headers = summary.get("headers")
        if (
            isinstance(pivot_index, (str | None))
            and isinstance(pivot_column, str | list)
            and isinstance(filter, pl.Expr | None)
            and isinstance(headers, list)
            and all(isinstance(x, str) for x in headers)
        ):
            summary = summary.buildSummary(
                df,
                pivot_column=pivot_column,
                headers=headers,
                pivot_index=pivot_index,
                filter_expr=filter,
            )

    def _refresh_summary(table: Report):
        print(f"Getting {table.name} from Smartsheet")
        table.load_from_ss()
        ss_df = table.data  # current Smartsheet records
        if not table.src:
            log(f"failed attempt to load from file: {table.name} ")
            return

        # Load new records from Excel
        new_df = pl.read_excel(
            table.src,
            schema_overrides=ss_df.select(
                [col for col in ss_df.columns if not col.startswith("_")]
            ).collect_schema(),
        )

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

    # threader(_refresh_summary, tables, CFG.threadcount)
