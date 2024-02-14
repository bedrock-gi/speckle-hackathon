import warnings

import streamlit as st
import pandas as pd
import plotly.express as px

from specklepy.api.client import SpeckleClient
from specklepy.api.credentials import get_account_from_token
from specklepy.logging.exceptions import SpeckleWarning


# Catch SpeckleWarnings as if they were errors.
# This is useful further down below when authenticating.
# When authentication fails, specklepy gives a warning.
warnings.filterwarnings(action="error", category=SpeckleWarning)


# Website HTML <header> title and favicon
st.set_page_config(page_title="Project Activity", page_icon="📊")

# Containers
header = st.container()
auth_input = st.container()
project_input = st.container()
model_input = st.container()
viewer = st.container()
report = st.container()
graphs = st.container()

# Title block
header.title("Speckle Project Activity App 📈")
with header.expander("About this app 🔽", expanded=True):
    st.markdown(
        """This is a beginner web app developed using Streamlit. The goal was to understand how to interact with Speckle API using SpecklePy, 
        analyze what is received and its structure. This was an easy and fun experiment.
        """
    )

# Layout inside user_input container
auth_input.subheader("Connect to your project")
server_col, token_col = auth_input.columns([1, 2])

# Speckle Server URL & Token input fields
speckle_server = server_col.text_input(
    "Speckle server URL",
    "app.speckle.systems",
    help="Speckle server URL to connect to.",
)
speckle_token = token_col.text_input(
    "Speckle token",
    "e.g. 087fea753d12f91a6f692c8ea087c1bf4112e93ed7",
    help="If you don't know how to get your token, take a look at [this Speckle docs page](<https://speckle.guide/dev/tokens.html>)👈",
)

# Authenticate with Speckle server
try:
    account = get_account_from_token(speckle_token, speckle_server)
    client = SpeckleClient(host=speckle_server)
    client.authenticate_with_account(account)
    # print(account)
except SpeckleWarning:
    auth_input.error(
        "Oh no 😨 The Speckle server - token combination is incorrect or invalid.",
        icon="🚨",
    )
    auth_input.markdown(
        "Take a look at [this Speckle docs page](<https://speckle.guide/dev/tokens.html>)👈 to find out how you can obtain a Speckle token."
    )
    st.stop()

# Select Speckle project
projects = client.stream.list()
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
            "Description": model.description,
            "Latest version author": model.commits.items[0].authorName,
            "Latest version commit message": model.commits.items[0].message,
            "ModelID": model.id,
        }
        model_df.append(model_dict)

if not model_df:
    model_input.error(
        "Oh no 😨 It seems your Speckle project doesn't contain any models. Try adding some data to your Speckle project 🤩",
        icon="🚨",
    )
    st.stop()

model_input.markdown(
    "Select the models of this project that you want to show (together) in the Speckle viewer below"
)
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


# Show the selected (federated) model in a Speckle viewer
with viewer:
    st.components.v1.iframe(
        src=f"https://app.speckle.systems/projects/{selected_project.id}/models/{selected_models_str}#embed=%7B%22isEnabled%22%3Atrue%7D",
        height=500,
    )

