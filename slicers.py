import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from db_utils import get_schedule_ids, get_operators, get_seat_types, get_hours_before_departure, get_date_of_journey

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
            className='mb-4'
        )
    ])

def create_seat_type_slicer():
    """Create a dropdown slicer for seat types"""
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
            create_seat_type_slicer(),
            create_date_range_slicer()
        ]),
        className='mb-4'
    )
