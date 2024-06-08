from io import StringIO
import warnings

import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit.components.v1 as components

from specklepy.api.client import SpeckleClient
from specklepy.api.credentials import get_account_from_token
from specklepy.logging.exceptions import SpeckleWarning
import os
from dotenv import load_dotenv
from speckle_io import create_borehole_data_in_speckle

load_dotenv()

# Catch SpeckleWarnings as if they were errors.
# This is useful further down below when authenticating.
# When authentication fails, specklepy gives a warning.
warnings.filterwarnings(action="error", category=SpeckleWarning)


# Website HTML <header> title and favicon
st.set_page_config(page_title="Project Activity", page_icon="📊")
project_input = st.sidebar.container(border=True)
project_input.subheader("Connect to your project")


# auth_input = st.container()
model_input = st.sidebar.container(border=True)
model_input.subheader("Select models to show in the Speckle viewer")


viewer = st.container()  # width and height are set to 500px to fit the iframe viewer

file_container = st.sidebar.container(border=True)
file_container.subheader("Upload AGS files")


# Layout inside user_input container
# server_col, token_col = auth_input.columns([1, 2])
speckle_server = "app.speckle.systems"
speckle_token = os.environ["TOKEN"]
client = SpeckleClient(host=speckle_server)
client.authenticate_with_token(speckle_token)


# Select Speckle project
projects = client.stream.list(5)
if not projects:
    model_input.error(
        "Oh no 😨 It seems your Speckle account doesn't contain any projects yet on the given server. Try creating a new Speckle project and adding some data to that Speckle project 🤩",
        icon="🚨",
    )
    st.stop()

project_names = [p.name for p in projects]
project_name = project_input.selectbox(
    label="Select your Speckle project",
    options=project_names,
    help="Select your Speckle stream from the dropdown",
)
selected_project = projects[project_names.index(project_name)]


# Select the Speckle model for the selected Speckle project
models = client.branch.list(selected_project.id)
model_df = []
for model in models:
    if model.commits.totalCount > 0:
        model_dict = {
            "Show": False,
            "Model name": model.name,
            "ModelID": model.id,
        }
        model_df.append(model_dict)

if not model_df:
    model_input.error(
        "Oh no 😨 It seems your Speckle project doesn't contain any models. Try adding some data to your Speckle project 🤩",
        icon="🚨",
    )
    st.stop()

model_input.markdown("Select the models to show (together) in the Speckle viewer")
model_df = pd.DataFrame(model_df)
edited_models_df = model_input.data_editor(
    model_df,
    hide_index=True,
    disabled=[
        "Model name",
        "Description",
        "Latest version author",
        "Latest version commit message",
        "ModelID",
    ],
)


selected_model_ids = edited_models_df[edited_models_df["Show"]]["ModelID"]
selected_models_str = ",".join(selected_model_ids.to_list())

uploaded_files = file_container.file_uploader(
    "Upload AGS files", type=["ags"], accept_multiple_files=True
)

upload_button = file_container.button("Upload to Speckle", disabled=not uploaded_files)
# fileuploader

if uploaded_files and upload_button:

    ags_data_strings = []
    for uploaded_file in uploaded_files:
        # To convert to a string based IO:
        stringio = StringIO(uploaded_file.getvalue().decode("utf-8", errors="ignore"))

        # To read file as string:
        string_data = stringio.read()
        ags_data_strings.append(string_data)

    create_borehole_data_in_speckle(client, ags_data_strings, selected_project.id)


with viewer:

    if not selected_models_str:
        st.warning("Please select a model to show in the Speckle viewer")
        st.stop()

    if not selected_project:
        st.warning("Please select a project to show in the Speckle viewer")
        st.stop()

    components.iframe(
        src=f"https://app.speckle.systems/projects/{selected_project.id}/models/{selected_models_str}#embed=%7B%22isEnabled%22%3Atrue%7D",
        height=800,
        width=1200,
    )
