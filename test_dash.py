import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from db_utils import get_schedule_ids

# Initialize Dash app with Bootstrap theme
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True
)

# App layout
app.layout = dbc.Container([
    # Header
    dbc.Row([
        dbc.Col([
            html.H1("Dynamic Pricing Dashboard - Test", className="mb-2"),
            html.P("Testing basic functionality", className="text-muted")
        ], width=12)
    ], className="mb-4 mt-4"),
    
    # Test schedule ID dropdown
    dbc.Row([
        dbc.Col([
            html.Label("Schedule ID Test", className="fw-bold"),
            dcc.Dropdown(
                id="test-dropdown",
                options=[{"label": f"Test Option {i}", "value": i} for i in range(1, 6)],
                value=1
            )
        ], width=6)
    ], className="mb-4"),
    
    # Test database connection
    dbc.Row([
        dbc.Col([
            html.Div(id="db-test-output")
        ], width=12)
    ])
])

@app.callback(
    dash.dependencies.Output("db-test-output", "children"),
    [dash.dependencies.Input("test-dropdown", "value")]
)
def update_output(value):
    try:
        # Try to get schedule IDs from database
        schedule_ids = get_schedule_ids()
        if schedule_ids:
            return html.Div([
                html.H4("Database Connection Successful"),
                html.P(f"Found {len(schedule_ids)} schedule IDs"),
                html.P(f"First 5 schedule IDs: {schedule_ids[:5]}")
            ], className="alert alert-success")
        else:
            return html.Div([
                html.H4("Database Connection Successful"),
                html.P("No schedule IDs found in the database")
            ], className="alert alert-warning")
    except Exception as e:
        return html.Div([
            html.H4("Database Connection Error"),
            html.P(f"Error: {str(e)}")
        ], className="alert alert-danger")

if __name__ == "__main__":
    app.run_server(debug=True, port=8051)
