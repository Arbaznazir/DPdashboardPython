import plotly.express as px
import plotly.graph_objects as go
from dash import dcc
import dash_bootstrap_components as dbc
from dash import html
import pandas as pd
from measures import get_price_trend_data, get_price_delta_data, get_occupancy_data, get_seat_wise_analysis, get_seat_wise_price_sum_by_hour

def create_price_trend_chart(schedule_id=None, operator_id=None, seat_type=None, hours_before_departure=None, date_of_journey=None):
    """Create a price trend chart comparing actual fare vs model price"""
    df = get_price_trend_data(schedule_id, operator_id, seat_type, hours_before_departure, date_of_journey)
    
    if df.empty:
        return dcc.Graph(
            figure=go.Figure().add_annotation(
                text="No data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
        )
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['TimeAndDateStamp'],
        y=df['actual_fare'],
        mode='lines+markers',
        name='Actual Fare',
        line=dict(color='#2E86C1', width=2),
        marker=dict(size=8)
    ))
    
    fig.add_trace(go.Scatter(
        x=df['TimeAndDateStamp'],
        y=df['price'],
        mode='lines+markers',
        name='Model Price',
        line=dict(color='#F39C12', width=2, dash='dot'),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title='Price Trend: Actual vs Model',
        xaxis_title='Time',
        yaxis_title='Price (₹)',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=40, r=40, t=60, b=40),
        hovermode="x unified"
    )
    
    return dbc.Card(
        [
            dbc.CardHeader(html.H5("Price Trend Analysis")),
            dbc.CardBody(dcc.Graph(figure=fig))
        ],
        className="mb-4"
    )

def create_price_delta_chart(schedule_id=None, operator_id=None, seat_type=None, hours_before_departure=None, date_of_journey=None):
    """Create a chart showing the delta between actual fare and model price"""
    df = get_price_delta_data(schedule_id, operator_id, seat_type, hours_before_departure, date_of_journey)
    
    if df.empty:
        return dcc.Graph(
            figure=go.Figure().add_annotation(
                text="No data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
        )
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=df['TimeAndDateStamp'],
        y=df['delta'],
        name='Price Delta',
        marker_color=['#27AE60' if x >= 0 else '#E74C3C' for x in df['delta']]
    ))
    
    fig.update_layout(
        title='Price Delta (Actual - Model)',
        xaxis_title='Time',
        yaxis_title='Delta (₹)',
        margin=dict(l=40, r=40, t=60, b=40),
        hovermode="x unified"
    )
    
    return dbc.Card(
        [
            dbc.CardHeader(html.H5("Price Delta Analysis")),
            dbc.CardBody(dcc.Graph(figure=fig))
        ],
        className="mb-4"
    )

def create_occupancy_chart(schedule_id=None, operator_id=None, seat_type=None, hours_before_departure=None, date_of_journey=None):
    """Create a chart showing actual vs expected occupancy"""
    df = get_occupancy_data(schedule_id, operator_id, seat_type, hours_before_departure, date_of_journey)
    
    if df.empty:
        return dcc.Graph(
            figure=go.Figure().add_annotation(
                text="No data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
        )
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['TimeAndDateStamp'],
        y=df['actual_occupancy'],
        mode='lines+markers',
        name='Actual Occupancy',
        line=dict(color='#2E86C1', width=2),
        marker=dict(size=8)
    ))
    
    fig.add_trace(go.Scatter(
        x=df['TimeAndDateStamp'],
        y=df['expected_occupancy'],
        mode='lines+markers',
        name='Expected Occupancy',
        line=dict(color='#F39C12', width=2, dash='dot'),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title='Occupancy Trend: Actual vs Expected',
        xaxis_title='Time',
        yaxis_title='Occupancy (%)',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=40, r=40, t=60, b=40),
        hovermode="x unified"
    )
    
    return dbc.Card(
        [
            dbc.CardHeader(html.H5("Occupancy Analysis")),
            dbc.CardBody(dcc.Graph(figure=fig))
        ],
        className="mb-4"
    )

def create_seat_scatter_chart(schedule_id=None, hours_before_departure=None, date_of_journey=None):
    """Create a scatter plot showing seat pricing vs sales percentage"""
    df = get_seat_wise_analysis(schedule_id, hours_before_departure, date_of_journey)
    
    if df.empty:
        return dcc.Graph(
            figure=go.Figure().add_annotation(
                text="No data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
        )
    
    fig = px.scatter(
        df,
        x="final_price",
        y="sales_percentage",
        color="seat_type",
        hover_data=["seat_number", "actual_fare", "delta"],
        title="Seat Price vs Sales Percentage",
        labels={
            "final_price": "Final Price (₹)",
            "sales_percentage": "Sales Percentage (%)",
            "seat_type": "Seat Type"
        }
    )
    
    fig.update_layout(
        margin=dict(l=40, r=40, t=60, b=40),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return dbc.Card(
        [
            dbc.CardHeader(html.H5("Seat-wise Analysis")),
            dbc.CardBody(dcc.Graph(figure=fig))
        ],
        className="mb-4"
    )

def create_seat_wise_price_sum_chart(schedule_id):
    """Create a chart showing sum of actual and model prices for all seats by hours before departure
    
    If there are multiple seat types, create separate graphs for each type
    """
    if not schedule_id:
        return html.Div([
            html.P("Select a schedule ID to view seat-wise price sum chart", className="text-muted text-center")
        ])
    
    try:
        # Get data for the chart
        df = get_seat_wise_price_sum_by_hour(schedule_id)
        
        if df.empty:
            return html.Div([
                html.P(f"No seat-wise price sum data available for schedule ID: {schedule_id}", 
                       className="text-muted text-center")
            ])
        
        # Check if there are multiple seat types
        seat_types = df['seat_type'].unique()
        
        # Create a container for the charts
        charts_container = html.Div([
            html.H5(f"Seat-wise Price Sum by Hours Before Departure", className="text-center mb-3")
        ])
        
        # Create a chart for each seat type
        for seat_type in seat_types:
            seat_type_df = df[df['seat_type'] == seat_type]
            
            fig = go.Figure()
            
            # Sort data by hours_before_departure in descending order (5h, 4h, 3h, etc.)
            seat_type_df = seat_type_df.sort_values('hours_before_departure', ascending=False)
            
            # Add trace for actual price sum
            fig.add_trace(go.Scatter(
                x=seat_type_df['hours_before_departure'],
                y=seat_type_df['total_actual_price'],
                mode='lines+markers',
                name='Actual Price Sum',
                line=dict(color='#2E86C1', width=2),
                marker=dict(size=8),
                hovertemplate='%{x} hours before departure<br>Actual Price Sum: $%{y:.2f}<br>Seat Count: ' + 
                              seat_type_df['seat_count'].astype(str) + '<extra></extra>'
            ))
            
            # Add trace for model price sum
            fig.add_trace(go.Scatter(
                x=seat_type_df['hours_before_departure'],
                y=seat_type_df['total_model_price'],
                mode='lines+markers',
                name='Model Price Sum',
                line=dict(color='#F39C12', width=2, dash='dot'),
                marker=dict(size=8),
                hovertemplate='%{x} hours before departure<br>Model Price Sum: $%{y:.2f}<br>Seat Count: ' + 
                              seat_type_df['seat_count'].astype(str) + '<extra></extra>'
            ))
            
            # Update layout
            fig.update_layout(
                title=f'Seat Type: {seat_type} - Total Price Sum by Hours Before Departure',
                xaxis_title='Hours Before Departure',
                yaxis_title='Price Sum ($)',
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                margin=dict(l=40, r=40, t=60, b=40),
                hovermode="x unified"
            )
            
            # Add the chart to the container
            charts_container.children.append(
                dbc.Card(
                    [
                        dbc.CardHeader(html.H5(f"Total Price Sum - Seat Type: {seat_type}")),
                        dbc.CardBody(dcc.Graph(figure=fig))
                    ],
                    className="mb-4"
                )
            )
        
        return charts_container
    except Exception as e:
        print(f"Error creating seat-wise price sum chart: {str(e)}")
        return html.Div([
            html.P(f"Error creating seat-wise price sum chart: {str(e)}", className="text-danger text-center")
        ])
