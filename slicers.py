import dash
from dash import dcc, html, callback, Input, Output, State
import dash_bootstrap_components as dbc
from db_utils import get_schedule_ids, get_operators, get_seat_types, get_hours_before_departure, get_date_of_journey, get_operator_id_by_schedule_id, get_operator_name_by_id, get_seat_types_by_schedule_id, get_origin_destination_by_schedule_id

def create_schedule_id_slicer():
    """Create a dropdown slicer for schedule IDs"""
    # Initially no options, will be populated via callback when date_of_journey is selected
    return html.Div([
        html.Label('Schedule ID', className='fw-bold mb-2'),
        dcc.Dropdown(
            id='schedule-id-dropdown',
            options=[],
            placeholder='Select Schedule ID',
            clearable=True,
            className='mb-4'
        )
    ])

def create_operator_slicer():
    """Create a dropdown slicer for operators"""
    operators = get_operators()
    
    return html.Div([
        html.Label('Operator', className='fw-bold mb-2'),
        dcc.Dropdown(
            id='operator-dropdown',
            options=[{'label': str(op), 'value': op} for op in operators],
            placeholder='Select Operator',
            clearable=True,
            className='mb-4',
            disabled=True  # Initially disabled, will be enabled if no schedule ID is selected
        ),
        # Display area for operator name, origin and destination
        html.Div([
            html.Label('Operator Name:', className='fw-bold me-2', style={'display': 'inline-block'}),
            html.Span(id='operator-name-display', className='text-primary')
        ], className='mb-2'),
        html.Div([
            html.Label('Origin:', className='fw-bold me-2', style={'display': 'inline-block'}),
            html.Span(id='origin-display', className='text-primary')
        ], className='mb-2'),
        html.Div([
            html.Label('Destination:', className='fw-bold me-2', style={'display': 'inline-block'}),
            html.Span(id='destination-display', className='text-primary')
        ], className='mb-3'),
        # Hidden div to store operator name
        html.Div(id='operator-name-container', style={'display': 'none'})
    ])

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
        html.Label('Hours Before Departure', className='fw-bold mb-2'),
        dcc.Dropdown(
            id='hours-before-departure-dropdown',
            options=[],
            placeholder='Select Hours Before Departure',
            clearable=True,
            className='mb-4'
        )
    ], id='hours-before-departure-container', style={'display': 'none'})

def create_date_of_journey_slicer():
    """Create a dropdown slicer for date of journey"""
    # This will be populated with all available dates of journey
    # and will be always visible as the primary filter
    from db_utils import get_all_dates_of_journey
    
    dates = get_all_dates_of_journey()
    options = [{'label': date, 'value': date} for date in dates]
    
    return html.Div([
        html.Label('Date of Journey', className='fw-bold mb-2'),
        dcc.Dropdown(
            id='date-of-journey-dropdown',
            options=options,
            placeholder='Select Date of Journey',
            clearable=True,
            className='mb-4'
        )
    ], id='date-of-journey-container')

def create_slicers_panel():
    """Create a panel with all slicers"""
    return dbc.Card(
        dbc.CardBody([
            html.H4('Filters', className='card-title mb-4'),
            create_date_of_journey_slicer(),  # Date of Journey is now the primary filter and always visible
            create_schedule_id_slicer(),       # Schedule ID options will depend on selected Date of Journey
            create_hours_before_departure_slicer(),  # Initially hidden, will be shown when schedule_id is selected
            create_operator_slicer(),
            # Removed seat type filter as requested
            create_date_range_slicer()
        ]),
        className='mb-4'
    )


# Callback to update operator dropdown when schedule ID is selected
@callback(
    [
        Output('operator-dropdown', 'value'),
        Output('operator-dropdown', 'disabled'),
        Output('operator-name-container', 'children'),
        Output('operator-name-display', 'children')
    ],
    [Input('schedule-id-dropdown', 'value')]
)
def update_operator_by_schedule_id(schedule_id):
    """Update operator dropdown based on selected schedule ID"""
    if not schedule_id:
        # If no schedule ID is selected, enable the operator dropdown for manual selection
        return None, False, None, ''
    
    # Get the operator_id for the selected schedule_id
    operator_id = get_operator_id_by_schedule_id(schedule_id)
    
    if operator_id is None:
        # If no operator_id found, enable the dropdown for manual selection
        return None, False, None, ''
    
    # Get the operator name based on operator_id
    operator_name = get_operator_name_by_id(operator_id)
    
    # Store the operator name in the hidden div
    operator_name_div = html.Div(operator_name)
    
    # Return the operator_id as the value, disable the dropdown, store the operator name, and display it
    return operator_id, True, operator_name_div, operator_name


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
