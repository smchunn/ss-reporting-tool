import polars as pl
from typing import Dict, Any
import json
from ss_api import create_sheet


def polars_to_smartsheet(
    df: pl.DataFrame, sheet_name: str, folder_id: str, primary_col=0
) -> Dict | None:
    """
    Converts a Polars DataFrame and a sheet name to Smartsheet API JSON for creating a new sheet.
    """
    type_mapping = {
        pl.Boolean: {"type": "CHECKBOX"},
        pl.Int8: {"type": "TEXT_NUMBER"},
        pl.Int16: {"type": "TEXT_NUMBER"},
        pl.Int32: {"type": "TEXT_NUMBER"},
        pl.Int64: {"type": "TEXT_NUMBER"},
        pl.UInt8: {"type": "TEXT_NUMBER"},
        pl.UInt16: {"type": "TEXT_NUMBER"},
        pl.UInt32: {"type": "TEXT_NUMBER"},
        pl.UInt64: {"type": "TEXT_NUMBER"},
        pl.Float32: {"type": "TEXT_NUMBER"},
        pl.Float64: {"type": "TEXT_NUMBER"},
        pl.Utf8: {"type": "TEXT_NUMBER"},
        pl.Date: {"type": "DATE"},
        pl.Datetime: {"type": "DATE"},
        pl.Time: {"type": "TEXT_NUMBER"},
        pl.Categorical: {"type": "PICKLIST"},
    }

    columns_json = []
    for idx, col in enumerate(df.columns):
        dtype = df[col].dtype
        col_dict: Dict[str, Any] = {"title": col}

        mapped = None
        for polars_type, smartsheet_info in type_mapping.items():
            if dtype == polars_type:
                mapped = smartsheet_info.copy()
                break
        if mapped is None:
            mapped = {"type": "TEXT_NUMBER"}

        if idx == primary_col:
            col_dict["primary"] = True

        col_dict.update(mapped)
        columns_json.append(col_dict)

    result = {"name": sheet_name, "columns": columns_json}
    create_sheet(folder_id, result)
