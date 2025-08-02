import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
import pandas as pd
import base64
import os

def create_seat_map(df):
    """
    Create a seat map visualization for seat-wise pricing data
    
    Args:
        df: DataFrame containing seat_number, actual_fare, final_price columns
        
    Returns:
        A Dash component with the seat map visualization
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
    
    # Calculate delta (model_price - actual_price)
    # Positive delta means model price is higher than actual price
    df['actual_numeric'] = pd.to_numeric(df['actual_fare'], errors='coerce')
    df['final_numeric'] = pd.to_numeric(df['final_price'], errors='coerce')
    df['price_delta'] = df['final_numeric'] - df['actual_numeric']
    
    # Format prices with dollar sign and 2 decimal places
    df['actual_fare_formatted'] = df['actual_numeric'].apply(lambda x: f"${x:.2f}")
    df['final_price_formatted'] = df['final_numeric'].apply(lambda x: f"${x:.2f}")
    df['delta_formatted'] = df['price_delta'].apply(lambda x: f"${abs(x):.2f}")
    
    # Get the SVG files
    positive_svg_path = os.path.join('d:\\Programming\\DP-Dashboard', 'positive_delta.svg')
    negative_svg_path = os.path.join('d:\\Programming\\DP-Dashboard', 'negative_delta.svg')
    
    # Read SVG files
    try:
        with open(positive_svg_path, 'rb') as f:
            positive_svg = f.read()
            positive_svg_base64 = base64.b64encode(positive_svg).decode('utf-8')
        
        with open(negative_svg_path, 'rb') as f:
            negative_svg = f.read()
            negative_svg_base64 = base64.b64encode(negative_svg).decode('utf-8')
    except Exception as e:
        print(f"Error reading SVG files: {e}")
        return html.Div(f"Error loading SVG files: {str(e)}", className="text-danger")
    
    # Create a dynamic seat map layout based on the actual seat numbers available
    # Sort seat numbers numerically
    seat_numbers = sorted([int(row['seat_number']) for _, row in df.iterrows() if pd.notna(row['seat_number'])])
    
    # Create a dictionary for quick seat lookup
    seat_dict = {int(row['seat_number']): row for _, row in df.iterrows() if pd.notna(row['seat_number'])}
    
    # Group seats into rows with max 13 seats per row
    seats_per_row = 13
    seat_rows = [seat_numbers[i:i+seats_per_row] for i in range(0, len(seat_numbers), seats_per_row)]
    
    # Create rows based on the dynamic layout
    rows = []
    
    # Process each row of seats
    for row_seats in seat_rows:
        seat_items = []
        
        for seat_number in row_seats:
            # Get seat data from dictionary
            seat = seat_dict[seat_number]
            actual_price = seat['actual_fare_formatted']
            model_price = seat['final_price_formatted']
            delta = seat['delta_formatted']
            delta_value = seat['price_delta']
            
            # Choose SVG based on delta
            svg_base64 = positive_svg_base64 if delta_value > 0 else negative_svg_base64
            
            # Create tooltip content
            tooltip_content = html.Div([
                html.H6(f"Seat: {seat_number}", className="mb-2 font-weight-bold"),
                html.P(f"Actual Price: {actual_price}", className="mb-1"),
                html.P(f"Model Price: {model_price}", className="mb-1"),
                html.P([
                    "Delta: ",
                    html.Span(
                        delta, 
                        style={"color": "#51ff45" if delta_value > 0 else "#f54040"}
                    )
                ], className="mb-0")
            ], className="p-2 text-dark")
            
            # Always use white text for seat numbers
            text_color = "white"
            
            # Create seat item with tooltip
            seat_item = html.Div(
                [
                    html.Div(
                        [
                            html.Img(
                                src=f"data:image/svg+xml;base64,{svg_base64}",
                                style={"width": "45px", "height": "45px", "position": "relative"}
                            ),
                            html.Div(
                                f"{seat_number}",
                                style={
                                    "position": "absolute",
                                    "top": "36%",  # Adjusted to account for SVG shape
                                    "left": "46%",
                                    "transform": "translate(-50%, -50%)",
                                    "color": text_color,
                                    "fontWeight": "bold",
                                    "fontSize": "10px",
                                    "textAlign": "center",
                                    "width": "100%",
                                    "height": "100%",
                                    "display": "flex",
                                    "justifyContent": "center",
                                    "alignItems": "center",
                                    "margin": "0",
                                    "padding": "0",
                                    "pointerEvents": "none"  # Ensures text doesn't interfere with click events
                                }
                            )
                        ],
                        style={"position": "relative"}
                    ),
                    dbc.Tooltip(
                        tooltip_content,
                        target=f"seat-{seat_number}",
                        placement="top"
                    )
                ],
                id=f"seat-{seat_number}",
                className="mx-1 my-1",
                style={"display": "inline-block", "cursor": "pointer"}
            )
            
            seat_items.append(seat_item)
        
        # Add row to layout with proper styling
        rows.append(
            dbc.Row(
                [dbc.Col(seat_item, width="auto", className="px-0") for seat_item in seat_items],
                className="mb-2 justify-content-center"
            )
        )
    
    # Create the final layout
    return dbc.Card([
        dbc.CardHeader([
            html.H5("Seat Map Visualization", className="mb-0 text-white"),
            html.Span(f"{len(df)} Seats", className="badge bg-success ms-2")
        ], className="d-flex align-items-center"),
        dbc.CardBody([
            html.Div(rows, className="text-center")
        ], className="bg-dark")
    ], className="mb-4")
