# CS340 Project Two | Dashboard
# Author: GCZ79
# Date: 12/09/2025
# Description: Dashboard to interact with "aac" database through CRUD Python Module.

from jupyter_dash import JupyterDash     # Setup the Jupyter version of Dash
JupyterDash.infer_jupyter_proxy_config() # URL detection and configuration
from dash import dcc, html               # core Dash components + HTML wrappers
from dash import dash_table              # table components
from dash.dependencies import Input, Output, State # callback functionality
from dash import callback_context        # determine which input triggers callback
from functools import lru_cache          # caching for performance optimization
import base64                            # image encoding
import dash_leaflet as dl                # interactive maps
import pandas as pd                      # manipulate DataFrames from MongoDB
import plotly.express as px              # create plots

from CRUD_Python_Module import AnimalShelter # Import class from CRUD Python module

#############################
# Data Manipulation / Model #
#############################

username = "aacuser"
password = "NoSQLNoParty"
shelter = AnimalShelter(username, password) # credentials and connection setup

# Helper function to get rescue type queries
# (DRY principle, we need the same queries in buttons and charts)
def get_rescue_query(button_id):
    queries = {
        ########################################## Water SAR Criteria:
        'btn1': {
            "animal_type": "Dog",                    # - Must be a dog
            "age_upon_outcome_in_weeks": {
                "$gte": 26,                          # - Age between 26 and 156 weeks
                "$lte": 156
            },
            "breed": {                               # - Specific working breeds:
                "$regex": (
                "(labrador retriever.*(mix|\\s*/|/)"   # - Labrador Retriever Mix
                "|chesapeake bay retriever"            # - Chesapeake Bay Retriever
                "|newfoundland)"                       # - Newfoundland
                ),
                "$options": "i"
            },
            "sex_upon_outcome": "Intact Female",     # - Intact Female 
            "outcome_type": {
            "$nin": ["Return to Owner", "Died", "Euthanasia"] # Optional search enhancement
            }
        },
        ########################################## Mountain or Wilderness SAR Criteria:
        'btn2': {
            "animal_type": "Dog",                    # - Must be a dog
            "age_upon_outcome_in_weeks": {
                "$gte": 26,                          # - Age between 26 and 156 weeks
                "$lte": 156
            },
            "breed": {                               # - Specific working breeds:
                "$regex": (
                "(german shepherd"                     # - German Shepherd
                "|alaskan malamute"                    # - Alaskan Malamute
                "|old english sheepdog"                # - Old English Sheepdog
                "|siberian husky"                      # - Siberian Husky
                "|rottweiler)"                         # - Rottweiler
                ),
                "$options": "i"
            },
            "sex_upon_outcome": "Intact Male",       # - Intact Male 
            "outcome_type": {
            "$nin": ["Return to Owner", "Died", "Euthanasia"] # Optional search enhancement
            }
        },
        ###################################### Disaster or Individual Tracking SAR Criteria:
        'btn3': {
            "animal_type": "Dog",                    # - Must be a dog
            "age_upon_outcome_in_weeks": {
                "$gte": 20,                          # - Age between 20 and 300 weeks
                "$lte": 300
            },
            "breed": {                               # - Specific working breeds:
                "$regex": (
                "(doberman pinscher"                   # - Doberman Pinscher
                "|german shepherd"                     # - German Shepherd
                "|golden retriever"                    # - Golden Retriever
                "|bloodhound"                          # - Bloodhound
                "|rottweiler)"                         # - Rottweiler
                ),
                  "$options": "i"
            },
            "sex_upon_outcome": "Intact Male",       # - Intact Male 
            "outcome_type": {
            "$nin": ["Return to Owner", "Died", "Euthanasia"] # Optional search enhancement
            }
        },
        'btn4': {}                              # Reset - empty query returns all records
    }
    return queries.get(button_id, {}) # Return the query dictionary for the given button ID

# Load initial data from MongoDB with error handling
try: # load all documents from MongoDB and convert to pandas DataFrame
    df = pd.DataFrame.from_records(shelter.read({}))
except Exception as e: # Handle any errors during data loading and print error message
    print(f"Error loading initial data from MongoDB: {e}") # Error message for debugging
    df = pd.DataFrame()                                    # Create empty DataFrame as fallback

# Remove MongoDB _id field (ObjectID not compatible with DataTable)
if '_id' in df.columns:                    # Check if _id column exists in DataFrame
    df.drop(columns=['_id'], inplace=True) # Remove _id column in-place (modifies original)

# --- Build Summary Table for Dataset Cardinality --- #
summary_data = [] # Initialize empty list to store summary information for each column
for col in df.columns:                       # Loop through all column names
    unique_vals = df[col].dropna().unique()  # Analyze each column's uniqueness
    unique_count = len(unique_vals)          # Counts distinct values per column

    # Categorize columns based on their cardinality (number of unique values)
    if unique_count <= 5:
        category_flag = "Categorical (up to 5 options)"
    elif unique_count <= 20:
        category_flag = "Semi-Categorical (5 to 20 options)"
    elif unique_count <= 50:
        category_flag = "Moderate-Cardinality (20 to 50 options)"
    else:
        category_flag = "High-Cardinality (more than 50 options)"

    summary_data.append({ # Append dictionary with column analysis to summary_data list
        "Field": col,                                          # Column name
        "Unique Values": unique_count,                         # Number of unique values
        "Sample Values": ", ".join(map(str, unique_vals[:5])), # Show first 5 unique values
        "Cardinality Classification": category_flag            # Descriptive label
    })

summary_df = pd.DataFrame(summary_data) # Convert the lists above into a pandas DataFrame

# Style rules | Color-coding based on classification
card_col = "Cardinality Classification" # Column name for classification
summary_style = [
    {
        'if': {'filter_query': f'{{{card_col}}} = "Categorical (up to 5 options)"'},
        'backgroundColor': '#d4f4dd', 'color': 'black' # green
    },
    {
        'if': {'filter_query': f'{{{card_col}}} = "Semi-Categorical (5 to 20 options)"'},
        'backgroundColor': '#fff2cc', 'color': 'black' # yellow
    },
    {
        'if': {'filter_query': f'{{{card_col}}} = "Moderate-Cardinality (20 to 50 options)"'},
        'backgroundColor': '#ffe0b2', 'color': 'black' # orange
    },
    {
        'if': {'filter_query': f'{{{card_col}}} = "High-Cardinality (more than 50 options)"'},
        'backgroundColor': '#f4cccc', 'color': 'black' # red
    }
]

#########################
# Encode image for Dash #
#########################
image_filename = 'Grazioso Salvare Logo.png' # Define the filename of the logo image
# Read the image file, encode it in base64, and decode to ASCII string for HTML embedding
encoded_image = base64.b64encode(open(image_filename, 'rb').read()).decode('ascii')

##############################
# Column visibility defaults #
##############################
# Define list of columns to hide by default in the DataTable
HIDDEN_COLS_DEFAULT = [
    "animal_id",     # Not all animals have one
    "date_of_birth", # Not relevant since we have their age
    "monthyear",     # Duplicate of date with different format
    "location_lat",  # Latitude of the rescue/foster location, no need to show it
    "location_long", # Longitude, same as above
    "age_upon_outcome_in_weeks" # Used for filtering, but no need to show this too
]
# Set columns visibility
VISIBLE_BY_DEFAULT = [col for col in df.columns if col not in HIDDEN_COLS_DEFAULT]

###########################
# Dashboard Layout / View #
###########################
# Initialize the Dash application with a specific name for internal reference
app = JupyterDash('CS340Dashboard')

# Define the main layout structure of the dashboard using nested HTML components
app.layout = html.Div([

    # Inject custom CSS to hide the superfluous "Toggle Columns" button 
    # (Created automatically by Dash when we hide some columns)
    html.Link(rel='stylesheet', 
              href='data:text/css,.dash-table-container%20.show-hide%7Bdisplay:none!important%7D'),

    # Logo and title
    html.Div([
        html.A( # Anchor tag to make logo clickable (links to SNHU (client) website)
            href="https://www.snhu.edu",    # Hyperling
            target="_blank",                # Open in new tab
            children=[                      # Children elements inside the anchor tag
                html.Img(                   # Image element for logo
                    src='data:image/png;base64,{}'.format(encoded_image), # Base64 encoded image source
                    style={"width": "80px"} # Inline CSS for image width
                )
            ]
        ),
        html.H1( # Main heading for dashboard title
            [
                "Grazioso Salvare | ",                                         # Main title text
                html.Span("GCZ79", style={"fontSize": "16px"}) # Small superscript
            ],
            style={"margin": "0", "padding": "0", "alignSelf": "center"}       # H1 styling
        )
    ],
    style={
        "display": "flex",          # Flexbox layout
        "flexDirection": "row",     # Horizontal alignment
        "justifyContent": "center", # Center horizontally
        "alignItems": "center",     # Center vertically
        "gap": "10px"               # Space between logo and title
    }),

    html.Hr(style={"border": "none", "height": "2px", "backgroundColor": "#c9134b"}), # Break line

    # Button row for rescue type filtering
    html.Div(className='buttonRow',     # Div for button container with CSS class
             style={'display': 'flex'}, # Flexbox display
             children=[                 # Children elements inside button container
                 html.Span("Rescue type:", style={'marginRight': '10px'}),
                 html.Button(id='btn1', n_clicks=0, style={                #-- Water rescue button --
                             "border": "3px solid #000000",                # Black border
                             "backgroundColor": "#ADD8E6",                 # Light blue background
                             "color": "#000000",                           # Black text
                             "marginRight": "10px",                        # Right margin
                             "padding": "6px 12px",                        # Internal padding
                             "borderRadius": "6px"},                       # Rounded corners
                             children='Water'),                            # Button text
                 html.Button(id='btn2', n_clicks=0, style={  #-- Mountain/Wilderness rescue button --
                             "border": "3px solid #000000",
                             "backgroundColor": "#90EE90",                 # Light green background
                             "color": "#000000",
                             "marginRight": "10px",
                             "padding": "6px 12px",
                             "borderRadius": "6px"},
                             children='Mountain or Wilderness'),
                 html.Button(id='btn3', n_clicks=0, style={ #-- Disaster/Individual Tracking button --
                             "border": "3px solid #000000",
                             "backgroundColor": "#F08080",                 # Light coral background
                             "color": "#000000",
                             "marginRight": "10px",
                             "padding": "6px 12px",
                             "borderRadius": "6px"},
                             children='Disaster or Individual Tracking'),
                 html.Button(id='btn4', n_clicks=0, style={                #-- Reset filters button --
                             "border": "3px solid #000000",
                             "backgroundColor": "#FFFFFF",                 # White background
                             "color": "#000000",
                             "marginRight": "10px",
                             "padding": "6px 12px",
                             "borderRadius": "6px"},
                             children='Reset Filters'),
             ]),
    
    html.Hr(style={"border": "none", "height": "2px", "backgroundColor": "#c9134b"}), # Break line

    # Main DataTable | Show 10 results per page, hide selected columns
    html.Div(
        id="datatable-container",                   # Unique identifier for callbacks to reference
        children=[                                  # List of components inside this div
            dash_table.DataTable(                   # Interactive table component from Dash
                id='datatable-id',                  # Unique identifier for callback targeting
                columns=[{"name": i, "id": i, "deletable": False, "selectable": True} # Column configuration
                         for i in df.columns],
                data=df.to_dict('records'),         # Convert DataFrame to list of dictionaries for DataTable
                filter_action="native",             # Enable built-in column filtering
                sort_action="native",               # Enable built-in column sorting
                sort_mode="multi",                  # Allow sorting by multiple columns
                selected_rows=[0],                  # Initially select first row
                row_selectable="single",            # For mapping callback to function properly
                page_size=10,                       # Number of rows per page
                hidden_columns=HIDDEN_COLS_DEFAULT, # Columns to hide initially
            ),
        ]
    ),
    
    html.Hr(style={"border": "none", "height": "2px", "backgroundColor": "#c9134b"}), # Break line

    # Map and Chart container | Collapsible, open by default
    html.Details([
        html.Summary("🗺️ Map & Summary Chart"), # Summary/title for collapsible section
        
        # Flex container for map + pie chart
        html.Div([ # Container div for map and chart
            # Map
            html.Div(
                id='map-id', # Div for map with unique ID
                style={"flex": "1", "padding": "5px", "minHeight": "400px"} 
            ),
    
            # Pie chart
            html.Div(
                dcc.Graph(id='pie-chart-id'), # Plotly graph component for pie chart
                style={"flex": "1", "padding": "5px", "minHeight": "400px"}
            )
        ], style={"display": "flex", "flexDirection": "row", "width": "100%"}) # Flexbox row layout
    ], open=True), # Collapsible section initially open
    
    html.Hr(style={"border": "none", "height": "2px", "backgroundColor": "#c9134b"}), # Break line

    # Column Visibility: show/hide columns | Collapsible, closed by default
    ## Helps users focus on relevant data by hiding unnecessary columns
    html.Details([ # Collapsible section for column visibility controls
        html.Summary("📦 Column Visibility"), # Section title with icon

        html.Div([ # Container for checklist and instructions
            dcc.Checklist(
                id="column-visibility-checklist", # Unique ID for callbacks
                options=[{"label": col, "value": col} for col in df.columns], # Options from DataFrame columns
                value=VISIBLE_BY_DEFAULT, # Apply column exclusions: Default checked items
                labelStyle={'display': 'block'} # CSS for label display
            ),
            html.Div(  # Help text for users
                "Check a box to show a column; uncheck to hide it.", # Instruction text
                style={"fontSize": "12px", "marginTop": "6px", "color": "#666"} # Styled help text
            )
        ], style={"margin": "10px"}) # Container margin
    ], open=False), # Collapsible section initially closed

    html.Hr(style={"border": "none", "height": "3px", "backgroundColor": "#c9134b"}), # Break line

    # Dataset Summary | Collapsible, closed by default
    html.Details([ # Collapsible section for dataset summary
        html.Summary("📝 Dataset Cardinality Summary"), # Section title with icon

        html.Button( # Button to trigger summary generation/update
            "Update Summary",           # Button text
            id="update-summary-btn",    # Unique button ID
            n_clicks=0,                 # Click counter initialization
            style={"margin": "10px 0"}  # Button styling with vertical margin
        ),

        html.Div(id="summary-table-container"), # Container div where summary table will be inserted
    ], open=False), # Collapsible section initially closed

    html.Hr(style={"border": "none", "height": "3px", "backgroundColor": "#c9134b"}), # Break line
])

###############################################
# Interaction Between Components / Controller #
###############################################

# --- Buttons ---
# Callback to filter DataTable data based on button clicks
@app.callback(                      # Decorator to define a Dash callback
    Output('datatable-id', 'data'), # Output: Update the data property of DataTable
    [Input('btn1', 'n_clicks'),     # Input triggers: Button click counters
     Input('btn2', 'n_clicks'),
     Input('btn3', 'n_clicks'),
     Input('btn4', 'n_clicks')]
)
def filter_data(btn1, btn2, btn3, btn4): # Callback function definition
    # Filter database based on rescue type button clicks
    # Uses centralized query function and error handling
    ctx = callback_context # Get callback context to identify trigger source

    if not ctx.triggered: # determine which button triggered the callback
        query = {}        # if no button was clicked, show full dataset
    else: 
        # otherwise, extract the ID of the clicked button from callback context
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        # Use centralized query function (DRY principle)
        query = get_rescue_query(button_id)
    
    try: # fetch data from MongoDB based on the query and convert it into a pandas DataFrame
        df2 = pd.DataFrame.from_records(shelter.read(query))
    except Exception as e:
        print(f"Error querying database: {e}") # Print error to console
        return []                              # Return empty list if query fails

    # remove MongoDB internal _id field as it is not compatible with Dash DataTable
    if "_id" in df2.columns:                    # Check if _id exists in new DataFrame
        df2.drop(columns=["_id"], inplace=True) # Remove _id column

    # convert DataFrame back to a list of dictionaries for DataTable
    return df2.to_dict('records')

# --- Highlight columns ---
# Callback to highlight selected columns in DataTable
@app.callback(
    Output('datatable-id', 'style_data_conditional'), # Output: Update conditional styling
    [Input('datatable-id', 'selected_columns')]       # Input: Selected columns from DataTable
)
def update_styles(selected_columns):
    if not selected_columns: # Check for empty selection 
        return [] # Return empty style list
    # Highlight the currently selected columns in the DataTable
    return [{ # Return list of style dictionaries
        'if': {'column_id': col}, # Condition: Apply to specific column
        'background_color': '#D2F3FF' # Light blue highlight color
    } for col in selected_columns] # List comprehension for all selected columns

#--- Change Table background color based on filters --
# Callback to match background color to rescue types buttons color
@app.callback(
    Output("datatable-container", "style"), # Output: Update the style CSS of the container
    Input("btn1", "n_clicks"),              # Button 1 click count (Water rescue)
    Input("btn2", "n_clicks"),              # Button 2 click count (Mountain/Wilderness rescue)
    Input("btn3", "n_clicks"),              # Button 3 click count (Disaster/Individual Tracking rescue)
    Input("btn4", "n_clicks"),              # Button 4 click count (Reset)
)
def update_table_background(btn1, btn2, btn3, btn4):
    ctx = callback_context # Get callback context to determine which input triggered the callback

    # Default table style
    style = {
        "padding": "10px",                          # Internal spacing
        "borderRadius": "8px",                      # Rounded corners
        "transition": "background-color 0.3s ease"  # Smooth color transition animation
    }

    if not ctx.triggered:  # If callback triggered without user action
        return style       # Return default style without background color
      
    # Extract which button was clicked from the triggered event
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # Match table background color to rescue type
    bg_colors = {
        "btn1": "#ADD8E6",   # Water (light blue)
        "btn2": "#90EE90",   # Mountain/Wilderness rescue (light green)
        "btn3": "#F08080",   # Disaster/Individual Tracking (light coral)
        "btn4": "#FFFFFF",   # Reset (white)
    }

    style["backgroundColor"] = bg_colors.get(button_id, "#FFFFFF") # Default to white if not found
    return style             # Return the complete style dictionary to update the container           

# --- Map ---
# Callback to update map based on filtered data and selection
@app.callback(
    Output('map-id', "children"), # Output: Update children of map container div
    [Input('datatable-id', "derived_viewport_data"), # Input: Currently visible/filtered data
     Input('datatable-id', "derived_virtual_selected_rows")] # Input: Currently selected row indices
)
def update_map(viewData, index): # Callback function with two inputs
    # viewData = the filtered table data
    # index = list of selected row indices
    
    if viewData is None or len(viewData) == 0:               # Check for no data or empty data
        return [                                             # Return default map when no data
            dl.Map(                                          # If true: Dash Leaflet Map component
                style={'width': '750px', 'height': '500px'}, # returns a map centered in
                center=[30.75, -97.48],                      # Austin, TX
                zoom=10,                                     # Default zoom level
                children=[dl.TileLayer(id="base-layer-id")]  # Base map layer
            )
        ]

    # Convert the dictionary data into a pandas DataFrame for easier manipulation
    dff = pd.DataFrame.from_dict(viewData)

    if dff.shape[1] < 15: # Check if the database has fewer than 15 columns
        return [
            dl.Map(                                          # If true
                style={'width': '750px', 'height': '500px'}, # returns same map centered in
                center=[30.75, -97.48],                      # Austin, TX
                zoom=10,
                children=[dl.TileLayer(id="base-layer-id")]
            )
        ]

    # Determine which row to display on the map with highlighted marker
    if index is None or len(index) == 0:    # If no rows are selected
        selected_row = 0                    # default to 0,
    else:                                   # otherwise
        selected_row = index[0]             # use the first selected row

    if selected_row >= len(dff):   # If row index exceeds the DataFrame length                 
        selected_row = 0           # default to 0

    # Show all filtered results as markers, with selected one highlighted
    # Helps coordinate multiple appointments in close proximity
    markers = []                    # Initialize empty list for map markers
    for idx, row in dff.iterrows(): # Loop through all rows in filtered DataFrame
        # Check if this row is the selected one
        is_selected = (idx == selected_row)
        
        # Create marker with different styling for selected vs unselected
        marker = dl.Marker(
            position=[row["location_lat"], row["location_long"]],   # Marker coordinates
            children=[                             # Marker children (tooltip and popup)
                dl.Tooltip(row["name"]),                      # Tooltip with animal name
                dl.Popup([                             # Popup with detailed information
                    html.H4("Animal Name: " + str(row["name"])),    # Animal name header
                    html.P("Breed: " + str(row["breed"])),           # Breed information
                    html.P("Age: " + str(row.get("age_upon_outcome", "Unknown"))), # Age
                    html.P("Sex: " + str(row.get("sex_upon_outcome", "Unknown")))  # Sex
                ])
            ],
            # Visual distinction for selected marker
            icon=dict( # Red for selected, blue for others
                iconUrl='https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png' if is_selected 
                        else 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
                iconSize=[25, 41],     # Icon dimensions
                iconAnchor=[12, 41]    # Icon anchor point
            ) if is_selected else None # Only custom icon for selected, default for others 
        )
        markers.append(marker)         # Add marker to list

    return [    # Return map with all markers
        dl.Map( # Map component
            style={'width': '750px', 'height': '500px'}, # Map dimensions
            # Center on selected marker
            center=[dff.iloc[selected_row]["location_lat"], dff.iloc[selected_row]["location_long"]],
            zoom=10,                              # Zoom level
            children=[                            # Map children layers
                dl.TileLayer(id="base-layer-id"), # Base map layer
                *markers                          # Unpack all markers into the children list
            ]
        )
    ]

# --- Pie Chart ---
# Callback to update pie chart based on rescue type filter
@app.callback(
    Output('pie-chart-id', 'figure'), # Output: Update figure property of pie chart
    [Input('btn1', 'n_clicks'),       # Input: Button clicks
     Input('btn2', 'n_clicks'),
     Input('btn3', 'n_clicks'),
     Input('btn4', 'n_clicks')]
)
def update_pie_chart(btn1, btn2, btn3, btn4): # Callback function
    ctx = callback_context                    # Get callback context

    if not ctx.triggered:                     # Check if callback was triggered
        return px.pie(values=[1], names=["-"], title="Dataset too large to display as a pie chart")  # Default

    button_id = ctx.triggered[0]['prop_id'].split('.')[0] # Get triggered button ID

    # Use centralized query function
    query = get_rescue_query(button_id)
    
    # If Reset button or no valid query, show default message
    if not query: # Check if query is all records
        return px.pie(values=[1], names=["-"], title="Dataset too large to display as a pie chart")

    # Fetch filtered data from MongoDB with error handling
    try:
        dff = pd.DataFrame.from_records(shelter.read(query))                   # Query database
    except Exception as e:
        print(f"Error fetching data for pie chart: {e}")                       # Print error
        return px.pie(values=[1], names=["Error"], title="Error loading data") # Error chart
    
    if '_id' in dff.columns:                             # Clean DataFrame
        dff.drop(columns=['_id'], inplace=True)          # Remove _id

    if dff.empty:                                        # Check if DataFrame is empty
        return px.pie(values=[1], names=["No data"], title="No data matches the selected filter")

    # Pie chart of 'breed' counts
    return px.pie(dff, names='breed', title="Breed Distribution") # Create pie chart

# --- Dataset Cardinality Summary ---
# Cache summary calculation for performance optimization
@lru_cache(maxsize=1)    # Decorator to cache function results (max 1 cached result)
def calculate_summary(): # Function definition

    return summary_df.to_dict("records") # Return summary data in DataTable format

# Callback to update summary table
@app.callback(
    Output("summary-table-container", "children"), # Output: Update children of summary container
    [Input("update-summary-btn", "n_clicks")]      # Input: Update button clicks
)
def update_summary_table(n_clicks): # Callback function
    if n_clicks == 0:               # Check if button hasn't been clicked
        return html.Div("Click 'Update Summary' to generate table.") # Initial message

    return dash_table.DataTable(                                    # Generate table on request
        id='summary-table',                                         # Table ID
        columns=[{"name": i, "id": i} for i in summary_df.columns], # Column definitions
        data=calculate_summary(),                                   # Use cached function
        style_cell={'textAlign': 'left', 'maxWidth': '300px', 'whiteSpace': 'normal'}, # Cell styling
        style_header={'fontWeight': 'bold'},                        # Header styling
        page_size=20,                                               # Rows per page
        style_data_conditional=summary_style                        # Apply color-coded styles
    )

# --- Column visibility callback ---
# Updates the DataTable's hidden columns based on checklist selection
@app.callback(
    Output("datatable-id", "hidden_columns"),     # Output: Update hidden_columns property
    Input("column-visibility-checklist", "value") # Input: Checklist selected values
)
def toggle_hidden_columns(visible_columns):       # Callback function
    # Toggle column visibility based on user selection
    if visible_columns is None: # If no columns are selected
        visible_columns = []    # Set to empty list
    # Hide all columns not explicitly selected as visible
    hidden = [col for col in df.columns if col not in visible_columns] # Calculate hidden columns
    return hidden # Return list of columns to hide

####################
# Run the Dash App #
####################
# Start the Dash server in JupyterLab mode on port 8055
app.run_server(mode='jupyterlab', port=8055) # Launch the dashboard application