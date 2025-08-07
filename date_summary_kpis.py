import dash
from dash import html
import dash_bootstrap_components as dbc
from db_utils_summary import get_price_summary_by_date
from date_utils import is_past_date
from kpis import create_kpi_card

def create_date_summary_kpis(date_of_journey=None):
    """
    Create 6 KPI cards (3 per row) showing price summaries for a selected past date
    Only shows KPIs if a past date is selected
    """
    # Check if date is in the past
    if not date_of_journey or not is_past_date(date_of_journey):
        # Return empty div if no date selected or date is not in the past
        return html.Div(id="date-summary-kpis-container")
    
    # Get price summary data for the selected date
    price_summary = get_price_summary_by_date(date_of_journey)
    
    # Extract data for easier access
    seat_prices = price_summary['seat_prices']
    seat_wise_prices = price_summary['seat_wise_prices']
    
    # Format values for display
    sp_actual = f"${seat_prices['actual_sum']:.2f}"
    sp_model = f"${seat_prices['model_sum']:.2f}"
    # Always show absolute value for delta (no negative sign)
    sp_delta = f"${abs(seat_prices['delta']):.2f}"
    
    swp_actual = f"${seat_wise_prices['actual_sum']:.2f}"
    swp_model = f"${seat_wise_prices['model_sum']:.2f}"
    # Always show absolute value for delta (no negative sign)
    swp_delta = f"${abs(seat_wise_prices['delta']):.2f}"
    
    # Determine colors based on business logic:
    # Green when model > actual (good for business)
    # Red when actual > model (bad for business)
    sp_delta_color = "success" if seat_prices['model_sum'] > seat_prices['actual_sum'] else "danger"
    swp_delta_color = "success" if seat_wise_prices['model_sum'] > seat_wise_prices['actual_sum'] else "danger"
    
    # Create KPI cards for seat_prices_raw
    sp_actual_card = create_kpi_card(
        "Total Historic Price (Schedule)",
        sp_actual,
        f"Sum of all schedule prices on {date_of_journey}",
        "primary",
        "money-bill-wave"
    )
    
    sp_model_card = create_kpi_card(
        "Total Model Price (Schedule)",
        sp_model,
        f"Sum of all schedule model prices on {date_of_journey}",
        "info",
        "calculator"
    )
    
    sp_delta_card = create_kpi_card(
        "Total Price Delta (Schedule)",
        sp_delta,
        "Difference between historic and model prices",
        sp_delta_color,
        "exchange-alt"
    )
    
    # Create KPI cards for seat_wise_prices_raw
    swp_actual_card = create_kpi_card(
        "Total Historic Price (Seat)",
        swp_actual,
        f"Sum of all seat prices on {date_of_journey}",
        "primary",
        "chair"
    )
    
    swp_model_card = create_kpi_card(
        "Total Model Price (Seat)",
        swp_model,
        f"Sum of all seat model prices on {date_of_journey}",
        "info",
        "calculator-alt"
    )
    
    swp_delta_card = create_kpi_card(
        "Total Price Delta (Seat)",
        swp_delta,
        "Difference between historic and model seat prices",
        swp_delta_color,
        "exchange-alt"
    )
    
    # Create layout with two rows, 3 cards per row
    return html.Div([
        # Title for the section
        html.H4("Date Summary KPIs", className="text-center mb-3"),
        
        # First row - Schedule level KPIs
        dbc.Row([
            dbc.Col(sp_actual_card, width=4),
            dbc.Col(sp_model_card, width=4),
            dbc.Col(sp_delta_card, width=4)
        ], className="mb-4"),
        
        # Second row - Seat level KPIs
        dbc.Row([
            dbc.Col(swp_actual_card, width=4),
            dbc.Col(swp_model_card, width=4),
            dbc.Col(swp_delta_card, width=4)
        ])
    ], id="date-summary-kpis-container", className="mt-4")
