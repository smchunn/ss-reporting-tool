from ss_reporting_tool.Config import Config
from ss_reporting_tool.Report import Report
from ss_reporting_tool.Summary import Summary
from ss_reporting_tool.Utils import threader, log
import polars as pl
from polars import col, lit
from typing import List, Dict, Optional, Callable, Tuple, Any


def create_generic_summary(
    df: pl.DataFrame,
    pivot_column: str | List[str],
    headers: List[str],
    pivot_index: Optional[str] = None,
    category_map: Optional[Dict[str, str]] = None,
    fill_null: int = 0,
    sort_by_index: bool = True,
    filter_expr: Optional[pl.Expr] = None,
    extra_processing: Optional[Callable] = None,
) -> pl.DataFrame:
    """
    Generate one or more pivot summaries and totals from a Polars DataFrame, grouped by specified columns.
    """
    if not isinstance(pivot_column, list):
        pivot_column = [pivot_column]

    # Apply optional category mapping
    if category_map and "CATEGORY" in df.columns:
        for x, y in category_map:
            df = df.with_columns(
                pl.when(pl.col("CATEGORY") == x)
                .then(lit(y))
                .otherwise(lit(x))
                .alias("CATEGORY")
            )

    # Apply optional filtering
    if filter_expr is not None:
        df = df.filter(filter_expr)

    df = df.group_by(pivot_column + [pivot_index]).count()
    df = df.drop_nulls(subset=pivot_column)

    # Group and pivot
    pivot_table = (
        df.pivot(
            index=pivot_index,
            on=pivot_column,
            values="count",
            aggregate_function="sum",
        )
    ).fill_null(fill_null)

    # Sort columns to desired order
    for col in headers:
        if col not in pivot_table.columns:
            pivot_table = pivot_table.with_columns(pl.lit(0).alias(col))
    pivot_table = pivot_table.select(headers)
    if sort_by_index and pivot_index in pivot_table.columns:
        pivot_table = pivot_table.sort(pivot_index)

    if pivot_index:
        sum_row = pivot_table.select(
            [
                pl.sum(col).alias(col)
                for col in pivot_table.columns
                if col != pivot_index
            ]
        ).with_columns(pl.lit("ALL").alias(pivot_index))
        sum_row = sum_row.select(pivot_table.columns)
        pivot_table = pl.concat([sum_row, pivot_table])

    # Extra processing hook
    if extra_processing:
        pivot_table = extra_processing(pivot_table)

    print(pivot_table.head())
    return pivot_table


def refresh_summary(cfg: Config, reports: List[Report], summaries: List[Summary]):
    """
    make smartsheet table match newly generated excel table without changing _id's
    """
    print("Starting summary feedback ...")

    for table in reports:
        table.load_from_ss()
    threader(lambda x: x.load_from_ss(), reports, cfg.threadcount)

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
            summary = create_generic_summary(
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
