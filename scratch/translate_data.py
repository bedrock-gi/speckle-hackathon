import pandas as pd
import zipfile
import os
import glob

from src.app.speckle_io import ags3_to_dfs


csv_path = (
    "/Users/jamesholcombe/Documents/git/speckle-hackathon/RelevantReportNo (1).csv"
)

folder = "/Users/jamesholcombe/Documents/git/speckle-hackathon/data/drive-download-20240607T142246Z-001/GI_AGS"

df = pd.read_csv(csv_path)
report_nums = set(df["REPORT_NO"].tolist())
report_nums = set([int(x) for x in report_nums])
print("Number of report numbers: ", len(report_nums))


# for file in os.listdir(folder):
#     if file.endswith(".zip") and int(file.replace(".zip", "")) in report_nums:
#         with zipfile.ZipFile(os.path.join(folder, file), "r") as zip_ref:
#             zip_ref.extractall(folder)
#             print(f"Extracted {file}")
#             # get list of files in the zip
#             files = zip_ref.namelist()
#             print(files)

# TODO: Extract the AGS files that are in the list of report numbers
# create 3 points for each borehole
# upload to speckle

ags_file_paths = []


for report_name in os.listdir(folder):
    if ".zip" in report_name:
        continue

    if int(report_name) in report_nums:
        # print(f"Extracting {report_name}")
        search_path = os.path.join(folder, report_name)
        for f in glob.glob(os.path.join(folder, report_name, "*.ags")):

            ags_file_paths.append(f)

data_strings = []
for file_path in ags_file_paths:
    with open(file_path, "r") as f:
        try:
            data_strings.append(f.read())
        except Exception as e:
            print(f"Could not read {file_path}")


data_dfs = [ags3_to_dfs(data_string) for data_string in data_strings]
data_dfs = [data_df for data_df in data_dfs if "WETH" in data_df.keys()]

df_holes = pd.concat([data_df["HOLE"] for data_df in data_dfs], ignore_index=True)
df_weth = pd.concat([data_df["WETH"] for data_df in data_dfs], ignore_index=True)
common_keys = set.intersection(*[set(data_df.keys()) for data_df in data_dfs])


print("Number of AGS files extracted: ", len(data_dfs))
