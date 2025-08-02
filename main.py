import dash
from dash import html, dcc, dash_table
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd

# Import custom modules
from db_utils import get_filtered_data, get_seat_wise_data, get_seat_wise_prices
from slicers import create_slicers_panel
from kpis import create_kpi_row
from graphs import (
    create_price_trend_chart, 
    create_price_delta_chart,
    create_occupancy_chart,
    create_seat_scatter_chart,
    create_seat_wise_price_sum_chart
)
from seat_slider import create_seat_price_slider, create_seat_details_card
from seat_map import create_seat_map

# Initialize Dash app with Bootstrap theme - using DARKLY for a modern dark theme
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.DARKLY,  # Modern dark theme
        'https://use.fontawesome.com/releases/v5.15.4/css/all.css',
        'https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;700&display=swap'  # Modern font
    ],
    suppress_callback_exceptions=True
)

# Custom CSS for better styling
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            body {
                font-family: 'Poppins', sans-serif;
                background-color: #1e1e2f;
                color: #ffffff;
            }
            .dashboard-header {
                background: linear-gradient(87deg, #5e72e4 0, #825ee4 100%);
                padding: 20px 0;
                border-radius: 10px;
                box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.14), 0 7px 10px -5px rgba(94, 114, 228, 0.4);
                margin-bottom: 30px;
            }
            .dashboard-title {
                font-weight: 700;
                font-size: 2.5rem;
                margin: 0;
                color: white;
                text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            }
            .dashboard-subtitle {
                color: rgba(255, 255, 255, 0.8);
                font-size: 1.1rem;
                font-weight: 300;
            }
            .card {
                border-radius: 10px;
                box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.14);
                margin-bottom: 20px;
                background-color: #27293d;
                border: none;
            }
            .card-header {
                background-color: rgba(0, 0, 0, 0.2);
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                padding: 15px 20px;
                border-radius: 10px 10px 0 0 !important;
            }
            .card-body {
                padding: 20px;
            }
            .kpi-card {
                background: linear-gradient(45deg, #1d8cf8, #3358f4);
                color: white;
                border-radius: 10px;
                padding: 20px;
                box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.14);
                transition: transform 0.3s;
            }
            .kpi-card:hover {
                transform: translateY(-5px);
            }
            .nav-pills .nav-link.active {
                background-color: #5e72e4;
            }
            .dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner th {
                background-color: #5e72e4 !important;
                color: white !important;
            }
            .dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner td {
                background-color: #27293d !important;
                color: white !important;
            }
            /* Dark dropdown styling */
            .dark-dropdown .Select-control {
                background-color: #2c2c44 !important;
                border-color: #444 !important;
            }
            .dark-dropdown .Select-menu-outer {
                background-color: #2c2c44 !important;
                border: 1px solid #444 !important;
            }
            .dark-dropdown .Select-option {
                background-color: #2c2c44 !important;
                color: white !important;
            }
            .dark-dropdown .Select-option:hover {
                background-color: #3a3a5a !important;
            }
            .dark-dropdown .Select-value-label {
                color: white !important;
            }
            .dark-dropdown .Select-placeholder {
                color: #aaa !important;
            }
            .dark-dropdown.is-focused:not(.is-open) > .Select-control {
                border-color: #5e72e4 !important;
                box-shadow: 0 0 0 3px rgba(94, 114, 228, 0.25) !important;
            }
            
            /* Icon circle styling */
            .icon-circle {
                width: 50px;
                height: 50px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .bg-info-subtle {
                background-color: rgba(66, 153, 225, 0.15);
            }
            
            .bg-success-subtle {
                background-color: rgba(72, 187, 120, 0.15);
            }
            
            .bg-danger-subtle {
                background-color: rgba(245, 101, 101, 0.15);
            }
            
            .card-header-gradient {
                background: linear-gradient(87deg, #172b4d, #1a174d);
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# App layout
app.layout = dbc.Container([
    # Header with gradient background
    dbc.Row([
        dbc.Col([
            html.Div([
                html.H1("Dynamic Pricing Dashboard", className="dashboard-title"),
                html.P("Analyze seat pricing and occupancy data", className="dashboard-subtitle"),
                html.Div([
                    html.I(className="fas fa-chart-line mr-2"),
                    " Real-time analytics for optimal pricing decisions"
                ], className="mt-2")
            ], className="text-center dashboard-header")
        ], width=12)
    ]),
    
    # Filters row
    dbc.Row([
        dbc.Col([
            create_slicers_panel()
        ], width=12)
    ]),
    
    # KPI row
    dbc.Row([
        dbc.Col([
            html.Div(id="kpi-container")
        ], width=12)
    ]),
    
    # Charts row - Price Trend and Price Delta graphs removed as requested
    
    dbc.Row([
        dbc.Col([
            html.Div(id="occupancy-container", className="mb-4")
        ], width=12)
    ]),
    
    # Seat-wise Price Sum Chart row
    dbc.Row([
        dbc.Col([
            html.Div(id="seat-wise-price-sum-container", className="mb-4")
        ], width=12)
    ]),
    
    # Seat Map Visualization row
    dbc.Row([
        dbc.Col([
            html.Div(id="seat-map-container")
        ], width=12)
    ], className="mb-4"),
    
    # Seat Price Slider row
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("Seat-wise Pricing Table")),
                dbc.CardBody([
                    html.Div(id="seat-price-slider-container")
                ])
            ])
        ], width=12)
    ], className="mb-4"),
    
    # Data table
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("Detailed Data")),
                dbc.CardBody([
                    html.Div(id="data-table-container")
                ])
            ])
        ], width=12)
    ]),
    
    # Store component for sharing data between callbacks
    dcc.Store(id="filtered-data-store"),
    
], fluid=True)

# Callback to update hours before departure slicer when schedule ID is selected
@app.callback(
    [
        Output("hours-before-departure-container", "style"),
        Output("hours-before-departure-dropdown", "options")
    ],
    [Input("schedule-id-dropdown", "value")]
)
def update_hours_before_departure_slicer(schedule_id):
    """Update hours before departure slicer based on selected schedule ID"""
    from db_utils import get_hours_before_departure
    
    if schedule_id:
        # Get hours before departure for the selected schedule ID
        hours_before_departure = get_hours_before_departure(schedule_id)
        options = [{'label': str(hbd), 'value': hbd} for hbd in hours_before_departure]
        return {'display': 'block'}, options
    else:
        # Hide the slicer if no schedule ID is selected
        return {'display': 'none'}, []

# Callback to update schedule ID slicer when date of journey is selected
@app.callback(
    Output("schedule-id-dropdown", "options"),
    [Input("date-of-journey-dropdown", "value")]
)
def update_schedule_id_slicer(date_of_journey):
    """Update schedule ID slicer based on selected date of journey"""
    from db_utils import get_schedule_ids_by_date, get_schedule_ids
    
    if date_of_journey:
        # Get schedule IDs for the selected date of journey
        schedule_ids = get_schedule_ids_by_date(date_of_journey)
        options = [{'label': str(sid), 'value': sid} for sid in schedule_ids]
        return options
    else:
        # If no date is selected, show all schedule IDs
        schedule_ids = get_schedule_ids()
        options = [{'label': str(sid), 'value': sid} for sid in schedule_ids]
        return options

# Callback to update KPIs and charts based on filters
@app.callback(
    [
        Output("kpi-container", "children"),
        Output("occupancy-container", "children"),
        Output("data-table-container", "children"),
        Output("filtered-data-store", "data"),
        Output("seat-wise-price-sum-container", "children")
    ],
    [
        Input("schedule-id-dropdown", "value"),
        Input("hours-before-departure-dropdown", "value"),
        Input("date-of-journey-dropdown", "value"),
        Input("operator-name-container", "children")
    ]
)
def update_dashboard(schedule_id, hours_before_departure, date_of_journey, operator_name_div):
    # Extract operator_id from the operator-name-container div if available
    operator_id = None
    if operator_name_div is not None and len(operator_name_div) > 0:
        # The operator name is stored in the div, we can get the operator_id from the schedule_id
        if schedule_id:
            from db_utils import get_operator_id_by_schedule_id
            operator_id = get_operator_id_by_schedule_id(schedule_id)
    """Update dashboard components based on selected filters - seat type filter removed as requested"""
    # Set seat_type to None to show all seat types
    seat_type = None
    
    # Initialize default components in case of errors
    default_message = html.Div([html.P("Select filters to view data")])
    data_json = None
    
    try:
        # Get KPI row
        print(f"Creating KPI row with: schedule_id={schedule_id}, operator_id={operator_id}, seat_type={seat_type}, hours_before_departure={hours_before_departure}")
        kpi_row = create_kpi_row(schedule_id, operator_id, seat_type, hours_before_departure, date_of_journey)
    except Exception as e:
        print(f"Error creating KPI row: {str(e)}")
        kpi_row = html.Div([html.P(f"Error loading KPIs: {str(e)}")])
    
    # Price trend and price delta charts removed as requested
    
    try:
        # Get occupancy chart
        occupancy_chart = create_occupancy_chart(schedule_id, operator_id, seat_type, hours_before_departure, date_of_journey)
    except Exception as e:
        print(f"Error creating occupancy chart: {str(e)}")
        occupancy_chart = default_message
    
    # Seat scatter chart removed as requested
    
    try:
        # Get data for table
        df = get_filtered_data(schedule_id, operator_id, seat_type, hours_before_departure, date_of_journey)
        
        if df is not None and not df.empty:
            # Store data for sharing between callbacks
            data_json = df.to_json(date_format='iso', orient='split')
            
            # Create modern data table with dark theme styling - using only supported properties
            data_table = dash_table.DataTable(
                id='data-table',
                columns=[{"name": i, "id": i} for i in df.columns],
                data=df.to_dict('records'),
                page_size=10,
                style_table={
                    'overflowX': 'auto',
                    'backgroundColor': '#27293d',
                    'border': '1px solid #444'
                },
                style_cell={
                    'textAlign': 'left',
                    'minWidth': '100px', 
                    'width': '150px', 
                    'maxWidth': '200px',
                    'overflow': 'hidden',
                    'textOverflow': 'ellipsis',
                    'backgroundColor': '#27293d',
                    'color': 'white',
                    'fontFamily': 'Poppins, sans-serif',
                    'border': '1px solid #444'
                },
                style_header={
                    'backgroundColor': '#1d8cf8',
                    'color': 'white',
                    'fontWeight': 'bold',
                    'textAlign': 'center',
                    'border': '1px solid #1d8cf8'
                },
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': '#2c2f43'
                    }
                ],
                sort_action='native',
                filter_action='native',
                page_action='native'
            )
        else:
            data_json = None
            data_table = html.P("No data available for the selected filters.")
    except Exception as e:
        print(f"Error creating data table: {str(e)}")
        data_table = default_message
        data_json = None
    
    try:
        # Get seat-wise price sum chart (only depends on schedule_id, not on hours_before_departure)
        seat_wise_price_sum_chart = create_seat_wise_price_sum_chart(schedule_id)
    except Exception as e:
        print(f"Error creating seat-wise price sum chart: {str(e)}")
        seat_wise_price_sum_chart = html.Div([html.P(f"Error loading seat-wise price sum chart: {str(e)}", className="text-danger text-center")])
    
    return kpi_row, occupancy_chart, data_table, data_json, seat_wise_price_sum_chart

# Callback to update seat price slider based on selected schedule ID and hours before departure
@app.callback(
    [Output("seat-price-slider-container", "children"),
     Output("seat-map-container", "children")],
    [Input("schedule-id-dropdown", "value"),
     Input("hours-before-departure-dropdown", "value")]
)
def update_seat_visualizations(schedule_id, hours_before_departure):
    """Update seat price slider and seat map based on selected schedule ID and hour before departure"""
    if not schedule_id:
        empty_message = html.Div([
            html.P("Select a schedule ID to view seat-wise pricing data", className="text-muted text-center")
        ])
        return empty_message, empty_message
    
    # Only show seat-wise prices when hours before departure is selected
    if not hours_before_departure:
        empty_message = html.Div([
            html.P("Select hours before departure to view seat-wise pricing data", className="text-muted text-center")
        ])
        return empty_message, empty_message
    
    try:
        # Get seat-wise pricing data for the selected schedule ID and hour before departure
        df = get_seat_wise_prices(schedule_id, hours_before_departure)
        
        if df is not None and not df.empty:
            # Create the seat price slider and seat map components
            seat_slider = create_seat_price_slider(df)
            seat_map = create_seat_map(df)
            return seat_slider, seat_map
        else:
            empty_message = html.Div([
                html.P(f"No seat-wise pricing data available for schedule ID: {schedule_id} and hour before departure: {hours_before_departure}", 
                       className="text-muted text-center")
            ])
            return empty_message, empty_message
    except Exception as e:
        print(f"Error creating seat visualizations: {str(e)}")
        error_message = html.Div([
            html.P(f"Error loading seat-wise pricing data: {str(e)}", className="text-danger text-center")
        ])
        return error_message, error_message

# Callback to update origin and destination when schedule ID is selected
@app.callback(
    [
        Output("origin-display", "children"),
        Output("destination-display", "children")
    ],
    [Input("schedule-id-dropdown", "value")]
)
def update_route_info(schedule_id):
    """Update origin and destination based on selected schedule ID"""
    if not schedule_id:
        return "", ""
    
    # For now, hardcode the origin and destination for all schedule IDs
    # This is a temporary solution until we can fix the database query
    origin_id = 1646
    destination_id = 1821
    origin_name = "Santiago"
    destination_name = "La Serena"
    
    # Format the origin and destination display
    origin_display = f"{origin_name} (ID: {origin_id})"
    destination_display = f"{destination_name} (ID: {destination_id})"
    
    return origin_display, destination_display

# Callback to update seat details card based on selected seat
@app.callback(
    Output("seat-details", "children"),
    [Input("seat-selector", "value"),
     Input("schedule-id-dropdown", "value")]
)
def update_seat_details(selected_seat, schedule_id):
    """Update seat details card based on selected seat"""
    if not selected_seat or not schedule_id:
        return html.Div()
    
    try:
        # Get seat-wise pricing data for the selected schedule ID
        df = get_seat_wise_prices(schedule_id)
        
        if df is not None and not df.empty:
            # Filter data for the selected seat
            seat_data = df[df['seat_number'].astype(str) == str(selected_seat)]
            
            if not seat_data.empty:
                # Create a dictionary with seat details
                seat_details = {
                    'seat_number': selected_seat,
                    'actual_fare': seat_data['actual_fare'].iloc[0],
                    'final_price': seat_data['final_price'].iloc[0]
                }
                
                # Create the seat details card
                return create_seat_details_card(seat_details)
            else:
                return html.Div([
                    html.P(f"No data available for seat {selected_seat}", className="text-muted")
                ])
        else:
            return html.Div()
    except Exception as e:
        print(f"Error creating seat details card: {str(e)}")
        return html.Div([
            html.P(f"Error loading seat details: {str(e)}", className="text-danger")
        ])

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True, port=8050)
