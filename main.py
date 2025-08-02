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
    create_seat_scatter_chart
)
from seat_slider import create_seat_price_slider, create_seat_details_card

# Initialize Dash app with Bootstrap theme
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        'https://use.fontawesome.com/releases/v5.15.4/css/all.css'
    ],
    suppress_callback_exceptions=True
)

# App layout
app.layout = dbc.Container([
    # Header
    dbc.Row([
        dbc.Col([
            html.H1("Dynamic Pricing Dashboard", className="mb-2"),
            html.P("Analyze seat pricing and occupancy data", className="text-muted")
        ], width=12)
    ], className="mb-4 mt-4"),
    
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
    
    # Charts row
    dbc.Row([
        dbc.Col([
            html.Div(id="price-trend-container", className="mb-4")
        ], width=6),
        dbc.Col([
            html.Div(id="price-delta-container", className="mb-4")
        ], width=6),
    ]),
    
    dbc.Row([
        dbc.Col([
            html.Div(id="occupancy-container", className="mb-4")
        ], width=6),
        dbc.Col([
            html.Div(id="seat-scatter-container", className="mb-4")
        ], width=6),
    ]),
    
    # Seat Price Slider row
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("Seat-wise Pricing")),
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
        Output("price-trend-container", "children"),
        Output("price-delta-container", "children"),
        Output("occupancy-container", "children"),
        Output("seat-scatter-container", "children"),
        Output("data-table-container", "children"),
        Output("filtered-data-store", "data")
    ],
    [
        Input("schedule-id-dropdown", "value"),
        Input("hours-before-departure-dropdown", "value"),
        Input("date-of-journey-dropdown", "value"),
        Input("operator-dropdown", "value")
    ]
)
def update_dashboard(schedule_id, hours_before_departure, date_of_journey, operator_id):
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
    
    try:
        # Get price trend chart
        price_trend_chart = create_price_trend_chart(schedule_id, operator_id, seat_type, hours_before_departure, date_of_journey)
    except Exception as e:
        print(f"Error creating price trend chart: {str(e)}")
        price_trend_chart = default_message
    
    try:
        # Get price delta chart
        price_delta_chart = create_price_delta_chart(schedule_id, operator_id, seat_type, hours_before_departure, date_of_journey)
    except Exception as e:
        print(f"Error creating price delta chart: {str(e)}")
        price_delta_chart = default_message
    
    try:
        # Get occupancy chart
        occupancy_chart = create_occupancy_chart(schedule_id, operator_id, seat_type, hours_before_departure, date_of_journey)
    except Exception as e:
        print(f"Error creating occupancy chart: {str(e)}")
        occupancy_chart = default_message
    
    try:
        # Get seat scatter chart
        seat_scatter_chart = create_seat_scatter_chart(schedule_id, hours_before_departure, date_of_journey)
    except Exception as e:
        print(f"Error creating seat scatter chart: {str(e)}")
        seat_scatter_chart = default_message
    
    try:
        # Get data for table
        df = get_filtered_data(schedule_id, operator_id, seat_type, hours_before_departure, date_of_journey)
        
        if df is not None and not df.empty:
            # Store data for sharing between callbacks
            data_json = df.to_json(date_format='iso', orient='split')
            
            # Create data table
            data_table = dash_table.DataTable(
                id='data-table',
                columns=[{"name": i, "id": i} for i in df.columns],
                data=df.to_dict('records'),
                page_size=10,
                style_table={'overflowX': 'auto'},
                style_cell={
                    'textAlign': 'left',
                    'minWidth': '100px', 'width': '150px', 'maxWidth': '200px',
                    'overflow': 'hidden',
                    'textOverflow': 'ellipsis',
                },
                sort_action='native',
                filter_action='native',
            )
        else:
            data_json = None
            data_table = html.P("No data available for the selected filters.")
    except Exception as e:
        print(f"Error creating data table: {str(e)}")
        data_table = html.P(f"Error loading data: {str(e)}")
        data_json = None
    
    return kpi_row, price_trend_chart, price_delta_chart, occupancy_chart, seat_scatter_chart, data_table, data_json

# Callback to update seat price slider based on selected schedule ID
@app.callback(
    Output("seat-price-slider-container", "children"),
    [Input("schedule-id-dropdown", "value"),
     Input("hours-before-departure-dropdown", "value")]
)
def update_seat_price_slider(schedule_id, hours_before_departure):
    """Update seat price slider based on selected schedule ID and hour before departure"""
    if not schedule_id:
        return html.Div([
            html.P("Select a schedule ID to view seat-wise pricing data", className="text-muted text-center")
        ])
    
    try:
        # Get seat-wise pricing data for the selected schedule ID and hour before departure
        df = get_seat_wise_prices(schedule_id, hours_before_departure)
        
        if df is not None and not df.empty:
            # Create the seat price slider component
            return create_seat_price_slider(df)
        else:
            return html.Div([
                html.P(f"No seat-wise pricing data available for schedule ID: {schedule_id} and hour before departure: {hours_before_departure}", 
                       className="text-muted text-center")
            ])
    except Exception as e:
        print(f"Error creating seat price slider: {str(e)}")
        return html.Div([
            html.P(f"Error loading seat-wise pricing data: {str(e)}", className="text-danger text-center")
        ])

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
