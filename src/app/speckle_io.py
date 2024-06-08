from typing import Dict, List
import pandas as pd
import datetime as dt
import os
import re

from dotenv import load_dotenv
import pandas as pd

from specklepy.api.client import SpeckleClient
from specklepy.api.credentials import get_default_account
from specklepy.objects import Base
from specklepy.objects.geometry import Point, Line
from specklepy.transports.server import ServerTransport
from specklepy.api import operations


def create_borehole_data_in_speckle(client, ags_data: List[str], stream_id: str):
    """Create borehole data in Speckle from AGS 3 files.

    Args:
        ags_paths (List[str]): A list of file paths to AGS 3 files.
        stream_id (str): The ID of the Speckle stream to which the borehole data will be added.

    """

    tables = []
    for data_string in ags_data:

        ags_dfs = ags3_to_dfs(data_string)

        hole_table = ags_dfs["HOLE"]

        tables.append(hole_table)
    hole_table = pd.concat(tables, ignore_index=True)

    # coerce all columns to numeric, by trying to convert to float
    hole_table = hole_table.apply(pd.to_numeric, errors="coerce")

    # drop cols with all NaNs
    hole_table.dropna(axis=1, how="all", inplace=True)

    to_speckle(client, stream_id, hole_table)


def ags3_to_dfs(ags_data: str) -> Dict[str, pd.DataFrame]:
    """Convert AGS 3 data to a dictionary of pandas DataFrames.

    Args:
        ags_data (str): The AGS 3 data as a string.

    Returns:
        Dict[str, pd.DataFrame]: A dictionary of pandas DataFrames, where each key represents a group name from AGS 3 data,
        and the corresponding value is a DataFrame containing the data for that group.
    """
    ags_dfs = {}
    group = None
    headers = ["", "", ""]
    data_rows = [["", "", ""], ["", "", ""], ["", "", ""]]

    for i, line in enumerate(ags_data.split("\n")):
        # In AGS 3.1 group names are prefixed with **
        if line.startswith('"**'):
            if group:
                ags_dfs[group] = pd.DataFrame(data_rows, columns=headers)
            pattern = re.compile("([A-Z?])\w+")
            group = pattern.search(line).group()

            data_rows = []

        # In AGS 3.1 header names are prefixed with *
        elif line.startswith('"*'):
            new_headers = line.split('","')
            new_headers = [h.strip(' "*') for h in new_headers]

            # Some groups have headers that span multiple lines
            # new_headers[-2] is used because:
            #   1. the first columns in AGS tables are mostly foreign keys
            #   2. the last column in AGS table is often FILE_FSET
            if new_headers[-2].split("_")[0] == headers[-2].split("_")[0]:
                headers = headers + new_headers
            else:
                headers = new_headers

        # Skip lines where group units are defined, these are defined in the AGS 3.1 data dictionary
        elif line.startswith('"<UNITS>"'):
            continue

        # The rest of the lines contain data, "<CONT>" lines, or are worthless
        else:
            data_row = line.split('","')
            if len("".join(data_row)) == 0:
                print(f"No data was found on line {i}. Last Group: {group}")
                continue
            elif len(data_row) != len(headers):
                # TODO: This should be a warning
                print(
                    f"The number of columns on line {i} doesn't match the number of columns of group {group}"
                )

            # Append continued lines (<CONT>) to the last data_row
            elif data_row[0] == '"<CONT>':
                data_row = [d.strip(' "') for d in data_row]
                last_data_row = data_rows[-1]
                for j, datum in enumerate(data_row):
                    if datum and datum != "<CONT>":
                        last_data_row[j] += datum
            else:
                data_row = [d.strip(' "') for d in data_row]
                data_rows.append(data_row)

    # Also add the last group's df to the dictionary of AGS dfs
    ags_dfs[group] = pd.DataFrame(data_rows, columns=headers)

    return ags_dfs


def to_speckle(client, stream_id: str, df_hole_table: pd.DataFrame):

    # next create a server transport - this is the vehicle through which you will send and receive
    transport = ServerTransport(client=client, stream_id=stream_id)

    hash = create_hash(df_hole_table, transport)

    commit_hash(hash, client, stream_id)


def get_stream(stream_id):
    # Authenticate with Speckle server
    speckle_server = "app.speckle.systems"
    speckle_token = os.environ["TOKEN"]
    client = SpeckleClient(host=speckle_server)
    account = get_default_account()

    client.authenticate_with_token(speckle_token)

    # create a new stream. this returns the stream id
    if not stream_id:
        stream_id = client.stream.create(name="a shiny new stream")

    # use that stream id to get the stream from the server
    new_stream = client.stream.get(id=stream_id)
    return client, stream_id


def create_hash(df: pd.DataFrame, transport):

    df["z_top"] = df["HOLE_GL"]
    df["z_bot"] = df["HOLE_GL"] - df["HOLE_FDEP"]
    records = df.to_dict(orient="records")
    newObj = Base()

    lines = [
        Line(
            start=Point(x=row["HOLE_NATE"], y=row["HOLE_NATN"], z=row["z_top"]),
            end=Point(x=row["HOLE_NATE"], y=row["HOLE_NATN"], z=row["z_bot"]),
        )
        for row in records
    ]

    for i, (line, record) in enumerate(zip(lines, records)):
        line["userStrings"] = record
        line_name = record.get("HOLE_ID", f"line_{i}")
        newObj[line_name] = line

    hash = operations.send(base=newObj, transports=[transport])
    return hash


def commit_hash(hash, client, stream_id) -> str:
    # you can now create a commit on your stream with this object
    return client.commit.create(
        stream_id=stream_id,
        object_id=hash,
        message=f"these are lines I made in speckle-py at {dt.datetime.now()}",
    )
