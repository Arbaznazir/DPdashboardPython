import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
from db_utils import get_actual_price, get_model_price

def create_price_kpis():
    """Create KPI cards for actual and model prices"""
    
    # Create a container for the KPI cards
    kpi_container = html.Div([
        html.H4("Price KPIs", className="mb-3"),
        
        # Actual Price KPI Card
        dbc.Card([
            dbc.CardHeader("Actual Price", className="fw-bold"),
            dbc.CardBody([
                html.H3(id="actual-price-value", children="-"),
                html.P("Current actual price based on selected filters", className="text-muted")
            ])
        ], className="mb-3"),
        
        # Model Price KPI Card
        dbc.Card([
            dbc.CardHeader("Model Price", className="fw-bold"),
            dbc.CardBody([
                html.H3(id="model-price-value", children="-"),
                html.P("Current model price based on selected filters", className="text-muted")
            ])
        ], className="mb-3"),
        
        # Price Delta KPI Card
        dbc.Card([
            dbc.CardHeader("Price Delta", className="fw-bold"),
            dbc.CardBody([
                html.H3(id="price-difference-value", children="-"),
                html.P("Delta between actual and model price", className="text-muted")
            ])
        ])
    ], className="mb-4")
    
    return kpi_container

@callback(
    [
        Output("actual-price-value", "children"),
        Output("model-price-value", "children"),
        Output("price-difference-value", "children")
    ],
    [
        Input("schedule-id-dropdown", "value"),
        Input("seat-type-dropdown", "value"),
        Input("hours-before-departure-dropdown", "value")
    ]
)
def update_price_kpis(schedule_id, seat_type, hours_before_departure):
    """Update price KPIs based on selected filters"""
    
    # Initialize with default values
    actual_price_display = "-"
    model_price_display = "-"
    price_diff_display = "-"
    
    # Only calculate prices if all required filters are selected
    if schedule_id and seat_type and hours_before_departure is not None:
        # Get actual price
        actual_price = get_actual_price(schedule_id, seat_type, hours_before_departure)
        
        # Get model price
        model_price = get_model_price(schedule_id, seat_type, hours_before_departure)
        
        # Calculate price difference if both prices are available
        if actual_price is not None and model_price is not None:
            # Ensure both are numeric before subtraction
            try:
                actual_price = float(actual_price) if isinstance(actual_price, (str, int)) else actual_price
                model_price = float(model_price) if isinstance(model_price, (str, int)) else model_price
                price_diff = actual_price - model_price
            except (ValueError, TypeError) as e:
                print(f"Error converting prices to float in kpi_components: actual={actual_price}, model={model_price}, error={e}")
                price_diff = 0
            
            # Format the values for display
            actual_price_display = f"${actual_price:,.2f}"
            model_price_display = f"${model_price:,.2f}"
            
            # Format price delta as absolute value (always positive)
            price_diff_abs = abs(price_diff)
            price_diff_display = html.Span(f"${price_diff_abs:,.2f}", style={"color": "green"})
        else:
            # If either price is not available, show appropriate message
            if actual_price is None:
                actual_price_display = "N/A"
            else:
                actual_price_display = f"${actual_price:,.2f}"
                
            if model_price is None:
                model_price_display = "N/A"
            else:
                model_price_display = f"${model_price:,.2f}"
                
            price_diff_display = "N/A"
    
    return actual_price_display, model_price_display, price_diff_display
