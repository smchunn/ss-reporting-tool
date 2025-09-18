import os
import polars as pl
from sys import argv

# 1. Read input and output folder paths
INPUT_FOLDER = argv[1]
OUTPUT_FOLDER = argv[2]
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# 2. Find the single .xlsx file in the input folder
input_files = [f for f in os.listdir(INPUT_FOLDER) if f.lower().endswith('.xlsx')]
if len(input_files) != 1:
    raise ValueError(f"Expected exactly one .xlsx file in {INPUT_FOLDER}, found {len(input_files)}.")
input_file_path = os.path.join(INPUT_FOLDER, input_files[0])

# 3. Output file path
output_file_path = os.path.join(OUTPUT_FOLDER, "rpt_epr_pivot.xlsx")

# 4. Read the Excel file
df = pl.read_excel(input_file_path)
df = df.rename({col: col.upper() for col in df.columns})

# 5. Set group key
group_key = 'PN'

# 6. Identify all other columns (keep input order, except for ACTION)
other_columns = [col for col in df.columns if col != group_key and col != 'ACTION']

# 7. Aggregation expressions for all non-group columns
agg_exprs = []
for col in other_columns:
    nonblank = pl.col(col).cast(pl.String).filter(
        pl.col(col).cast(pl.String).is_not_null() & (pl.col(col).cast(pl.String).str.strip_chars() != "")
    )
    agg_exprs.append(
        pl.when(nonblank.n_unique() == 0)
        .then(pl.lit(""))  # All blank
        .when(nonblank.n_unique() == 1)
        .then(nonblank.first())  # Only one unique non-blank value
        .otherwise(pl.lit("Mixed"))  # More than one unique non-blank value
        .alias(col)
    )

# 8. Add Effectivity and ATA conflict columns
agg_exprs += [
    pl.col("AC").filter(pl.col("ACTION") == "ADD_EFFECTIVITY").unique().sort().alias("Add Effectivity"),
    pl.col("AC").filter(pl.col("ACTION") == "VALIDATE_EFFECTIVITY").unique().sort().alias("Validate Effectivity"),
    pl.col("PN").filter(pl.col("ACTION") == "NO_ACTION").unique().sort().alias("ATA conflict"),
]

# 9. Group and aggregate
agg_df = (
    df
    .group_by(group_key)
    .agg(agg_exprs)
)

# 10. Convert effectivity and ATA conflict lists to newline-separated strings
agg_df = (
    agg_df
    .with_columns([
        pl.col("Add Effectivity").list.eval(pl.element().cast(pl.String)).list.join(chr(10)).alias("Add Effectivity"),
        pl.col("Validate Effectivity").list.eval(pl.element().cast(pl.String)).list.join(chr(10)).alias("Validate Effectivity"),
        pl.col("ATA conflict").list.eval(pl.element().cast(pl.String)).list.join(chr(10)).alias("ATA conflict"),
    ])
)

# 11. Assemble final column order: PN, then other columns in input order, then effectivity/ATA columns last
final_column_order = (
    [group_key] +
    [col for col in other_columns if col != group_key] +
    ["Add Effectivity", "Validate Effectivity", "ATA conflict"]
)
agg_df = agg_df.select([col for col in final_column_order if col in agg_df.columns])

# 12. Sort by PN
agg_df = agg_df.sort(group_key)

# 13. Write the output to a single Excel file
agg_df.write_excel(output_file_path)
print(f"Written: {output_file_path}")