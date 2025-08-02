import dash
from dash import dcc, html, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc
from db_utils import get_schedule_ids, get_operators, get_seat_types, get_hours_before_departure, get_date_of_journey, get_operator_id_by_schedule_id, get_operator_name_by_id, get_seat_types_by_schedule_id, get_origin_destination_by_schedule_id, get_all_dates_of_journey

def create_schedule_id_slicer():
    """Create a dropdown slicer for schedule IDs with search button"""
    # Initially no options, will be populated via callback when date_of_journey is selected
    return html.Div([
        html.Label('Schedule ID', className='fw-bold mb-2 text-info'),
        dbc.Row([
            dbc.Col([
                dcc.Dropdown(
                    id='schedule-id-dropdown',
                    options=[],
                    placeholder='Select Schedule ID',
                    clearable=True,
                    className='dark-dropdown',
                    style={
                        'border-radius': '8px',
                        'background-color': '#2c2c44',
                        'color': 'white',
                        'width': '100%'
                    }
                )
            ], width=8),
            dbc.Col([
                dbc.Input(
                    id='schedule-id-search',
                    type='text',
                    placeholder='Enter Schedule ID',
                    className='mb-2',
                    style={
                        'border-radius': '8px',
                        'background-color': '#2c2c44',
                        'color': 'white',
                        'border': '1px solid #444'
                    }
                ),
                dbc.Button(
                    html.I(className="fas fa-search"),
                    id='schedule-id-search-button',
                    color='info',
                    className='ms-2',
                    style={'border-radius': '8px'}
                )
            ], width=4, className='d-flex align-items-center')
        ], className='mb-2')
    ], className='filter-section')

def create_operator_slicer():
    """Create a beautiful display for route information (operator, origin, destination)"""
    
    return html.Div([
        # Display area for operator name, origin and destination in a styled card
        dbc.Card([
            dbc.CardHeader([
                html.H5("Route Information", className="d-flex align-items-center mb-0"),
                html.I(className="fas fa-route ms-2 text-primary")
            ], className="d-flex align-items-center card-header-gradient"),
            dbc.CardBody([
                # Single row with all route information
                dbc.Row([
                    # Operator with bus icon
                    dbc.Col([
                        html.Div([
                            html.Div([
                                html.I(className="fas fa-bus text-info", style={'font-size': '24px'})
                            ], className="icon-circle bg-info-subtle"),
                            html.H6('Operator', className='text-muted mt-2 mb-1'),
                            html.H5(id='operator-name-display', className='text-light mb-0')
                        ], className="d-flex flex-column align-items-center justify-content-center text-center")
                    ], width=4),
                    
                    # Origin with departure icon
                    dbc.Col([
                        html.Div([
                            html.Div([
                                html.I(className="fas fa-plane-departure text-success", style={'font-size': '24px'})
                            ], className="icon-circle bg-success-subtle"),
                            html.H6('Origin', className='text-muted mt-2 mb-1'),
                            html.H5(id='origin-display', className='text-light mb-0')
                        ], className="d-flex flex-column align-items-center justify-content-center text-center")
                    ], width=4),
                    
                    # Destination with arrival icon
                    dbc.Col([
                        html.Div([
                            html.Div([
                                html.I(className="fas fa-plane-arrival text-danger", style={'font-size': '24px'})
                            ], className="icon-circle bg-danger-subtle"),
                            html.H6('Destination', className='text-muted mt-2 mb-1'),
                            html.H5(id='destination-display', className='text-light mb-0')
                        ], className="d-flex flex-column align-items-center justify-content-center text-center")
                    ], width=4)
                ])
            ], className="p-3")
        ], className='mb-4 route-info-card shadow'),
        # Hidden div to store operator name
        html.Div(id='operator-name-container', style={'display': 'none'}),
        # Hidden div to store operator id (for compatibility with existing callbacks)
        html.Div(id='operator-dropdown', style={'display': 'none'})
    ], className='filter-section')

def create_seat_type_slicer():
    """Create a dropdown slicer for seat types"""
    # Initially get all seat types, will be filtered via callback when schedule_id is selected
    seat_types = get_seat_types()
    
    return html.Div([
        html.Label('Seat Type', className='fw-bold mb-2'),
        dcc.Dropdown(
            id='seat-type-dropdown',
            options=[{'label': str(st), 'value': st} for st in seat_types],
            placeholder='Select Seat Type',
            clearable=True,
            className='mb-4'
        )
    ])

def create_date_range_slicer():
    """Create a date range slicer"""
    return html.Div([
        html.Label('Date Range', className='fw-bold mb-2'),
        dcc.DatePickerRange(
            id='date-range-picker',
            start_date_placeholder_text='Start Date',
            end_date_placeholder_text='End Date',
            className='mb-4'
        )
    ])

def create_hours_before_departure_slicer(schedule_id=None):
    """Create a dropdown slicer for hours before departure"""
    # Initially no options, will be populated via callback when schedule_id is selected
    return html.Div([
        html.Label('Hours Before Departure', className='fw-bold mb-2 text-info'),
        dbc.Row([
            dbc.Col([
                html.I(className="fas fa-clock me-2 text-warning"),
                dcc.Dropdown(
                    id='hours-before-departure-dropdown',
                    options=[],
                    placeholder='Select Hours',
                    clearable=True,
                    className='dark-dropdown',
                    style={
                        'border-radius': '8px',
                        'background-color': '#2c2c44',
                        'color': 'white',
                        'width': '100%',
                        'min-width': '100px'
                    }
                )
            ], width=12, className='d-flex align-items-center')
        ], className='mb-2')
    ], id='hours-before-departure-container', style={'display': 'none'}, className='filter-section')

def create_date_of_journey_slicer():
    """Create a dropdown slicer for date of journey"""
    # This will be populated with all available dates of journey
    # and will be always visible as the primary filter
    from db_utils import get_all_dates_of_journey
    
    dates = get_all_dates_of_journey()
    options = [{'label': date, 'value': date} for date in dates]
    
    return html.Div([
        html.Label('Date of Journey', className='fw-bold mb-2 text-info'),
        dbc.Row([
            dbc.Col([
                html.I(className="fas fa-calendar-alt me-2 text-warning"),
                dcc.Dropdown(
                    id='date-of-journey-dropdown',
                    options=options,
                    placeholder='Select Date',
                    clearable=True,
                    className='dark-dropdown',
                    style={
                        'border-radius': '8px',
                        'background-color': '#2c2c44',
                        'color': 'white',
                        'width': '100%',
                        'min-width': '120px'
                    }
                )
            ], width=12, className='d-flex align-items-center')
        ], className='mb-2')
    ], id='date-of-journey-container', className='filter-section')

def create_slicers_panel():
    """Create a panel with all slicers in a single row on desktop, stacked on mobile"""
    return dbc.Card([
        dbc.CardHeader([
            html.H4("Dashboard Filters", className="d-flex align-items-center mb-0"),
            html.I(className="fas fa-filter ms-2 text-info")
        ], className="d-flex align-items-center"),
        dbc.CardBody([
            dbc.Row([
                # Date of Journey
                dbc.Col([
                    html.Label('Date of Journey', className='fw-bold mb-2 text-info'),
                    html.Div([
                        html.I(className="fas fa-calendar-alt me-2 text-warning"),
                        dcc.Dropdown(
                            id='date-of-journey-dropdown',
                            options=[{'label': date, 'value': date} for date in get_all_dates_of_journey()],
                            placeholder='Select Date',
                            clearable=True,
                            className='dark-dropdown',
                            style={
                                'border-radius': '8px',
                                'background-color': '#2c2c44',
                                'color': 'white',
                                'width': '100%',
                            }
                        )
                    ], className='d-flex align-items-center')
                ], xs=12, sm=12, md=6, lg=3, className="mb-3 mb-lg-0"),
                
                # Schedule ID
                dbc.Col([
                    html.Label('Schedule ID', className='fw-bold mb-2 text-info'),
                    html.Div([
                        dcc.Dropdown(
                            id='schedule-id-dropdown',
                            options=[],
                            placeholder='Select Schedule ID',
                            clearable=True,
                            className='dark-dropdown',
                            style={
                                'border-radius': '8px',
                                'background-color': '#2c2c44',
                                'color': 'white',
                                'width': '100%',
                            }
                        )
                    ], className='d-flex align-items-center')
                ], xs=12, sm=12, md=6, lg=3, className="mb-3 mb-lg-0"),
                
                # Hours Before Departure
                dbc.Col([
                    html.Label('Hours Before Departure', className='fw-bold mb-2 text-info'),
                    html.Div([
                        html.I(className="fas fa-clock me-2 text-warning"),
                        dcc.Dropdown(
                            id='hours-before-departure-dropdown',
                            options=[],
                            placeholder='Select Hours',
                            clearable=True,
                            className='dark-dropdown',
                            style={
                                'border-radius': '8px',
                                'background-color': '#2c2c44',
                                'color': 'white',
                                'width': '100%',
                            }
                        )
                    ], className='d-flex align-items-center')
                ], id='hours-before-departure-container', style={'display': 'none'}, xs=12, sm=12, md=6, lg=3, className="mb-3 mb-lg-0"),
                
                # Search
                dbc.Col([
                    html.Label('Search Schedule ID', className='fw-bold mb-2 text-info'),
                    html.Div([
                        dbc.Input(
                            id='schedule-id-search',
                            type='text',
                            placeholder='Enter Schedule ID',
                            style={
                                'border-radius': '8px',
                                'background-color': '#2c2c44',
                                'color': 'white',
                                'border': '1px solid #444'
                            }
                        ),
                        dbc.Button(
                            html.I(className="fas fa-search"),
                            id='schedule-id-search-button',
                            color='info',
                            className='ms-2',
                            style={'border-radius': '8px'}
                        )
                    ], className='d-flex align-items-center')
                ], xs=12, sm=12, md=6, lg=3, className="mb-3 mb-lg-0"),
            ], className="mobile-stack"),
            
            # Route Info Card (Operator, Origin, Destination)
            dbc.Row([
                dbc.Col(create_operator_slicer(), width=12, className="mt-3")
            ])
        ])
    ], className='mb-4 filter-panel shadow')


# Callback to update operator info when schedule ID is selected
@callback(
    [
        Output('operator-dropdown', 'children'),  # Changed from 'value' to 'children'
        Output('operator-name-container', 'children'),
        Output('operator-name-display', 'children')
    ],
    [Input('schedule-id-dropdown', 'value')]
)
def update_operator_by_schedule_id(schedule_id):
    """Update operator information based on selected schedule ID"""
    if not schedule_id:
        # If no schedule ID is selected, return empty values
        return None, None, ''
    
    # Get the operator_id for the selected schedule_id
    operator_id = get_operator_id_by_schedule_id(schedule_id)
    
    if operator_id is None:
        # If no operator_id found, return empty values
        return None, None, ''
    
    # Get the operator name based on operator_id
    operator_name = get_operator_name_by_id(operator_id)
    
    # Store the operator name in the hidden div
    operator_name_div = html.Div(operator_name)
    
    # Store the operator_id in the hidden div for compatibility with other callbacks
    operator_id_div = html.Div(operator_id)
    
    # Return the operator_id as hidden div content, store the operator name, and display it
    return operator_id_div, operator_name_div, operator_name


# Callback for schedule ID search button
@callback(
    Output('schedule-id-dropdown', 'value'),
    [Input('schedule-id-search-button', 'n_clicks')],
    [State('schedule-id-search', 'value'),
     State('schedule-id-dropdown', 'options')]
)
def search_schedule_id(n_clicks, search_value, available_options):
    """Search for a schedule ID and select it if found"""
    if not n_clicks or not search_value:
        # No clicks or no search value, return no change
        return dash.no_update
    
    # Convert search value to string for comparison
    search_value = str(search_value).strip()
    
    # Check if the search value matches any available schedule ID
    for option in available_options:
        if str(option['value']) == search_value:
            # Found a match, return this value to select it in the dropdown
            return option['value']
    
    # No match found
    return dash.no_update


# Callback to update seat type dropdown when schedule ID is selected
@callback(
    Output('seat-type-dropdown', 'options'),
    [Input('schedule-id-dropdown', 'value')]
)
def update_seat_types_by_schedule_id(schedule_id):
    """Update seat type dropdown options based on selected schedule ID"""
    if not schedule_id:
        # If no schedule ID is selected, show all seat types
        seat_types = get_seat_types()
    else:
        # Get seat types specific to the selected schedule_id
        seat_types = get_seat_types_by_schedule_id(schedule_id)
        
        # If no seat types found for this schedule, fall back to all seat types
        if not seat_types:
            seat_types = get_seat_types()
    
    # Format the options for the dropdown
    options = [{'label': str(st), 'value': st} for st in seat_types]
    
    return options
