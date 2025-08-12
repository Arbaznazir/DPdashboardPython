import dash
from dash import html, dcc, callback_context, dash_table
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import psycopg2
from db_utils import get_connection, execute_query

def get_operator_name_by_id(operator_id):
    """Get operator name based on operator_id
    
    Implements the SWITCH logic:
    OperatorName = 
    SWITCH(
        seat_prices[operator_id],
        191, "Pullman San Andress",
        296, "Pullman Bus TS",
        "Other"  -- Default
    )
    """
    # Ensure we're comparing the correct data types
    # Convert to integer or string for comparison
    try:
        # Try to convert to int first
        operator_id_int = int(operator_id)
        
        # Now do the comparison with integers
        if operator_id_int == 191:
            return "Pullman San Andreas"
        elif operator_id_int == 296:
            return "Pullman Bus TS"
        else:
            return "Other"
    except (TypeError, ValueError):
        # If conversion fails, try string comparison
        operator_id_str = str(operator_id)
        
        if operator_id_str == "191":
            return "Pullman San Andreas"
        elif operator_id_str == "296":
            return "Pullman Bus TS"
        else:
            return "Other"

def get_operators_with_dt():
    """Get unique operators from seat_prices_with_dt table"""
    query = """
    SELECT DISTINCT operator_id
    FROM seat_prices_with_dt
    ORDER BY operator_id
    """
    result = execute_query(query)
    return result

def get_dates_of_journey_with_dt():
    """Get all available dates of journey from seat_prices_with_dt table"""
    query = """
    SELECT DISTINCT date_of_journey
    FROM seat_prices_with_dt
    ORDER BY date_of_journey ASC
    """
    result = execute_query(query)
    return result

def get_matching_times_of_journey(date_of_journey, model_operator_id, actual_operator_id):
    """
    Get matching times of journey (departure_time) for two operators on a specific date
    """
    print(f"Searching for matching times: DOJ={date_of_journey}, Model Op={model_operator_id}, Actual Op={actual_operator_id}")
    
    # First check if departure_time is NULL for these operators
    check_query = """
    SELECT COUNT(*) as count
    FROM seat_prices_with_dt
    WHERE operator_id IN (%s, %s)
      AND date_of_journey = %s
      AND departure_time IS NOT NULL
    """
    check_result = execute_query(check_query, params=(model_operator_id, actual_operator_id, date_of_journey))
    
    if check_result is None or check_result.empty or check_result['count'].iloc[0] == 0:
        print(f"No non-NULL departure_times found for these operators on {date_of_journey}")
        # Return a default time for testing
        import pandas as pd
        return pd.DataFrame({'departure_time': ['08:00:00']})
    
    query = """
    SELECT DISTINCT a.departure_time
    FROM seat_prices_with_dt a
    JOIN seat_prices_with_dt b ON a.departure_time = b.departure_time
        AND a.date_of_journey = b.date_of_journey
    WHERE a.date_of_journey = %s
        AND a.operator_id = %s
        AND b.operator_id = %s
        AND a.departure_time IS NOT NULL
    ORDER BY a.departure_time
    """
    result = execute_query(query, params=(date_of_journey, model_operator_id, actual_operator_id))
    
    if result is None or result.empty:
        print("No matching times found in database query")
        # Return a default time for testing
        import pandas as pd
        return pd.DataFrame({'departure_time': ['08:00:00']})
    
    print(f"Found {len(result)} matching times: {result['departure_time'].tolist()}")
    return result

def get_matching_times_with_same_seat_types(date_of_journey, operator1_id, operator2_id):
    """
    Get matching departure times for two operators on a specific date
    where both operators have the same seat types available
    
    Args:
        date_of_journey (str): Date in format YYYY-MM-DD
        operator1_id (str): First operator ID
        operator2_id (str): Second operator ID
        
    Returns:
        pandas.DataFrame: DataFrame containing matching departure times
    """
    # Direct join approach as requested
    query = """
    SELECT DISTINCT a.departure_time
    FROM seat_prices_with_dt a
    JOIN seat_prices_with_dt b ON a.departure_time = b.departure_time
        AND a.date_of_journey = b.date_of_journey
        AND a.seat_type = b.seat_type
    WHERE a.date_of_journey = %s
        AND a.operator_id = %s
        AND b.operator_id = %s
        AND a.departure_time IS NOT NULL
    ORDER BY a.departure_time
    """
    
    result = execute_query(query, params=(date_of_journey, operator1_id, operator2_id))
    
    if result is None or result.empty:
        print(f"No matching times with same seat types found for operators {operator1_id} and {operator2_id} on {date_of_journey}")
        # For testing purposes, return a DataFrame with sample times
        return pd.DataFrame({'departure_time': ['08:00:00', '10:00:00', '19:00:00']})
    
    print(f"Found {len(result)} matching times with same seat types: {result['departure_time'].tolist()}")
    return result

def get_price_comparison_data(date_of_journey, model_operator_id, actual_operator_id, time_of_journey):
    """
    Get price comparison data for two operators on a specific date and time of journey
    """
    # Get model prices from seat_prices_with_dt
    model_query = """
    WITH latest_prices AS (
        SELECT DISTINCT ON (schedule_id, seat_type)
            seat_type,
            price,  -- For dynamic pricing model operator, use price column
            hours_before_departure,
            schedule_id,
            "TimeAndDateStamp"
        FROM seat_prices_with_dt
        WHERE date_of_journey = %s
            AND operator_id = %s
            AND departure_time = %s
        ORDER BY schedule_id, seat_type, "TimeAndDateStamp" DESC
    )
    SELECT 
        seat_type,
        price,
        hours_before_departure,
        schedule_id
    FROM latest_prices
    """
    # Cast operator_id to string to match database column type
    model_prices = execute_query(model_query, params=(date_of_journey, str(model_operator_id), time_of_journey))
    
    # Get actual prices from seat_prices_with_dt
    actual_query = """
    WITH latest_prices AS (
        SELECT DISTINCT ON (schedule_id, seat_type)
            seat_type,
            actual_fare as price,  -- For non-dynamic pricing operator, use actual_fare column
            hours_before_departure,
            schedule_id,
            "TimeAndDateStamp"
        FROM seat_prices_with_dt
        WHERE date_of_journey = %s
            AND operator_id = %s
            AND departure_time = %s
        ORDER BY schedule_id, seat_type, "TimeAndDateStamp" DESC
    )
    SELECT 
        seat_type,
        price,
        hours_before_departure,
        schedule_id
    FROM latest_prices
    """
    # Cast operator_id to string to match database column type
    actual_prices = execute_query(actual_query, params=(date_of_journey, str(actual_operator_id), time_of_journey))
    
    # Get model seat-wise prices
    model_seat_wise_query = """
    WITH relevant_schedules AS (
        SELECT schedule_id 
        FROM seat_prices_with_dt 
        WHERE date_of_journey = %s 
            AND operator_id = %s 
            AND departure_time = %s
    ),
    latest_snapshots AS (
        SELECT DISTINCT ON (swp.schedule_id, swp.seat_number)
            swp.schedule_id,
            swp.seat_number,
            swp."TimeAndDateStamp"
        FROM seat_wise_prices_with_dt swp
        JOIN relevant_schedules rs ON swp.schedule_id = rs.schedule_id
        WHERE swp.travel_date = %s
        ORDER BY swp.schedule_id, swp.seat_number, swp."TimeAndDateStamp" DESC
    )
    SELECT 
        swp.seat_number,
        swp.seat_type,
        swp.final_price,  -- For dynamic pricing model operator, use final_price column
        swp.schedule_id
    FROM seat_wise_prices_with_dt swp
    JOIN latest_snapshots ls 
        ON swp.schedule_id = ls.schedule_id 
        AND swp.seat_number = ls.seat_number 
        AND swp."TimeAndDateStamp" = ls."TimeAndDateStamp"
    """
    # Cast operator_id to string to match database column type
    model_seat_wise_prices = execute_query(model_seat_wise_query, 
                                           params=(date_of_journey, str(model_operator_id), time_of_journey, date_of_journey))
    
    # Get actual seat-wise prices
    actual_seat_wise_query = """
    WITH relevant_schedules AS (
        SELECT schedule_id 
        FROM seat_prices_with_dt 
        WHERE date_of_journey = %s 
            AND operator_id = %s 
            AND departure_time = %s
    ),
    latest_snapshots AS (
        SELECT DISTINCT ON (swp.schedule_id, swp.seat_number)
            swp.schedule_id,
            swp.seat_number,
            swp."TimeAndDateStamp"
        FROM seat_wise_prices_with_dt swp
        JOIN relevant_schedules rs ON swp.schedule_id = rs.schedule_id
        WHERE swp.travel_date = %s
        ORDER BY swp.schedule_id, swp.seat_number, swp."TimeAndDateStamp" DESC
    )
    SELECT 
        swp.seat_number,
        swp.seat_type,
        swp.actual_fare as final_price,
        swp.schedule_id
    FROM seat_wise_prices_with_dt swp
    JOIN latest_snapshots ls 
        ON swp.schedule_id = ls.schedule_id 
        AND swp.seat_number = ls.seat_number 
        AND swp."TimeAndDateStamp" = ls."TimeAndDateStamp"
    """
    # Cast operator_id to string to match database column type
    actual_seat_wise_prices = execute_query(actual_seat_wise_query, 
                                            params=(date_of_journey, str(actual_operator_id), time_of_journey, date_of_journey))
    
    return {
        'model_prices': model_prices,
        'actual_prices': actual_prices,
        'model_seat_wise_prices': model_seat_wise_prices,
        'actual_seat_wise_prices': actual_seat_wise_prices
    }

def get_operator_name_by_id(operator_id):
    """Get operator name based on operator_id"""
    if operator_id == 191:
        return "Pullman San Andreas"
    elif operator_id == 296:
        return "Pullman Bus"
    else:
        return f"Operator {operator_id}"

def create_price_comparison_layout():
    """Create the layout for the price comparison page"""
    # Get available operators
    operators_df = get_operators_with_dt()
    # Create options with explicit names instead of using operator IDs
    operator_options = [
        {'label': 'Pullman San Andreas', 'value': 191},
        {'label': 'Pullman Bus TS', 'value': 296}
    ]
    
    # Get available dates
    dates_df = get_dates_of_journey_with_dt()
    date_options = [{'label': date, 'value': date} for date in dates_df['date_of_journey'].tolist()]
    
    return html.Div([
        dbc.Card(
            dbc.CardBody([
                html.H2("Price Comparison Between Operators", className="mb-4 text-center"),
                
                # Filters row
                dbc.Row([
                    # Date of Journey
                    dbc.Col([
                        html.Label("Date of Journey"),
                        dcc.Dropdown(
                            id='price-comparison-doj',
                            options=date_options,
                            value=date_options[0]['value'] if date_options else None,
                            clearable=False,
                            className="mb-3",
                            style={'color': 'black', 'background-color': 'white'},
                            optionHeight=35
                        )
                    ], width=4),
                    
                    # Model Price Operator
                    dbc.Col([
                        html.Label("Model Price Operator"),
                        dcc.Dropdown(
                            id='model-operator',
                            options=operator_options,
                            value=None,
                            clearable=False,
                            className="mb-3",
                            style={'color': 'black', 'background-color': 'white'},
                            optionHeight=35
                        )
                    ], width=4),
                    
                    # Actual Price Operator
                    dbc.Col([
                        html.Label("Actual Price Operator"),
                        dcc.Dropdown(
                            id='actual-operator',
                            options=[],  # Will be populated based on model operator selection
                            value=None,
                            clearable=False,
                            className="mb-3",
                            style={'color': 'black', 'background-color': 'white'},
                            optionHeight=35
                        )
                    ], width=4)
                ]),
                
                # Time of Journey row
                dbc.Row([
                    dbc.Col([
                        html.Label("Time of Journey"),
                        dcc.Dropdown(
                            id='time-of-journey',
                            options=[],  # Will be populated based on operator selections
                            value=None,
                            clearable=False,
                            className="mb-3",
                            style={'color': 'black', 'background-color': 'white'},
                            optionHeight=35
                        )
                    ], width=4),
                    dbc.Col(width=8)  # Empty column for spacing
                ]),
                
                # Results section
                html.Div(id='price-comparison-results', className="mt-4"),
                
                # Loading indicator
                dcc.Loading(
                    id="loading-comparison",
                    type="circle",
                    children=html.Div(id="loading-output-comparison")
                )
            ]),
            className="shadow-sm mb-4 bg-dark text-white"
        )
    ])

def create_price_comparison_kpi_cards(comparison_data, model_operator_name, actual_operator_name):
    """Create KPI cards for price comparison"""
    if comparison_data is None or any(df.empty for df in comparison_data.values()):
        return html.Div("No data available for the selected criteria.")
    
    model_prices = comparison_data['model_prices']
    actual_prices = comparison_data['actual_prices']
    model_seat_wise = comparison_data['model_seat_wise_prices']
    actual_seat_wise = comparison_data['actual_seat_wise_prices']
    
    # Add origin and destination names
    # Default values if not available in the data
    origin_id = 1646  # Santiago
    destination_id = 1821  # La Serena
    
    # Map IDs to names
    origin_name = "Santiago" if origin_id == 1646 else "Other"
    destination_name = "La Serena" if destination_id == 1821 else "Other"
    
    # Calculate price totals
    try:
        # Ensure price values are numeric before calculations
        if model_prices is not None and not model_prices.empty:
            model_prices['price'] = pd.to_numeric(model_prices['price'], errors='coerce')
            model_total = model_prices['price'].sum()
        else:
            model_total = 0
            
        if actual_prices is not None and not actual_prices.empty:
            actual_prices['price'] = pd.to_numeric(actual_prices['price'], errors='coerce')
            actual_total = actual_prices['price'].sum()
        else:
            actual_total = 0
            
        print(f"Model total: {model_total}, Actual total: {actual_total}")
        price_diff = actual_total - model_total
        price_diff_abs = abs(price_diff)
        price_diff_color = "success" if model_total > actual_total else "danger"
    except Exception as e:
        print(f"Error calculating price totals: {e}")
        model_total = 0
        actual_total = 0
        price_diff = 0
        price_diff_abs = 0
        price_diff_color = "secondary"
    
    # We still need seat-wise data for tables, but we're removing the KPI cards
    # Process the data for tables
    if model_seat_wise is not None and not model_seat_wise.empty:
        model_seat_wise['final_price'] = pd.to_numeric(model_seat_wise['final_price'], errors='coerce')
    
    if actual_seat_wise is not None and not actual_seat_wise.empty:
        actual_seat_wise['final_price'] = pd.to_numeric(actual_seat_wise['final_price'], errors='coerce')
    
    # Create KPI cards
    return html.Div([
        html.H3("Price Comparison Summary", className="mb-3"),
        html.H5(f"Route: {origin_name} to {destination_name}", className="mb-3 text-muted"),
        
        # First row - Seat Prices - removed Status column and made other columns wider
        dbc.Row([
            # Model Price
            dbc.Col([
                dbc.Card(
                    dbc.CardBody([
                        html.H5(f"{model_operator_name} Price", className="card-title"),
                        html.H3(f"${model_total:.2f}", 
                               style={'font-weight': 'bold', 'color': '#00ffff'}),
                        html.P("Sum of model prices", className="card-text text-muted")
                    ]),
                    className="shadow-sm mb-4 bg-dark text-white",
                    style={'border-left': '4px solid #00ffff'}
                )
            ], width=4),
            
            # Actual Price
            dbc.Col([
                dbc.Card(
                    dbc.CardBody([
                        html.H5(f"{actual_operator_name} Historic Price", className="card-title"),
                        html.H3(f"${actual_total:.2f}", className="card-text text-warning", 
                               style={'font-weight': 'bold'}),
                        html.P("Sum of historic prices", className="card-text text-muted")
                    ]),
                    className="shadow-sm mb-4 bg-dark text-white",
                    style={'border-left': '4px solid #ffc107'}
                )
            ], width=4),
            
            # Price Difference
            dbc.Col([
                dbc.Card(
                    dbc.CardBody([
                        html.H5("Price Difference", className="card-title"),
                        html.H3(f"${price_diff_abs:.2f}", 
                               className=f"card-text text-{'success' if model_total > actual_total else 'danger'}",
                               style={'font-weight': 'bold'}),
                        html.P("Model - Historic", className="card-text text-muted")
                    ]),
                    className="shadow-sm mb-4 bg-dark text-white",
                    style={'border-left': f"4px solid {'#28a745' if model_total > actual_total else '#dc3545'}"}
                )
            ], width=4)
        ]),
        
        
        # Toggle button for details
        html.Div([
            dbc.Button(
                "Show/Hide Details", 
                id="toggle-details-button",
                color="secondary",
                className="mb-3"
            ),
        ], className="text-center mt-4"),
        
        # Details tables - initially hidden
        html.Div([
            html.H4("Detailed Price Comparison", className="mt-4 mb-3"),
            
            # Seat Type Prices
            html.H5("Prices by Seat Type", className="mt-4 mb-3"),
            dbc.Row([
            # Model prices table
            dbc.Col([
                html.H5(f"{model_operator_name} Prices by Seat Type"),
                dash_table.DataTable(
                    id='model-prices-table',
                    columns=[
                        {"name": "Seat Type", "id": "seat_type"},
                        {"name": "Price", "id": "price", "type": "numeric", "format": {"specifier": "$.2f"}},
                        {"name": "Hours Before", "id": "hours_before_departure"},
                        {"name": "Schedule ID", "id": "schedule_id"}
                    ],
                    data=model_prices.to_dict('records'),
                    style_table={'overflowX': 'auto'},
                    style_cell={
                        'backgroundColor': '#1e1e2f',
                        'color': 'white',
                        'textAlign': 'left'
                    },
                    style_header={
                        'backgroundColor': '#252538',
                        'fontWeight': 'bold'
                    }
                )
            ], width=6),
            
            # Actual prices table
            dbc.Col([
                html.H5(f"{actual_operator_name} Prices by Seat Type"),
                dash_table.DataTable(
                    id='actual-prices-table',
                    columns=[
                        {"name": "Seat Type", "id": "seat_type"},
                        {"name": "Price", "id": "price", "type": "numeric", "format": {"specifier": "$.2f"}},
                        {"name": "Hours Before", "id": "hours_before_departure"},
                        {"name": "Schedule ID", "id": "schedule_id"}
                    ],
                    data=actual_prices.to_dict('records'),
                    style_table={'overflowX': 'auto'},
                    style_cell={
                        'backgroundColor': '#1e1e2f',
                        'color': 'white',
                        'textAlign': 'left'
                    },
                    style_header={
                        'backgroundColor': '#252538',
                        'fontWeight': 'bold'
                    }
                )
            ], width=6)
            ]),
            
            # Seat-wise Prices
            html.H5("Seat-wise Prices", className="mt-4 mb-3"),
            dbc.Row([
            # Model seat-wise prices table
            dbc.Col([
                html.H5(f"{model_operator_name} Seat-wise Prices"),
                dash_table.DataTable(
                    id='model-seat-wise-table',
                    columns=[
                        {"name": "Seat Number", "id": "seat_number"},
                        {"name": "Seat Type", "id": "seat_type"},
                        {"name": "Final Price", "id": "final_price", "type": "numeric", "format": {"specifier": "$.2f"}},
                        {"name": "Schedule ID", "id": "schedule_id"}
                    ],
                    data=model_seat_wise.to_dict('records'),
                    style_table={'overflowX': 'auto'},
                    style_cell={
                        'backgroundColor': '#343a40',
                        'color': 'white',
                        'textAlign': 'left'
                    },
                    style_header={
                        'backgroundColor': '#212529',
                        'fontWeight': 'bold'
                    }
                )
            ], width=6),
            
            # Actual seat-wise prices table
            dbc.Col([
                html.H5(f"{actual_operator_name} Seat-wise Prices"),
                dash_table.DataTable(
                    id='actual-seat-wise-table',
                    columns=[
                        {"name": "Seat Number", "id": "seat_number"},
                        {"name": "Seat Type", "id": "seat_type"},
                        {"name": "Actual Fare", "id": "actual_fare", "type": "numeric", "format": {"specifier": "$.2f"}},
                        {"name": "Schedule ID", "id": "schedule_id"}
                    ],
                    data=actual_seat_wise.to_dict('records'),
                    style_table={'overflowX': 'auto'},
                    style_cell={
                        'backgroundColor': '#343a40',
                        'color': 'white',
                        'textAlign': 'left'
                    },
                    style_header={
                        'backgroundColor': '#212529',
                        'fontWeight': 'bold'
                    }
                )
            ], width=6)
            ])
        ], id="details-container")
    ])

def register_price_comparison_callbacks(app):
    """Register callbacks for price comparison page"""
    
    # Toggle details visibility
    @app.callback(
        Output('details-container', 'style'),
        Input('toggle-details-button', 'n_clicks'),
        State('details-container', 'style')
    )
    def toggle_details(n_clicks, current_style):
        if n_clicks is None:
            # Initial load - hide details
            return {'display': 'none'}
        
        if current_style is None or 'display' not in current_style:
            current_style = {}
        
        if current_style.get('display') == 'none':
            return {'display': 'block'}
        else:
            return {'display': 'none'}
    
    # Update actual operator dropdown based on model operator selection
    @app.callback(
        Output('actual-operator', 'options'),
        Output('actual-operator', 'value'),
        Input('model-operator', 'value')
    )
    def update_actual_operator_dropdown(model_operator):
        if model_operator is None:
            return [], None
        
        # Create options with explicit names instead of using operator IDs
        all_operators = {
            191: 'Pullman San Andreas',
            296: 'Pullman Bus TS'
        }
        
        # Filter out the selected model operator
        available_operators = [op for op in all_operators.keys() if op != model_operator]
        options = [{'label': all_operators[op], 'value': op} for op in available_operators]
        
        # Set default value to first available operator
        default_value = available_operators[0] if available_operators else None
        
        return options, default_value
    
    # Update time of journey dropdown based on operator selections and date
    @app.callback(
        Output('time-of-journey', 'options'),
        Output('time-of-journey', 'value'),
        Input('price-comparison-doj', 'value'),
        Input('model-operator', 'value'),
        Input('actual-operator', 'value')
    )
    def update_time_of_journey_dropdown(doj, model_operator, actual_operator):
        if None in [doj, model_operator, actual_operator]:
            print(f"Missing required values: DOJ={doj}, Model Op={model_operator}, Actual Op={actual_operator}")
            return [], None
        
        print(f"Getting matching times for DOJ={doj}, Model Op={model_operator}, Actual Op={actual_operator}")
        
        # Get matching times of journey with same seat types
        times_df = get_matching_times_with_same_seat_types(doj, model_operator, actual_operator)
        
        print(f"Found {len(times_df) if times_df is not None else 0} matching times")
        
        if times_df is None or times_df.empty:
            print("No matching times found")
            return [], None
        
        # Convert times to strings for dropdown
        times_list = times_df['departure_time'].tolist()
        print(f"Times found: {times_list}")
        
        options = [{'label': str(time), 'value': str(time)} for time in times_list]
        default_value = str(times_list[0]) if times_list else None
        
        return options, default_value
    
    # Update price comparison results
    @app.callback(
        Output('price-comparison-results', 'children'),
        Output('loading-output-comparison', 'children'),
        Input('price-comparison-doj', 'value'),
        Input('model-operator', 'value'),
        Input('actual-operator', 'value'),
        Input('time-of-journey', 'value')
    )
    def update_price_comparison_data(doj, model_operator, actual_operator, toj):
        print(f"Updating price comparison data: DOJ={doj}, Model Op={model_operator}, Actual Op={actual_operator}, TOJ={toj}")
        
        if None in [doj, model_operator, actual_operator, toj]:
            print("Missing required values for price comparison")
            return html.Div("Please select all filters to view comparison.", className="mt-3"), ""
        
        # Get price comparison data
        try:
            comparison_data = get_price_comparison_data(doj, model_operator, actual_operator, toj)
            print(f"Retrieved comparison data: {comparison_data is not None}")
            
            if comparison_data is None:
                return html.Div("No data available for the selected filters.", className="mt-3"), ""
            
            # Get operator names for display
            model_operator_name = get_operator_name_by_id(model_operator)
            actual_operator_name = get_operator_name_by_id(actual_operator)
            print(f"Operators: {model_operator_name} vs {actual_operator_name}")
            
            # Create KPI cards
            return create_price_comparison_kpi_cards(comparison_data, model_operator_name, actual_operator_name), ""
        except Exception as e:
            print(f"Error updating price comparison data: {e}")
            return html.Div(f"An error occurred: {str(e)}", className="mt-3 text-danger"), ""
