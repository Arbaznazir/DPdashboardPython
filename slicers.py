import dash
from dash import dcc, html, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc
from db_utils import get_schedule_ids, get_operators, get_seat_types, get_hours_before_departure, get_date_of_journey, get_operator_id_by_schedule_id, get_operator_name_by_id, get_seat_types_by_schedule_id, get_origin_destination_by_schedule_id, get_all_dates_of_journey
import datetime
import calendar
from date_utils import is_past_date

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
    # Get all available dates of journey
    dates = get_all_dates_of_journey()
    
    # Format dates for display
    date_options = [{'label': date.strftime('%Y-%m-%d'), 'value': date.strftime('%Y-%m-%d')} for date in dates]
    
    return html.Div([
        html.Label('Date of Journey', className='fw-bold mb-2 text-info'),
        dcc.Dropdown(
            id='date-of-journey-dropdown',
            options=date_options,
            value=date_options[0]['value'] if date_options else None,
            clearable=False,
            className='dark-dropdown',
            style={
                'border-radius': '8px',
                'background-color': '#2c2c44',
                'color': 'white',
                'width': '100%'
            }
        )
    ], className='filter-section mb-3')

def create_date_summary_section():
    """Create a section for date summary KPIs that only appear for past dates"""
    return html.Div([
        dbc.Card([
            dbc.CardHeader([
                html.H5("Date Summary Analysis", className="d-flex align-items-center mb-0"),
                html.I(className="fas fa-calendar-check ms-2 text-info")
            ], className="d-flex align-items-center card-header-gradient"),
            dbc.CardBody([
                # Container for Date Summary KPIs
                html.Div(id="date-summary-container", className="p-0")
            ])
        ])
    ], className='filter-section mt-4')

def create_monthly_delta_section():
    """Create a modern Monthly Delta Analysis section with month/year selectors and calculate button"""
    current_year = datetime.datetime.now().year
    current_month = datetime.datetime.now().month
    
    return html.Div([
        dbc.Card([
            dbc.CardHeader([
                html.H5("Monthly Delta Analysis", className="d-flex align-items-center mb-0"),
                html.I(className="fas fa-chart-line ms-2 text-success")
            ], className="d-flex align-items-center card-header-gradient"),
            dbc.CardBody([
                # Month/Year selectors and calculate button in a single row
                dbc.Row([
                    # Month selector
                    dbc.Col([
                        html.Label("Month:", className="text-light mb-2"),
                        dcc.Dropdown(
                            id="month-selector",
                            options=[
                                {"label": month, "value": i} for i, month in enumerate(calendar.month_name) if i > 0
                            ],
                            value=current_month,
                            clearable=False,
                            className="dark-dropdown",
                            style={
                                "background-color": "#2c2c44",
                                "color": "white",
                                "border-radius": "8px"
                            }
                        )
                    ], width=5),
                    
                    # Year selector
                    dbc.Col([
                        html.Label("Year:", className="text-light mb-2"),
                        dcc.Dropdown(
                            id="year-selector",
                            options=[
                                {"label": str(year), "value": year} 
                                for year in range(current_year - 2, current_year + 3)
                            ],
                            value=current_year,
                            clearable=False,
                            className="dark-dropdown",
                            style={
                                "background-color": "#2c2c44",
                                "color": "white",
                                "border-radius": "8px"
                            }
                        )
                    ], width=4),
                    
                    # Calculate button
                    dbc.Col([
                        html.Label("\u00A0", className="text-light mb-2"),  # Non-breaking space for alignment
                        dbc.Button(
                            [html.I(className="fas fa-calculator me-2"), "Calculate"],
                            id="calculate-monthly-delta-button",
                            color="success",
                            className="w-100",
                            style={
                                "boxShadow": "0 4px 6px rgba(50, 50, 93, 0.11), 0 1px 3px rgba(0, 0, 0, 0.08)",
                                "borderRadius": "8px",
                                "fontWeight": "600"
                            }
                        )
                    ], width=3, className="d-flex align-items-end")
                ], className="mb-4"),
                
                # KPI cards container
                html.Div(id="monthly-delta-kpis", className="mt-3")
            ], className="p-3")
        ], className="mb-4 shadow monthly-delta-card")
    ])

def create_month_year_selector():
    """Create month and year selectors for Monthly Delta Analysis"""
    # Get current month and year
    current_month = datetime.datetime.now().month
    current_year = datetime.datetime.now().year
    
    # Create month options
    month_options = [{'label': calendar.month_name[i], 'value': i} for i in range(1, 13)]
    
    # Create year options (current year and 2 years before/after)
    year_options = [{'label': str(year), 'value': year} for year in range(current_year - 2, current_year + 3)]
    
    return html.Div([
        html.Div([
            html.H5('Monthly Delta Analysis', className='fw-bold mb-3 text-primary'),
            html.Div([
                html.Div([
                    html.Label('Month', className='fw-bold mb-2 text-info d-block'),
                    dcc.Dropdown(
                        id='month-selector-dropdown',
                        options=month_options,
                        value=current_month,  # Default to current month
                        clearable=False,
                        className='dark-dropdown',
                        style={
                            'border-radius': '8px',
                            'background-color': '#2c2c44',
                            'color': 'white',
                            'width': '100%'
                        }
                    )
                ], className='me-2', style={'flex': '1'}),
                html.Div([
                    html.Label('Year', className='fw-bold mb-2 text-info d-block'),
                    dcc.Dropdown(
                        id='year-selector-dropdown',
                        options=year_options,
                        value=current_year,  # Default to current year
                        clearable=False,
                        className='dark-dropdown',
                        style={
                            'border-radius': '8px',
                            'background-color': '#2c2c44',
                            'color': 'white',
                            'width': '100%'
                        }
                    )
                ], className='me-2', style={'flex': '1'}),
                html.Div([
                    html.Label('\u00A0', className='fw-bold mb-2 d-block'), # Invisible label for alignment
                    dbc.Button(
                        'Calculate',
                        id='calculate-monthly-delta-button',
                        color='primary',
                        className='w-100',
                        style={
                            'border-radius': '8px',
                            'height': '38px',  # Match dropdown height
                            'background-image': 'linear-gradient(to right, #4facfe 0%, #00f2fe 100%)',
                            'border': 'none',
                            'box-shadow': '0 4px 6px rgba(50, 50, 93, 0.11), 0 1px 3px rgba(0, 0, 0, 0.08)'
                        }
                    )
                ], style={'flex': '1'})
            ], className='d-flex')
        ], className='p-3'),
        
        # Container for Monthly Delta KPIs
        html.Div(id="monthly-delta-container", className="mt-3")
    ], className='filter-section mt-4 p-0 border border-primary rounded shadow', style={'background-color': '#1e1e2f'})

def create_slicers_panel():
    """Create a panel with all slicers in a single row on desktop, stacked on mobile"""
    return html.Div([
        # Main filters card
        dbc.Card([
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
                    ], xs=12, sm=12, md=6, lg=3, className="mb-3 mb-lg-0"),
                    
                    # Schedule ID Search
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
                                    'border': '1px solid #444',
                                    'marginRight': '10px'
                                }
                            ),
                            dbc.Button(
                                html.I(className="fas fa-search"),
                                id='schedule-id-search-button',
                                color='info',
                                style={'border-radius': '8px'}
                            )
                        ], className='d-flex align-items-center')
                    ], xs=12, sm=12, md=6, lg=3, className="mb-3 mb-lg-0")
                ], className="mb-4"),
                
                # Route Information Card
                create_operator_slicer(),
                
                # Hidden divs for storing data
                html.Div(id='selected-schedule-id-store', style={'display': 'none'}),
                html.Div(id='selected-hour-store', style={'display': 'none'})
            ], className="p-3")
        ], className="mb-4 shadow"),
        
        # Date Summary Analysis section
        create_date_summary_section()
    ])

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
