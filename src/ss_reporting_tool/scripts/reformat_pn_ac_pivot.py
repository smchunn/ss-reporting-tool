import os
import polars as pl

FOLDER_PATH = '/Users/silas.bash/Library/CloudStorage/OneDrive-MMC/SmartSheet_API/ACA/data'
OUTPUT_FOLDER = '/Users/silas.bash/Library/CloudStorage/OneDrive-MMC/SmartSheet_API/ACA/processed'
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

all_data = []

# 1. Read all Excel files into Polars DataFrames
for filename in os.listdir(FOLDER_PATH):
    if filename.endswith('.xlsx'):
        file_path = os.path.join(FOLDER_PATH, filename)
        df = pl.read_excel(file_path)
        df = df.rename({col: col.upper() for col in df.columns})
        all_data.append(df)

# 2. Combine all data
df_all = pl.concat(all_data, how="vertical_relaxed")

# 3. Identify group keys and all columns
group_keys = ['CATEGORY', 'PN']

# Columns to exclude from output (TRAX_HEADER_EFFECTIVE and EFFECTIVITY_PN_INTERCHANGEABLE are NOT excluded)
exclude_columns = [
    "PROPOSED_ACTION", "AC", "EFFECTIVE",
    "PRIORITY", "FEEDBACK", "REPORT_DATE", "REPORT_WEEK"
]

all_columns = df_all.columns
# Exclude group keys and excluded columns
other_columns = [
    col for col in all_columns
    if col not in group_keys and col not in exclude_columns
]

# 4. Build aggregation expressions for all columns except group keys and excluded
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

# 5. Add Effectivity columns (always calculated from AC/PROPOSED_ACTION)
agg_exprs += [
    pl.col("AC").filter(pl.col("PROPOSED_ACTION") == "ADD_EFFECTIVITY").unique().sort().alias("Add Effectivity"),
    pl.col("AC").filter(pl.col("PROPOSED_ACTION") == "VALIDATE_EFFECTIVITY").unique().sort().alias("Validate Effectivity"),
]

# 6. Group and aggregate
agg_df = (
    df_all
    .group_by(group_keys)
    .agg(agg_exprs)
)

# 7. Convert effectivity lists to newline-separated strings
agg_df = (
    agg_df
    .with_columns([
        pl.col("Add Effectivity").list.eval(pl.element().cast(pl.String)).list.join(chr(10)).alias("Add Effectivity"),
        pl.col("Validate Effectivity").list.eval(pl.element().cast(pl.String)).list.join(chr(10)).alias("Validate Effectivity"),
    ])
)

# 8. Prepare final column order
desired_order = [
    "STATUS", "Add Effectivity", "Validate Effectivity", "PN", "MAIN_PN", "ASSIGNMENT", "NOTES", "CATEGORY",
    "DESCRIPTION", "CHAPTER", "SECTION", "TRAX_HEADER_EFFECTIVE", "EFFECTIVITY_PN_INTERCHANGEABLE", "FLEET",
    "VENDOR", "CREATED_DATE", "MODIFIED_DATE"
]

# Add any other columns not in the desired order, preserving their original order
remaining_columns = [
    col for col in agg_df.columns
    if col not in desired_order
]

final_column_order = [col for col in desired_order if col in agg_df.columns] + remaining_columns

agg_df = agg_df.select(final_column_order)

# 9. Sort by CATEGORY, then PN
agg_df = agg_df.sort(group_keys)

# 10. Split by CATEGORY and write output files
for category_tuple, group in agg_df.group_by("CATEGORY"):
    category = category_tuple if isinstance(category_tuple, str) else category_tuple[0]
    fleet = group["FLEET"][0] if "FLEET" in group.columns else "FLEET"
    out_filename = f"{fleet}_{category}.xlsx"
    out_path = os.path.join(OUTPUT_FOLDER, out_filename)
    group.write_excel(out_path)
    print(f"Written: {out_path}")