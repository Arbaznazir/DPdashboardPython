# This is a temporary file to fix the actual seat-wise price table column header
# Replace the actual seat-wise prices table section in create_price_comparison_kpi_cards function

# Actual seat-wise prices table
dbc.Col([
    html.H5(f"{actual_operator_name} Seat-wise Prices"),
    dash_table.DataTable(
        id='actual-seat-wise-table',
        columns=[
            {"name": "Seat Number", "id": "seat_number"},
            {"name": "Seat Type", "id": "seat_type"},
            {"name": "Actual Fare", "id": "final_price", "type": "numeric", "format": {"specifier": "$.2f"}},
            {"name": "Schedule ID", "id": "schedule_id"}
        ],
        data=actual_seat_wise.to_dict('records'),
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
