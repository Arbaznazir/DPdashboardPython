# Price Sum Analysis Documentation

## Overview

The Price Sum Analysis in the DP-Dashboard provides a visual representation of how the total price sum (both actual and model) changes over time as the departure date approaches. These graphs compare actual price sums with model price sums for each seat type in a selected schedule, helping operators understand pricing trends and revenue potential.

## Data Source

The price sum analysis data is retrieved from the `seat_prices_raw` table in the database, which contains the following key columns:
- `schedule_id`: Unique identifier for a bus schedule
- `hours_before_departure`: Number of hours before the bus departs
- `price`: The actual price at that time
- `price_model`: The model/predicted price at that time
- `seat_type`: The type of seat (e.g., "Salón Cama", "Semi Cama")
- `TimeAndDateStamp`: Timestamp of when the data was recorded

## Data Retrieval Process

The data for the price sum analysis graphs is retrieved using the `get_price_sum_data()` function in `measures.py`. This function:

1. Takes parameters for filtering: `schedule_id`, `operator_id`, `seat_type`, `hours_before_departure`, and `date_of_journey`
2. Executes a SQL query that retrieves price data from the `seat_prices_raw` table using `DISTINCT ON` to get the latest record for each seat type and hours before departure combination
3. Filters the data based on the provided `schedule_id`
4. Ensures that both `price` and `price_model` values are not null
5. Orders by `TimeAndDateStamp` DESC to get the latest record for each combination
6. Converts price values to numeric format and rounds to 2 decimal places
7. Calculates the sum of prices for each seat type and hours before departure

```python
def get_seat_wise_price_sum_by_hour(schedule_id):
    """Get sum of actual and model prices for all seats by hours before departure"""
    # Return empty DataFrame if no schedule_id is provided
    if schedule_id is None:
        return pd.DataFrame()
    
    # Query to get price data with DISTINCT ON to get latest record per seat_type, hours_before_departure, and seat_number
    query = """
    WITH all_hours AS (
        -- Get all distinct hours before departure for this schedule
        SELECT DISTINCT "hours_before_departure"
        FROM seat_prices_raw
        WHERE "schedule_id" = %(schedule_id)s
        ORDER BY "hours_before_departure" DESC
    ),
    all_seat_types AS (
        -- Get all distinct seat types for this schedule
        SELECT DISTINCT "seat_type"
        FROM seat_prices_raw
        WHERE "schedule_id" = %(schedule_id)s
    ),
    latest_snapshots AS (
        -- Get the latest snapshot for each hour before departure and seat type
        SELECT DISTINCT ON (sp."hours_before_departure", sp."seat_type") 
            sp."hours_before_departure", 
            sp."seat_type",
            sp."TimeAndDateStamp"
        FROM seat_prices_raw sp
        WHERE sp."schedule_id" = %(schedule_id)s
        ORDER BY sp."hours_before_departure", sp."seat_type", sp."TimeAndDateStamp" DESC
    ),
    latest_seat_data AS (
        -- Get the latest data for each seat number within each snapshot
        SELECT DISTINCT ON (swp."seat_number", ls."hours_before_departure", ls."seat_type")
            ls."hours_before_departure",
            ls."seat_type",
            swp."seat_number",
            CAST(swp."actual_fare" AS NUMERIC) as "actual_fare",
            CAST(swp."final_price" AS NUMERIC) as "final_price"
        FROM latest_snapshots ls
        JOIN seat_wise_prices_raw swp 
            ON swp."TimeAndDateStamp" = ls."TimeAndDateStamp" 
            AND swp."seat_type" = ls."seat_type"
            AND swp."schedule_id" = %(schedule_id)s
        ORDER BY 
            swp."seat_number", ls."hours_before_departure", ls."seat_type", swp."TimeAndDateStamp" DESC
    )
    SELECT 
        "hours_before_departure",
        "seat_type",
        SUM("actual_fare") as "total_actual_price",
        SUM("final_price") as "total_model_price",
        COUNT(DISTINCT "seat_number") as "seat_count"
    FROM latest_seat_data
    GROUP BY "hours_before_departure", "seat_type"
    ORDER BY "hours_before_departure" DESC
    """
    
    params = {'schedule_id': schedule_id}
    df = execute_query(query, params)
    
    # Return empty DataFrame if no data was found
    if df is None or df.empty:
        return pd.DataFrame()
    
    # Convert price values to numeric and round to 2 decimal places
    df['price_sum'] = pd.to_numeric(df['price_sum'], errors='coerce').round(2)
    df['model_price_sum'] = pd.to_numeric(df['model_price_sum'], errors='coerce').round(2)
    
    # Drop any rows with NaN values after conversion
    df = df.dropna(subset=['price_sum', 'model_price_sum'])
    
    # Sort by seat_type and hours_before_departure in descending order (highest to lowest)
    df = df.sort_values(['seat_type', 'hours_before_departure'], ascending=[True, False])
    
    return df
```

## Graph Creation

The price sum analysis graphs are created in the `create_price_sum_chart()` function in `graphs.py`. This function:

1. Takes the same parameters as `get_price_sum_data()`
2. Calls `get_price_sum_data()` to retrieve the price sum data
3. Creates either a single chart (if there's only one seat type) or multiple charts (one for each seat type)
4. Uses Plotly's `go.Figure()` and `go.Scatter()` to create the graphs
5. Applies styling and layout settings for a consistent look and feel

### Single Seat Type Case

When there's only one seat type, the function creates a single chart that shows:
- Actual price sum as a blue line with markers
- Model price sum as an orange dotted line with markers
- The chart is displayed at full width

```python
# If there's only one seat type, create a single chart
if len(seat_types) == 1:
    # Filter data for this seat type
    seat_df = df[df['seat_type'] == seat_types[0]].sort_values('hours_before_departure', ascending=False)
    
    # Create figure
    fig = go.Figure()
    
    # Add traces for actual and model price sums
    fig.add_trace(go.Scatter(
        x=seat_df['hours_before_departure'],
        y=seat_df['price_sum'],
        mode='lines+markers',
        name='Actual Price Sum',
        line=dict(color='#1d8cf8', width=3, shape='linear'),  # Blue color, linear line
        marker=dict(size=8, color='#1d8cf8', line=dict(width=2, color='#ffffff'))
    ))
    
    fig.add_trace(go.Scatter(
        x=seat_df['hours_before_departure'],
        y=seat_df['model_price_sum'],
        mode='lines+markers',
        name='Model Price Sum',
        line=dict(color='#ff9f43', width=3, shape='linear', dash='dot'),  # Orange color, dotted line
        marker=dict(size=8, color='#ff9f43', line=dict(width=2, color='#ffffff'))
    ))
    
    # Update layout
    fig.update_layout(
        title=f"Price Sum Analysis for {seat_types[0]}",
        **common_layout
    )
    
    # Add the chart to the container - full width for single seat type
    container.children[1].children = dcc.Graph(figure=fig)
```

### Multiple Seat Types Case

When there are multiple seat types, the function creates a separate chart for each seat type:
- Each chart shows actual and model price sums for a specific seat type
- Different colors are used for different seat types (from predefined color palettes)
- The charts are arranged in a grid with two charts per row
- A scrollable container is used if there are many charts

```python
# If there are multiple seat types, create a chart for each
else:
    charts = []
    
    # Define colors for different seat types
    actual_colors = ['#1d8cf8', '#00f2c3', '#fd5d93', '#ff9f43']
    model_colors = ['#3358f4', '#46c37b', '#ec250d', '#f5a623']
    
    for i, st in enumerate(seat_types):
        # Filter data for this seat type
        seat_df = df[df['seat_type'] == st].sort_values('hours_before_departure', ascending=False)
        
        # Create figure
        fig = go.Figure()
        
        # Use different colors for different seat types
        color_idx = i % len(actual_colors)
        
        # Add traces for actual and model price sums
        fig.add_trace(go.Scatter(
            x=seat_df['hours_before_departure'],
            y=seat_df['price_sum'],
            mode='lines+markers',
            name='Actual Price Sum',
            line=dict(color=actual_colors[color_idx], width=3, shape='linear'),
            marker=dict(size=8, color=actual_colors[color_idx], line=dict(width=2, color='#ffffff'))
        ))
        
        fig.add_trace(go.Scatter(
            x=seat_df['hours_before_departure'],
            y=seat_df['model_price_sum'],
            mode='lines+markers',
            name='Model Price Sum',
            line=dict(color=model_colors[color_idx], width=3, shape='linear', dash='dot'),
            marker=dict(size=8, color=model_colors[color_idx], line=dict(width=2, color='#ffffff'))
        ))
        
        # Update layout
        fig.update_layout(
            title=f'Price Sum Analysis for {st}',
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
```

## Graph Styling

The price sum analysis graphs use a consistent styling defined in the `common_layout` dictionary:
- Dark background colors (`#27293d` for both paper and plot)
- White font for text and labels
- Horizontal legend at the top right
- Custom margins and height
- Unified hover mode
- Custom styling for axes, including titles, colors, and grid lines

```python
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
        title=dict(text="Price Sum", font=dict(size=14, color="#eee")),
        color="#eee",
        gridcolor="rgba(255, 255, 255, 0.1)",
        zerolinecolor="rgba(255, 255, 255, 0.2)"
    )
)
```

## Integration with Dashboard

The price sum analysis graphs are integrated into the dashboard through callbacks in `main.py`. The graphs are updated whenever:
- A new schedule ID is selected
- The hours before departure value changes
- The date of journey changes

## User Interaction

Users can interact with the price sum analysis graphs in several ways:
1. **Hover**: Hovering over data points shows the exact price sum values
2. **Zoom**: Users can zoom in on specific parts of the graph
3. **Pan**: Users can pan across the graph to view different time periods
4. **Download**: Users can download the graph as a PNG image using Plotly's built-in tools
5. **Compare**: Users can visually compare actual vs model price sums

## Business Value

The price sum analysis graphs provide valuable insights for bus operators:
1. **Revenue Tracking**: Compare actual revenue against model/expected revenue
2. **Pricing Strategy Analysis**: Identify patterns in how prices change as departure time approaches
3. **Seat Type Comparison**: Compare price trends across different seat types
4. **Decision Support**: Help operators make informed decisions about pricing and revenue management
5. **Performance Evaluation**: Evaluate the effectiveness of dynamic pricing models

## Technical Implementation Details

1. **Data Flow**:
   - User selects a schedule ID and other parameters
   - Dashboard calls `get_price_sum_data()` to retrieve data
   - `create_price_sum_chart()` processes the data and creates the graphs
   - Graphs are rendered in the dashboard UI

2. **Performance Considerations**:
   - Data is filtered using DISTINCT ON to get latest records
   - Charts are created dynamically based on the number of seat types
   - Scrollable container prevents UI clutter with multiple charts

3. **Error Handling**:
   - Shows a placeholder message if no schedule ID is selected
   - Shows a different placeholder if no data is available for the selected schedule
   - Handles missing or null values by filtering them out

## Future Enhancements

Potential improvements for the price sum analysis:
1. Add trend lines or moving averages to smooth out fluctuations
2. Implement date range filtering to compare price sums across different dates
3. Add benchmarking against historical averages or similar routes
4. Incorporate predictive analytics to forecast future price trends
5. Add interactive elements to drill down into specific time periods or seat types
6. Implement cumulative revenue tracking over time
