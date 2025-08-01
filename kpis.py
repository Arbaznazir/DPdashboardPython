import dash
from dash import html
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from measures import get_kpi_data
from db_utils import get_actual_price, get_model_price, get_demand_index
from price_utils import get_prices_by_schedule_and_hour, get_total_seat_prices

def create_kpi_card(title, value, subtitle=None, color="primary", icon=None, text_color=None):
    """Create a KPI card component with modern styling"""
    # Apply text color style if provided
    value_style = {'font-size': '1.8rem', 'font-weight': '700'}
    if text_color:
        value_style['color'] = text_color
    
    # Define gradient backgrounds based on color
    gradient_map = {
        "primary": "linear-gradient(45deg, #1d8cf8, #3358f4)",
        "success": "linear-gradient(45deg, #00bf9a, #46c37b)",
        "warning": "linear-gradient(45deg, #f5a623, #ff9f43)",
        "danger": "linear-gradient(45deg, #fd5d93, #ec250d)",
        "info": "linear-gradient(45deg, #11cdef, #1171ef)",
        "light": "linear-gradient(45deg, #ebeff4, #ced4da)",
        "dark": "linear-gradient(45deg, #212529, #343a40)",
    }
    
    gradient_bg = gradient_map.get(color, gradient_map["primary"])
    
    icon_element = html.Div(
        html.Div(
            html.I(className=f"fas fa-{icon} fa-2x"),
            className="icon-circle"
        ),
        className="icon-shape",
        style={
            'position': 'absolute',
            'right': '15px',
            'top': '15px',
            'opacity': '0.4'
        }
    ) if icon else None
    
    card_content = [
        icon_element,
        html.Div([
            html.H6(title, className="text-white mb-1 font-weight-bold", 
                   style={'font-size': '0.9rem', 'text-transform': 'uppercase', 'letter-spacing': '0.5px'}),
            html.H4(value, className="mb-0 text-white", style=value_style),
            html.Hr(className="my-2", style={'background-color': 'rgba(255,255,255,0.3)', 'opacity': '0.3'}) if subtitle else None,
            html.P(subtitle, className="text-white-50 mt-2 mb-0 small") if subtitle else None
        ])
    ]
    
    return dbc.Card(
        dbc.CardBody(card_content),
        className="kpi-card shadow mb-4",
        style={
            'background': gradient_bg,
            'border-radius': '10px',
            'border': 'none',
            'overflow': 'hidden',
            'position': 'relative',
            'transition': 'transform 0.3s ease',
            'min-height': '140px'
        }
    )

def create_kpi_row(schedule_id=None, operator_id=None, seat_type=None, hours_before_departure=None, date_of_journey=None):
    """Create a row of KPI cards"""
    kpi_data = get_kpi_data(schedule_id, operator_id, seat_type, hours_before_departure, date_of_journey)
    
    # We'll keep these for reference but they won't be the main KPIs
    avg_actual_price_card = create_kpi_card(
        "Average Actual Price",
        f"${kpi_data['avg_actual_fare']}",
        "Average across all seats",
        "light",
        "money-bill-wave"
    )
    
    avg_model_price_card = create_kpi_card(
        "Average Model Price",
        f"${kpi_data['avg_model_price']}",
        "Average across all seats",
        "light",
        "calculator"
    )
    
    delta_card = create_kpi_card(
        "Price Delta",
        f"${kpi_data['avg_delta']} ({kpi_data['avg_delta_percentage']}%)",
        "Difference between actual and model",
        "success" if kpi_data['avg_delta'] > 0 else "warning",
        "exchange-alt"
    )
    
    occupancy_card = create_kpi_card(
        "Occupancy",
        f"{kpi_data['avg_occupancy']}%",
        f"Expected: {kpi_data['avg_expected_occupancy']}%",
        "primary",
        "users"
    )
    
    # Create a list to hold all the price KPI cards
    price_kpi_cards = []
    
    # Only calculate prices if required filters are selected
    if schedule_id and hours_before_departure is not None:
        print(f"KPI DEBUG: Getting prices for schedule_id={schedule_id}, hours_before_departure={hours_before_departure}")
        
        # Get all prices for this schedule ID and hour before departure
        price_data = get_prices_by_schedule_and_hour(schedule_id, hours_before_departure)
        
        # If seat_type is specified, only show that one
        if seat_type and seat_type in price_data:
            seat_types = [seat_type]
        else:
            # Otherwise, use all seat types from the price data
            seat_types = list(price_data.keys())
        
        print(f"KPI DEBUG: Processing prices for seat types: {seat_types}")
        
        # Get demand index once for the schedule (same for all seat types)
        try:
            demand_index = get_demand_index(schedule_id, hours_before_departure)
            print(f"KPI DEBUG: Raw demand index value: {demand_index}, type: {type(demand_index)}")
            
            if demand_index is not None:
                # If it's already a string like 'M/L', use it directly
                if isinstance(demand_index, str):
                    # Check if it's a string like 'M/L'
                    if '/' in demand_index:
                        demand_index_display = demand_index
                        print(f"KPI DEBUG: Using demand index string value directly: {demand_index_display}")
                    else:
                        # Try to convert to float for formatting
                        try:
                            demand_index_float = float(demand_index)
                            demand_index_display = f"{demand_index_float:.2f}"
                            print(f"KPI DEBUG: Converted string demand index to float: {demand_index_display}")
                        except (ValueError, TypeError):
                            demand_index_display = demand_index
                            print(f"KPI DEBUG: Using demand index string value: {demand_index_display}")
                # If it's a float or other numeric type
                else:
                    try:
                        demand_index_float = float(demand_index)
                        demand_index_display = f"{demand_index_float:.2f}"
                        print(f"KPI DEBUG: Formatted numeric demand index: {demand_index_display}")
                    except (ValueError, TypeError) as e:
                        print(f"KPI DEBUG: Error formatting demand index: {e}")
                        demand_index_display = str(demand_index)
            else:
                demand_index_display = "N/A"
                print(f"KPI DEBUG: No demand index found for schedule {schedule_id}")
        except Exception as e:
            print(f"Error getting demand index: {e}")
            demand_index_display = "N/A"
            
        # For each seat type, create a KPI card
        for st in seat_types:
            # Get prices from the price data
            if st in price_data:
                actual_price = price_data[st]['actual_price']
                model_price = price_data[st]['model_price']
                print(f"KPI DEBUG: Prices for {st}: actual={actual_price}, model={model_price}")
            else:
                actual_price = None
                model_price = None
                print(f"KPI DEBUG: No price data found for seat type {st}")
            
            # Ensure both prices are numeric
            try:
                if actual_price is not None:
                    actual_price = float(actual_price)
                if model_price is not None:
                    model_price = float(model_price)
            except (ValueError, TypeError) as e:
                print(f"Error converting prices to float: {e}")
                print(f"Actual price: {actual_price}, type: {type(actual_price)}")
                print(f"Model price: {model_price}, type: {type(model_price)}")
                # Set to None if conversion fails
                if actual_price is not None and not isinstance(actual_price, (int, float)):
                    actual_price = None
                if model_price is not None and not isinstance(model_price, (int, float)):
                    model_price = None
            
            # Default values
            current_actual_price = "N/A"
            current_model_price = "N/A"
            current_price_diff = "N/A"
            price_diff_color = "black"
            
            # Calculate price difference if both prices are available
            if actual_price is not None and model_price is not None:
                # Ensure values are numeric before arithmetic operations
                try:
                    actual_price_float = float(actual_price)
                    model_price_float = float(model_price)
                    price_diff = actual_price_float - model_price_float
                    
                    # Format the values for display
                    current_actual_price = f"${actual_price_float:,.2f}"
                    current_model_price = f"${model_price_float:,.2f}"
                except (ValueError, TypeError) as e:
                    print(f"Error converting prices to float: {e}")
                    print(f"Actual price type: {type(actual_price)}, value: {actual_price}")
                    print(f"Model price type: {type(model_price)}, value: {model_price}")
                    # Set default values if conversion fails
                    current_actual_price = f"${str(actual_price)}"
                    current_model_price = f"${str(model_price)}"
                    price_diff = 0
                
                # Format price difference with color based on value
                try:
                    # Model price should be higher than actual price for optimal pricing
                    # So positive delta (actual > model) is bad, negative delta (model > actual) is good
                    if price_diff > 0:
                        current_price_diff = f"${price_diff:,.2f}"
                        price_diff_color = "#f5365c"  # Bright red for positive delta
                    elif price_diff < 0:
                        # Remove negative sign as requested - delta is always a gain
                        current_price_diff = f"${abs(price_diff):,.2f}"
                        price_diff_color = "#2dce89"  # Bright green for negative delta
                    else:
                        current_price_diff = f"${price_diff:,.2f}"
                except Exception as e:
                    print(f"Error formatting price difference: {e}")
                    current_price_diff = "N/A"
                    price_diff_color = "black"
            else:
                # If either price is not available, show appropriate message
                if actual_price is not None:
                    current_actual_price = f"${actual_price:,.2f}"
                    
                if model_price is not None:
                    current_model_price = f"${model_price:,.2f}"
            
            # Create KPI cards for this seat type
            current_actual_price_card = create_kpi_card(
                "Actual Price",
                current_actual_price,
                f"For {st}",
                "success",
                "money-bill-wave"
            )
            
            current_model_price_card = create_kpi_card(
                "Model Price",
                current_model_price,
                f"For {st}",
                "info",
                "calculator"
            )
            
            # Determine card color based on price difference
            price_diff_card_color = "success" if price_diff < 0 else "danger" if price_diff > 0 else "light"
            
            price_diff_card = create_kpi_card(
                "Price Difference",
                current_price_diff,
                f"For {st}",
                price_diff_card_color,
                "exchange-alt"
            )
            
            # We'll create the demand index card only once, outside this loop
            
            # Add the cards for this seat type to our list (without demand index)
            price_kpi_cards.extend([
                dbc.Col(current_actual_price_card, width=3),
                dbc.Col(current_model_price_card, width=3),
                dbc.Col(price_diff_card, width=3),
                # Only add the occupancy card for the first row
                dbc.Col(create_kpi_card(
                    "Occupancy",
                    f"{kpi_data['avg_occupancy']}%",
                    f"Expected: {kpi_data['avg_expected_occupancy']}%",
                    "primary",
                    "users"
                ) if len(price_kpi_cards) == 0 else None, width=3),
            ])
    
    # Create a single demand index card for the entire schedule
    if price_kpi_cards:  # Only if we have seat types and prices
        demand_index_card = create_kpi_card(
            "Demand Index",
            demand_index_display,
            "For Schedule",
            "warning",
            "chart-line"
        )
        # Add the demand index card at the top, before any seat type cards
        price_kpi_cards.insert(0, dbc.Col(demand_index_card, width=3))
        
        # Add total price KPI cards for all seats at the selected hour
        if schedule_id and hours_before_departure is not None:
            # Get total prices for all seats
            total_prices = get_total_seat_prices(schedule_id, hours_before_departure)
            
            # Format the total prices for display
            total_actual_price = "N/A"
            total_model_price = "N/A"
            total_price_diff = "N/A"
            price_diff_color = "light"
            
            if total_prices['total_actual_price'] is not None:
                total_actual_price = f"${float(total_prices['total_actual_price']):,.2f}"
                
            if total_prices['total_model_price'] is not None:
                total_model_price = f"${float(total_prices['total_model_price']):,.2f}"
                
            if total_prices['price_difference'] is not None:
                total_price_diff = f"${float(total_prices['price_difference']):,.2f}"
                # Determine color based on which price is higher
                if total_prices['total_actual_price'] > total_prices['total_model_price']:
                    price_diff_color = "danger"  # Red when actual > model
                else:
                    price_diff_color = "success"  # Green when model > actual
            
            # Create total price KPI cards
            total_actual_price_card = create_kpi_card(
                "Total Actual Price",
                total_actual_price,
                "Sum for All Seats",
                "success",
                "money-bill-wave"
            )
            
            total_model_price_card = create_kpi_card(
                "Total Model Price",
                total_model_price,
                "Sum for All Seats",
                "info",
                "calculator"
            )
            
            total_price_diff_card = create_kpi_card(
                "Total Price Difference",
                total_price_diff,
                "Sum for All Seats",
                price_diff_color,
                "exchange-alt"
            )
            
            # Add a row for total price KPI cards
            price_kpi_cards.append(html.Div(style={"height": "20px"}))
            price_kpi_cards.append(html.H5("Total Prices for All Seats", className="text-center mt-4 mb-3"))
            price_kpi_cards.append(
                dbc.Row([
                    dbc.Col(total_actual_price_card, width=4),
                    dbc.Col(total_model_price_card, width=4),
                    dbc.Col(total_price_diff_card, width=4)
                ], className="mb-4")
            )
    
    # If no seat types were found or no prices were available, show placeholder cards
    if not price_kpi_cards:
        current_actual_price_card = create_kpi_card(
            "Actual Price",
            "No data",
            "Select filters",
            "success",
            "money-bill-wave"
        )
        
        current_model_price_card = create_kpi_card(
            "Model Price",
            "No data",
            "Select filters",
            "info",
            "calculator"
        )
        
        price_diff_card = create_kpi_card(
            "Price Difference",
            "No data",
            "Select filters",
            "light",
            "exchange-alt"
        )
        
        price_kpi_cards = [
            dbc.Col(current_actual_price_card, width=3),
            dbc.Col(current_model_price_card, width=3),
            dbc.Col(price_diff_card, width=3),
            dbc.Col(occupancy_card, width=3),
        ]
    
    # Create rows with 4 cards each
    kpi_rows = []
    for i in range(0, len(price_kpi_cards), 4):
        row_cards = price_kpi_cards[i:i+4]
        # If the row is not complete (less than 4 cards), add empty columns to fill
        while len(row_cards) < 4:
            row_cards.append(dbc.Col(None, width=3))
        kpi_rows.append(dbc.Row(row_cards, className="mb-4"))
    
    # Combine all rows into a single container
    return html.Div([
        html.H5("Pricing at Selected Hour", className="mb-3"),
        html.Div(kpi_rows)
    ])


# No longer needed - functionality integrated into create_kpi_row
