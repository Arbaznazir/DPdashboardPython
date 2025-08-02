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
    """Create a chart showing actual vs expected occupancy, with separate charts for each seat type"""
    # Only proceed if we have a schedule_id
    if schedule_id is None:
        return html.Div([
            # Section heading
            html.H4("Occupancy Analysis", className="text-white mb-4"),
            
            # Placeholder message
            dcc.Graph(
                figure=go.Figure().add_annotation(
                    text="Please select a Schedule ID",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=18, color="#5e72e4")
                ).update_layout(
                    paper_bgcolor='#27293d',
                    plot_bgcolor='#27293d',
                    font=dict(color="white")
                )
            )
        ])
    
    # Get occupancy data for all hours and seat types
    df = get_occupancy_data(schedule_id, operator_id, seat_type, hours_before_departure, date_of_journey)
    
    if df is None or df.empty:
        return html.Div([
            # Section heading
            html.H4("Occupancy Analysis", className="text-white mb-4"),
            
            # Placeholder message
            dcc.Graph(
                figure=go.Figure().add_annotation(
                    text="No occupancy data available for this schedule",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=18, color="#5e72e4")
                ).update_layout(
                    paper_bgcolor='#27293d',
                    plot_bgcolor='#27293d',
                    font=dict(color="white")
                )
            )
        ])
    
    # Convert hours_before_departure to numeric for proper sorting
    df['hours_before_departure'] = pd.to_numeric(df['hours_before_departure'], errors='coerce')
    
    # Get unique seat types
    seat_types = df['seat_type'].unique()
    
    # Common layout settings
    common_layout = dict(
        paper_bgcolor='#27293d',
        plot_bgcolor='#27293d',
        font=dict(family="Poppins, sans-serif", size=12, color="white"),
        title_font=dict(family="Poppins, sans-serif", size=20, color="white"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(family="Poppins, sans-serif", size=12, color="white"),
            bgcolor="rgba(39, 41, 61, 0.5)"
        ),
        margin=dict(l=50, r=50, t=80, b=50),
        height=400,
        hovermode="x unified",
        xaxis=dict(
            title=dict(text="Hours Before Departure", font=dict(size=14, color="#eee")),
            color="#eee",
            gridcolor="rgba(255, 255, 255, 0.1)",
            zerolinecolor="rgba(255, 255, 255, 0.2)"
        ),
        yaxis=dict(
            title=dict(text="Occupancy (%)", font=dict(size=14, color="#eee")),
            color="#eee",
            gridcolor="rgba(255, 255, 255, 0.1)",
            zerolinecolor="rgba(255, 255, 255, 0.2)"
        )
    )
    
    # Create a container with heading
    container = html.Div([
        # Section heading
        html.H4("Occupancy Analysis", className="text-white mb-4"),
        
        # Container for charts
        html.Div(id="occupancy-charts-container")
    ])
    
    # If there's only one seat type, create a single chart
    if len(seat_types) == 1:
        # Filter data for this seat type
        seat_df = df[df['seat_type'] == seat_types[0]].sort_values('hours_before_departure', ascending=False)
        
        # Create figure
        fig = go.Figure()
        
        # Add traces for actual and expected occupancy
        fig.add_trace(go.Scatter(
            x=seat_df['hours_before_departure'],
            y=seat_df['actual_occupancy'],
            mode='lines+markers',
            name='Actual Occupancy',
            line=dict(color='#1d8cf8', width=3, shape='spline', smoothing=1.3),  # Blue color, smooth curve
            marker=dict(size=8, color='#1d8cf8', line=dict(width=2, color='#ffffff'))
        ))
        
        fig.add_trace(go.Scatter(
            x=seat_df['hours_before_departure'],
            y=seat_df['expected_occupancy'],
            mode='lines+markers',
            name='Expected Occupancy',
            line=dict(color='#ff9f43', width=3, shape='spline', smoothing=1.3, dash='dot'),  # Orange color, smooth curve, dotted
            marker=dict(size=8, color='#ff9f43', line=dict(width=2, color='#ffffff'))
        ))
        
        # Update layout
        fig.update_layout(
            title=f"Occupancy Trend for {seat_types[0]}",
            **common_layout
        )
        
        # Add the chart to the container - full width for single seat type
        container.children[1].children = dcc.Graph(figure=fig)
    
    # If there are multiple seat types, create a chart for each
    else:
        charts = []
        
        # Define colors for different seat types
        actual_colors = ['#1d8cf8', '#00f2c3', '#fd5d93', '#ff9f43']
        expected_colors = ['#3358f4', '#46c37b', '#ec250d', '#f5a623']
        
        for i, st in enumerate(seat_types):
            # Filter data for this seat type
            seat_df = df[df['seat_type'] == st].sort_values('hours_before_departure', ascending=False)
            
            # Create figure
            fig = go.Figure()
            
            # Use different colors for different seat types
            color_idx = i % len(actual_colors)
            
            # Add traces for actual and expected occupancy
            fig.add_trace(go.Scatter(
                x=seat_df['hours_before_departure'],
                y=seat_df['actual_occupancy'],
                mode='lines+markers',
                name='Actual Occupancy',
                line=dict(color=actual_colors[color_idx], width=3, shape='spline', smoothing=1.3),
                marker=dict(size=8, color=actual_colors[color_idx], line=dict(width=2, color='#ffffff'))
            ))
            
            fig.add_trace(go.Scatter(
                x=seat_df['hours_before_departure'],
                y=seat_df['expected_occupancy'],
                mode='lines+markers',
                name='Expected Occupancy',
                line=dict(color=expected_colors[color_idx], width=3, shape='spline', smoothing=1.3, dash='dot'),
                marker=dict(size=8, color=expected_colors[color_idx], line=dict(width=2, color='#ffffff'))
            ))
            
            # Update layout
            fig.update_layout(
                title=f'Occupancy Trend for {st}',
                **common_layout
            )
            
            # Ensure x-axis is properly formatted
            fig.update_xaxes(
                type='category',  # Use category type for discrete values
                categoryorder='array',  # Order by the array we provide
                categoryarray=sorted(seat_df['hours_before_departure'].unique(), reverse=True)  # Sort from highest to lowest
            )
            
            # Add the chart to the list
            charts.append(
                dbc.Col(
                    dcc.Graph(figure=fig),
                    width=6,  # Two charts per row
                    className="mb-4"
                )
            )
        
        # Add the charts to the container in a scrollable row
        container.children[1].children = html.Div(
            dbc.Row(charts),
            style={
                'overflowX': 'auto',  # Enable horizontal scrolling
                'paddingBottom': '15px'  # Space for scrollbar
            }
        )
    
    return container

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
            # Section heading
            html.H4("Price Sum Analysis", className="text-white mb-4"),
            
            # Placeholder message
            html.Div([
                html.I(className="fas fa-chart-line fa-3x text-info mb-3"),
                html.H5("Select a schedule ID to view seat-wise price sum chart", className="text-white")
            ], className="text-center p-5 bg-dark rounded shadow-sm")
        ])
    
    try:
        # Get data for the chart
        df = get_seat_wise_price_sum_by_hour(schedule_id)
        
        if df.empty:
            return html.Div([
                # Section heading
                html.H4("Price Sum Analysis", className="text-white mb-4"),
                
                # Placeholder message
                html.Div([
                    html.I(className="fas fa-exclamation-triangle fa-3x text-warning mb-3"),
                    html.H5(f"No seat-wise price sum data available for schedule ID: {schedule_id}", 
                           className="text-white")
                ], className="text-center p-5 bg-dark rounded shadow-sm")
            ])
        
        # Check if there are multiple seat types
        seat_types = df['seat_type'].unique()
        
        # Common layout settings
        common_layout = dict(
            paper_bgcolor='#27293d',
            plot_bgcolor='#27293d',
            font=dict(family="Poppins, sans-serif", size=12, color="white"),
            title_font=dict(family="Poppins, sans-serif", size=20, color="white"),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(family="Poppins, sans-serif", size=12, color="white"),
                bgcolor="rgba(39, 41, 61, 0.5)"
            ),
            margin=dict(l=50, r=50, t=80, b=50),
            height=400,
            hovermode="x unified",
            xaxis=dict(
                title=dict(text="Hours Before Departure", font=dict(size=14, color="#eee")),
                color="#eee",
                gridcolor="rgba(255, 255, 255, 0.1)",
                zerolinecolor="rgba(255, 255, 255, 0.2)"
            ),
            yaxis=dict(
                title=dict(text="Price Sum ($)", font=dict(size=14, color="#eee")),
                color="#eee",
                gridcolor="rgba(255, 255, 255, 0.1)",
                zerolinecolor="rgba(255, 255, 255, 0.2)"
            )
        )
        
        # Create a container with heading
        container = html.Div([
            # Section heading
            html.H4("Price Sum Analysis", className="text-white mb-4"),
            
            # Container for charts
            html.Div(id="price-sum-charts-container")
        ])
        
        # Create a container for the charts
        charts = []
        
        # Enhanced color palette for better visual distinction
        # Vibrant colors for actual price lines
        actual_colors = [
            '#4facfe',  # Bright blue
            '#00f2c3',  # Teal
            '#f868e6',  # Magenta
            '#ffcb57',  # Gold
            '#43e97b',  # Green
            '#a166ff'   # Purple
        ]
        
        # Subtle fill colors for actual price areas
        actual_fill_colors = [
            'rgba(79, 172, 254, 0.1)',  # Blue fill
            'rgba(0, 242, 195, 0.1)',   # Teal fill
            'rgba(248, 104, 230, 0.1)', # Magenta fill
            'rgba(255, 203, 87, 0.1)',  # Gold fill
            'rgba(67, 233, 123, 0.1)',  # Green fill
            'rgba(161, 102, 255, 0.1)'  # Purple fill
        ]
        
        # Complementary colors for model price lines
        model_colors = [
            '#ff5e62',  # Coral red
            '#ff9f43',  # Orange
            '#5e60ce',  # Indigo
            '#0072ff',  # Royal blue
            '#fd5d93',  # Pink
            '#17c0eb'   # Sky blue
        ]
        
        # Subtle fill colors for model price areas
        model_fill_colors = [
            'rgba(255, 94, 98, 0.1)',   # Coral fill
            'rgba(255, 159, 67, 0.1)',  # Orange fill
            'rgba(94, 96, 206, 0.1)',   # Indigo fill
            'rgba(0, 114, 255, 0.1)',   # Royal blue fill
            'rgba(253, 93, 147, 0.1)',  # Pink fill
            'rgba(23, 192, 235, 0.1)'   # Sky blue fill
        ]
        
        # If there's only one seat type, create a single chart
        if len(seat_types) == 1:
            seat_type = seat_types[0]
            seat_type_df = df[df['seat_type'] == seat_type]
            
            # Sort data by hours_before_departure in descending order (5h, 4h, 3h, etc.)
            seat_type_df = seat_type_df.sort_values('hours_before_departure', ascending=False)
            
            # Create figure
            fig = go.Figure()
            
            # Add trace for actual price sum
            fig.add_trace(go.Scatter(
                x=seat_type_df['hours_before_departure'],
                y=seat_type_df['total_actual_price'],
                mode='lines+markers',
                name='Actual Price Sum',
                line=dict(color=actual_colors[0], width=3, shape='spline', smoothing=1.3),
                marker=dict(size=8, color=actual_colors[0], line=dict(width=2, color='#ffffff')),
                fill='tozeroy',
                fillcolor=actual_fill_colors[0]
            ))
            
            # Add trace for model price sum
            fig.add_trace(go.Scatter(
                x=seat_type_df['hours_before_departure'],
                y=seat_type_df['total_model_price'],
                name="Model Price Sum",
                line=dict(color=model_colors[0], width=3, shape='spline', smoothing=1.3),
                mode='lines+markers',
                marker=dict(size=8, color=model_colors[0], line=dict(width=2, color=model_colors[0])),
                fill='tozeroy',
                fillcolor=model_fill_colors[0]
            ))
            
            # Update layout
            fig.update_layout(
                title=f"Price Sum Analysis for {seat_type}",
                **common_layout
            )
            
            # Ensure x-axis is properly formatted
            fig.update_xaxes(
                type='category',  # Use category type for discrete values
                categoryorder='array',  # Order by the array we provide
                categoryarray=sorted(seat_type_df['hours_before_departure'].unique(), reverse=True)  # Sort from highest to lowest
            )
            
            # Add the chart to the container - full width for single seat type
            container.children[1].children = dcc.Graph(figure=fig)
        
        # If there are multiple seat types, create a chart for each
        else:
            # Create a chart for each seat type
            for i, seat_type in enumerate(seat_types):
                seat_type_df = df[df['seat_type'] == seat_type]
                
                # Sort data by hours_before_departure in descending order (5h, 4h, 3h, etc.)
                seat_type_df = seat_type_df.sort_values('hours_before_departure', ascending=False)
                
                # Create figure
                fig = go.Figure()
                
                color_idx = i % len(actual_colors)
                
                # Add trace for actual price sum
                fig.add_trace(go.Scatter(
                    x=seat_type_df['hours_before_departure'],
                    y=seat_type_df['total_actual_price'],
                    mode='lines+markers',
                    name='Actual Price Sum',
                    line=dict(color=actual_colors[color_idx], width=3, shape='spline', smoothing=1.3),
                    marker=dict(size=8, color=actual_colors[color_idx], line=dict(width=2, color='#ffffff')),
                    fill='tozeroy',
                    fillcolor=actual_fill_colors[color_idx]
                ))
                
                # Add trace for model price sum
                fig.add_trace(go.Scatter(
                    x=seat_type_df['hours_before_departure'],
                    y=seat_type_df['total_model_price'],
                    name="Model Price Sum",
                    line=dict(color=model_colors[color_idx], width=3, shape='spline', smoothing=1.3),
                    mode='lines+markers',
                    marker=dict(size=8, color=model_colors[color_idx], line=dict(width=2, color=model_colors[color_idx])),
                    fill='tozeroy',
                    fillcolor=model_fill_colors[color_idx]
                ))
                
                # Update layout
                fig.update_layout(
                    title=f"Price Sum Analysis for {seat_type}",
                    **common_layout
                )
                
                # Ensure x-axis is properly formatted
                fig.update_xaxes(
                    type='category',  # Use category type for discrete values
                    categoryorder='array',  # Order by the array we provide
                    categoryarray=sorted(seat_type_df['hours_before_departure'].unique(), reverse=True)  # Sort from highest to lowest
                )
                
                # Add the chart to the list
                charts.append(
                    dbc.Col(
                        dcc.Graph(figure=fig),
                        width=6,  # Two charts per row
                        className="mb-4"
                    )
                )
            
            # Add the charts to the container in a scrollable row
            container.children[1].children = html.Div(
                dbc.Row(charts),
                style={
                    'overflowX': 'auto',  # Enable horizontal scrolling
                    'paddingBottom': '15px'  # Space for scrollbar
                }
            )
        
        return container
    except Exception as e:
        print(f"Error creating seat-wise price sum chart: {str(e)}")
        return html.Div([
            dbc.Card([
                dbc.CardBody([
                    html.I(className="fas fa-exclamation-circle fa-3x text-danger mb-3"),
                    html.H5(f"Error creating seat-wise price sum chart", className="text-white mb-3"),
                    html.Pre(str(e), className="bg-dark text-danger p-3 rounded")
                ], className="text-center")
            ], className="mb-4 shadow bg-dark")
        ])
