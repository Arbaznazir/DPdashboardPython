import dash
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
import pandas as pd

# This is a temporary file to demonstrate the fix for the column headers
# We'll create a function that generates the correct column headers for the seat-wise price tables

def create_actual_seat_wise_table(actual_seat_wise, actual_operator_name):
    """Create the actual operator's seat-wise prices table with correct column headers"""
    return html.Div([
        html.H5(f"{actual_operator_name} Seat-wise Prices"),
        dash_table.DataTable(
            id='actual-seat-wise-table',
            columns=[
                {"name": "Seat Number", "id": "seat_number"},
                {"name": "Seat Type", "id": "seat_type"},
                {"name": "Actual Fare", "id": "final_price", "type": "numeric", "format": {"specifier": "$.2f"}},
                {"name": "Schedule ID", "id": "schedule_id"}
            ],
            data=actual_seat_wise.to_dict('records') if not actual_seat_wise.empty else [],
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
    ])

# This function would replace the existing code in price_comparison.py
