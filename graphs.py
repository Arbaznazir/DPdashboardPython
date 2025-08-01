import plotly.express as px
import plotly.graph_objects as go
from dash import dcc
import dash_bootstrap_components as dbc
from dash import html
import pandas as pd
from measures import get_price_trend_data, get_occupancy_data, get_seat_wise_analysis

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
