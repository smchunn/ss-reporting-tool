import pandas as pd
import sys
import os

if len(sys.argv) != 3:
    print("Usage: python pivot_trax.py <input_folder_path> <output_folder_path>")
    sys.exit(1)

input_folder = sys.argv[1]
output_folder = sys.argv[2]

# Ensure the output folder exists
if not os.path.isdir(output_folder):
    print(f"Error: Output folder '{output_folder}' does not exist.")
    sys.exit(1)

input_file = os.path.join(input_folder, 'merged_normal.xlsx')
output_file = os.path.join(output_folder, 'pivoted_final.xlsx')

print(f"Reading: {input_file}")

df = pd.read_excel(input_file, dtype=str).fillna("")

# All columns except the normalization columns
pivot_columns = [c for c in df.columns if c not in ("AC", "Action", "ADD EFFECTIVITY", "VALIDATE EFFECTIVITY")]

grouped = df.groupby('PN')
rows = []

for pn, group in grouped:
    out_row = {}
    for col in pivot_columns:
        out_row[col] = group.iloc[0][col]

    # Drop 'Complete' rows unless all are complete
    non_complete_group = group[group['STATUS'].str.strip() != 'Complete']
    if not non_complete_group.empty:
        effective_group = non_complete_group
    else:
        effective_group = group

    add_ac_list = effective_group[effective_group["Action"] == "ADD EFFECTIVITY"]["AC"].tolist()
    val_ac_list = effective_group[effective_group["Action"] == "VALIDATE EFFECTIVITY"]["AC"].tolist()
    out_row["ADD EFFECTIVITY"] = "\n".join(add_ac_list)
    out_row["VALIDATE EFFECTIVITY"] = "\n".join(val_ac_list)

    statuses = set(
        str(s).strip() for s in effective_group["STATUS"] if str(s).strip() != ""
    )
    if not non_complete_group.empty:
        if len(statuses) == 1:
            out_row["STATUS"] = statuses.pop()
        else:
            out_row["STATUS"] = "In-Work"
    else:
        out_row["STATUS"] = "Complete"

    rows.append(out_row)

pivoted_df = pd.DataFrame(rows)

# Reorder columns
first_cols = [col for col in pivot_columns if col in pivoted_df.columns]
out_cols = first_cols + ["ADD EFFECTIVITY", "VALIDATE EFFECTIVITY"]
if "STATUS" in pivoted_df.columns and "STATUS" not in out_cols:
    out_cols.append("STATUS")
for col in pivoted_df.columns:
    if col not in out_cols:
        out_cols.append(col)
pivoted_df = pivoted_df[out_cols]

print(f"Saving to: {output_file}")
pivoted_df.to_excel(output_file, index=False)
print(f'Pivot complete. Output saved to {output_file}')