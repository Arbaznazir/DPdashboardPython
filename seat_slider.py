import dash
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
import pandas as pd

def create_seat_price_slider(df):
    """
    Create a simple table to display seat-wise pricing data
    
    Args:
        df: DataFrame containing seat_number, actual_fare, and final_price columns
        
    Returns:
        A Dash component with the table view of seat prices
    """
    if df is None or df.empty:
        return html.Div([
            html.P("No seat data available for the selected schedule.", className="text-muted text-center")
        ])
    
    # Ensure we have distinct seat numbers only
    df = df.drop_duplicates(subset=['seat_number'])
    
    # Convert seat_number to numeric for proper sorting
    df['seat_number'] = pd.to_numeric(df['seat_number'], errors='coerce')
    
    # Sort by seat number in ascending order (numerically)
    df = df.sort_values('seat_number', ascending=True)
    
    # Create a simple table with seat number, actual price and model price
    # Rename final_price to model_price for display
    table = dash_table.DataTable(
        id='seat-price-table',
        columns=[
            {"name": "Seat Number", "id": "seat_number"},
            {"name": "Actual Price", "id": "actual_fare"},
            {"name": "Model Price", "id": "final_price"}
        ],
        data=df[['seat_number', 'actual_fare', 'final_price']].to_dict('records'),
        page_action='none',  # Show all rows without pagination
        style_table={'overflowX': 'auto', 'overflowY': 'auto', 'height': '500px'},
        style_cell={
            'textAlign': 'center',
            'padding': '8px',
            'minWidth': '100px', 
            'width': '150px', 
            'maxWidth': '200px',
        },
        style_header={
            'backgroundColor': 'rgb(230, 230, 230)',
            'fontWeight': 'bold',
            'textAlign': 'center'
        },
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': 'rgb(248, 248, 248)'
            }
        ],
        sort_action='native',
        filter_action='native',
    )
    
    return html.Div([
        table
    ], className="mb-4")

def create_seat_details_card(seat_data):
    """
    Create a card to display detailed information for a selected seat
    
    Args:
        seat_data: Dictionary with seat details (seat_number, actual_fare, final_price)
        
    Returns:
        A Dash Bootstrap card component
    """
    if seat_data is None:
        return html.Div()
    
    # Calculate price difference and percentage
    actual_fare = seat_data.get('actual_fare', 0)
    final_price = seat_data.get('final_price', 0)
    
    if actual_fare and final_price:
        price_diff = final_price - actual_fare
        if actual_fare != 0:
            price_diff_pct = (price_diff / actual_fare) * 100
        else:
            price_diff_pct = 0
    else:
        price_diff = 0
        price_diff_pct = 0
    
    # Determine color based on price difference
    if price_diff > 0:
        diff_color = "success"
        diff_icon = "fas fa-arrow-up"
    elif price_diff < 0:
        diff_color = "danger"
        diff_icon = "fas fa-arrow-down"
    else:
        diff_color = "secondary"
        diff_icon = "fas fa-equals"
    
    return dbc.Card(
        dbc.CardBody([
            html.H5(f"Seat {seat_data.get('seat_number', 'N/A')} Details", className="card-title"),
            html.Div([
                html.Div([
                    html.P("Actual Fare:", className="fw-bold mb-0"),
                    html.H4(f"${actual_fare:,.2f}", className="text-success")
                ], className="col-4"),
                html.Div([
                    html.P("Final Price:", className="fw-bold mb-0"),
                    html.H4(f"${final_price:,.2f}", className="text-primary")
                ], className="col-4"),
                html.Div([
                    html.P("Price Difference:", className="fw-bold mb-0"),
                    html.Div([
                        html.I(className=f"{diff_icon} me-2"),
                        html.Span(f"${abs(price_diff):,.2f} ({abs(price_diff_pct):.1f}%)")
                    ], className=f"text-{diff_color} h4")
                ], className="col-4")
            ], className="row")
        ]),
        className="mt-3"
    )
