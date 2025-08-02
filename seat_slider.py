import dash
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
import pandas as pd

def create_seat_price_slider(df):
    """
    Create a modern table to display seat-wise pricing data
    
    Args:
        df: DataFrame containing seat_number, actual_fare, and final_price columns
        
    Returns:
        A Dash component with the table view of seat prices
    """
    if df is None or df.empty:
        return html.Div([
            html.Div([
                html.I(className="fas fa-chair fa-3x text-info mb-3"),
                html.H5("No seat data available for the selected schedule.", className="text-white")
            ], className="text-center p-5 bg-dark rounded shadow-sm")
        ])
    
    # Ensure we have distinct seat numbers only
    df = df.drop_duplicates(subset=['seat_number'])
    
    # Convert seat_number to numeric for proper sorting
    df['seat_number'] = pd.to_numeric(df['seat_number'], errors='coerce')
    
    # Sort by seat number in ascending order (numerically)
    df = df.sort_values('seat_number', ascending=True)
    
    # Format prices with dollar sign and 2 decimal places
    df['actual_fare'] = df['actual_fare'].apply(lambda x: f"${x:.2f}")
    df['final_price'] = df['final_price'].apply(lambda x: f"${x:.2f}")
    
    # Create a modern table with seat number, actual price and model price
    table = dash_table.DataTable(
        id='seat-price-table',
        columns=[
            {"name": ["Seat Details", "Seat Number"], "id": "seat_number"},
            {"name": ["Price Information", "Actual Price"], "id": "actual_fare"},
            {"name": ["Price Information", "Model Price"], "id": "final_price"}
        ],
        data=df[['seat_number', 'actual_fare', 'final_price']].to_dict('records'),
        page_action='none',  # Show all rows without pagination
        style_table={
            'overflowX': 'auto', 
            'overflowY': 'auto', 
            'height': '500px',
            'backgroundColor': '#27293d',
            'border': '1px solid #444',
            'borderRadius': '10px'
        },
        style_cell={
            'textAlign': 'center',
            'padding': '12px 8px',
            'minWidth': '100px', 
            'width': '150px', 
            'maxWidth': '200px',
            'backgroundColor': '#27293d',
            'color': 'white',
            'fontFamily': 'Poppins, sans-serif',
            'border': '1px solid #444'
        },
        style_header={
            'backgroundColor': '#1d8cf8',
            'color': 'white',
            'fontWeight': 'bold',
            'textAlign': 'center',
            'padding': '12px 8px',
            'border': '1px solid #1d8cf8'
        },
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': '#2c2f43'
            },
            {
                'if': {'column_id': 'actual_fare'},
                'color': '#00f2c3'
            },
            {
                'if': {'column_id': 'final_price'},
                'color': '#fd5d93'
            }
        ],
        sort_action='native',
        filter_action='native',
        merge_duplicate_headers=True
    )
    
    return dbc.Card([
        dbc.CardHeader([
            html.H5("Seat-wise Pricing Analysis", className="mb-0 text-white"),
            html.Span(f"{len(df)} Seats", className="badge bg-success ms-2")
        ], className="d-flex align-items-center"),
        dbc.CardBody([
            table
        ])
    ], className="mb-4 shadow")

def create_seat_details_card(seat_data):
    """
    Create a modern card to display detailed information for a selected seat
    
    Args:
        seat_data: Dictionary with seat details (seat_number, actual_fare, final_price)
        
    Returns:
        A Dash Bootstrap card component with modern styling
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
        diff_gradient = "linear-gradient(45deg, #00f2c3, #0098f0)"
    elif price_diff < 0:
        diff_color = "danger"
        diff_icon = "fas fa-arrow-down"
        diff_gradient = "linear-gradient(45deg, #fd5d93, #ec250d)"
    else:
        diff_color = "info"
        diff_icon = "fas fa-equals"
        diff_gradient = "linear-gradient(45deg, #1d8cf8, #3358f4)"
    
    seat_number = seat_data.get('seat_number', 'N/A')
    
    return dbc.Card(
        [
            dbc.CardHeader(
                [
                    html.Div(
                        [
                            html.I(className="fas fa-chair fa-2x text-white opacity-25 position-absolute top-0 end-0 m-3"),
                            html.H4(["Seat ", html.Span(seat_number, className="badge bg-info ms-2"), " Details"], className="text-white mb-0")
                        ],
                        className="position-relative"
                    )
                ],
                className="bg-dark text-white"
            ),
            dbc.CardBody(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Div(
                                        [
                                            html.P("Actual Fare", className="text-muted mb-1 small text-uppercase"),
                                            html.H3(f"${actual_fare:,.2f}", className="text-success mb-0"),
                                            html.I(className="fas fa-dollar-sign position-absolute top-0 end-0 m-2 text-success opacity-25 fa-2x")
                                        ],
                                        className="p-3 bg-dark rounded shadow-sm position-relative"
                                    )
                                ],
                                width=4
                            ),
                            dbc.Col(
                                [
                                    html.Div(
                                        [
                                            html.P("Model Price", className="text-muted mb-1 small text-uppercase"),
                                            html.H3(f"${final_price:,.2f}", className="text-primary mb-0"),
                                            html.I(className="fas fa-chart-line position-absolute top-0 end-0 m-2 text-primary opacity-25 fa-2x")
                                        ],
                                        className="p-3 bg-dark rounded shadow-sm position-relative"
                                    )
                                ],
                                width=4
                            ),
                            dbc.Col(
                                [
                                    html.Div(
                                        [
                                            html.P("Price Difference", className="text-muted mb-1 small text-uppercase"),
                                            html.Div(
                                                [
                                                    html.I(className=f"{diff_icon} me-2"),
                                                    html.Span(f"${abs(price_diff):,.2f}"),
                                                    html.Span(f" ({abs(price_diff_pct):.1f}%)", className="ms-1 small")
                                                ],
                                                className=f"text-{diff_color} h3 mb-0"
                                            )
                                        ],
                                        className="p-3 bg-dark rounded shadow-sm position-relative",
                                        style={"background": diff_gradient}
                                    )
                                ],
                                width=4
                            )
                        ]
                    )
                ],
                className="bg-gray-800"
            )
        ],
        className="mt-4 shadow border-0",
        style={"backgroundColor": "#27293d", "borderRadius": "10px"}
    )
