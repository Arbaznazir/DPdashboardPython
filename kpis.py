import dash
from dash import html
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from measures import get_kpi_data

def create_kpi_card(title, value, subtitle=None, color="primary", icon=None):
    """Create a KPI card component"""
    card_content = [
        html.Div([
            html.Div([
                html.H6(title, className="text-muted mb-1"),
                html.H4(value, className="mb-0")
            ], className="col-9"),
            html.Div([
                html.I(className=f"fas fa-{icon} fa-2x text-{color}")
            ], className="col-3 text-end") if icon else None
        ], className="row"),
        html.P(subtitle, className="text-muted mt-2 mb-0") if subtitle else None
    ]
    
    return dbc.Card(
        dbc.CardBody(card_content),
        className=f"border-start border-5 border-{color} shadow mb-4"
    )

def create_kpi_row(schedule_id=None, operator_id=None, seat_type=None, hours_before_departure=None, date_of_journey=None):
    """Create a row of KPI cards"""
    kpi_data = get_kpi_data(schedule_id, operator_id, seat_type, hours_before_departure, date_of_journey)
    
    actual_price_card = create_kpi_card(
        "Actual Price",
        f"₹{kpi_data['avg_actual_fare']}",
        "Average actual fare",
        "success",
        "money-bill-wave"
    )
    
    model_price_card = create_kpi_card(
        "Model Price",
        f"₹{kpi_data['avg_model_price']}",
        "Average model price",
        "info",
        "calculator"
    )
    
    delta_card = create_kpi_card(
        "Price Delta",
        f"₹{kpi_data['avg_delta']} ({kpi_data['avg_delta_percentage']}%)",
        "Difference between actual and model",
        "warning" if kpi_data['avg_delta'] < 0 else "success",
        "exchange-alt"
    )
    
    occupancy_card = create_kpi_card(
        "Occupancy",
        f"{kpi_data['avg_occupancy']}%",
        f"Expected: {kpi_data['avg_expected_occupancy']}%",
        "primary",
        "users"
    )
    
    return html.Div([
        dbc.Row([
            dbc.Col(actual_price_card, md=3),
            dbc.Col(model_price_card, md=3),
            dbc.Col(delta_card, md=3),
            dbc.Col(occupancy_card, md=3),
        ])
    ])
