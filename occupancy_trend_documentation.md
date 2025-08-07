# Occupancy Trend Graphs Documentation

## Overview

The occupancy trend graphs in the DP-Dashboard provide a visual representation of how seat occupancy changes over time as the departure date approaches. These graphs compare actual occupancy percentages with expected occupancy percentages for each seat type in a selected schedule.

## Data Source

The occupancy trend data is retrieved from the `seat_prices_raw` table in the database, which contains the following key columns:
- `schedule_id`: Unique identifier for a bus schedule
- `hours_before_departure`: Number of hours before the bus departs
- `actual_occupancy`: The actual percentage of seats occupied at that time
- `expected_occupancy`: The expected/predicted percentage of seats that should be occupied at that time
- `seat_type`: The type of seat (e.g., "Salón Cama", "Semi Cama")

## Data Retrieval Process

The data for the occupancy trend graphs is retrieved using the `get_occupancy_data()` function in `measures.py`. This function:

1. Takes parameters for filtering: `schedule_id`, `operator_id`, `seat_type`, `hours_before_departure`, and `date_of_journey`
2. Executes a SQL query that retrieves occupancy data from the `seat_prices_raw` table using `DISTINCT ON` to get the latest record for each seat type and hours before departure combination
3. Filters the data based on the provided `schedule_id`
4. Ensures that both `actual_occupancy` and `expected_occupancy` values are not null
5. Orders by `TimeAndDateStamp` DESC to get the latest record for each combination
6. Converts occupancy values to numeric format and rounds to 2 decimal places
7. Sorts the data by `seat_type` and `hours_before_departure` (in descending order)

```python
def get_occupancy_data(schedule_id=None, operator_id=None, seat_type=None, hours_before_departure=None, date_of_journey=None):
    """Get occupancy data for charts - simplified version that directly gets data from seat_prices_raw"""
    # Return empty DataFrame if no schedule_id is provided
    if schedule_id is None:
        return pd.DataFrame()
    
    # Query to get occupancy data with DISTINCT ON to get latest record per seat_type and hours_before_departure
    query = """
    WITH latest_snapshots AS (
        SELECT DISTINCT ON ("seat_type", "hours_before_departure") 
            "schedule_id",
            "hours_before_departure",
            "actual_occupancy"::NUMERIC(10,2) as "actual_occupancy",
            "expected_occupancy"::NUMERIC(10,2) as "expected_occupancy",
            "seat_type",
            "TimeAndDateStamp"
        FROM 
            seat_prices_raw
        WHERE 
            "schedule_id" = %(schedule_id)s
            AND "actual_occupancy" IS NOT NULL
            AND "expected_occupancy" IS NOT NULL
        ORDER BY 
            "seat_type", "hours_before_departure", "TimeAndDateStamp" DESC
    )
    SELECT * FROM latest_snapshots
    ORDER BY "seat_type", "hours_before_departure" DESC
    """
    
    params = {'schedule_id': schedule_id}
    df = execute_query(query, params)
    
    # Return empty DataFrame if no data was found
    if df is None or df.empty:
        return pd.DataFrame()
    
    # Convert occupancy values to numeric and round to 2 decimal places
    df['actual_occupancy'] = pd.to_numeric(df['actual_occupancy'], errors='coerce').round(2)
    df['expected_occupancy'] = pd.to_numeric(df['expected_occupancy'], errors='coerce').round(2)
    
    # Drop any rows with NaN values after conversion
    df = df.dropna(subset=['actual_occupancy', 'expected_occupancy'])
    
    # Sort by seat_type and hours_before_departure in descending order (highest to lowest)
    df = df.sort_values(['seat_type', 'hours_before_departure'], ascending=[True, False])
    
    return df
```

## Graph Creation

The occupancy trend graphs are created in the `create_occupancy_chart()` function in `graphs.py`. This function:

1. Takes the same parameters as `get_occupancy_data()`
2. Calls `get_occupancy_data()` to retrieve the occupancy data
3. Creates either a single chart (if there's only one seat type) or multiple charts (one for each seat type)
4. Uses Plotly's `go.Figure()` and `go.Scatter()` to create the graphs
5. Applies styling and layout settings for a consistent look and feel

### Single Seat Type Case

When there's only one seat type, the function creates a single chart that shows:
- Actual occupancy as a blue line with markers
- Expected occupancy as an orange dotted line with markers
- The chart is displayed at full width

```python
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
        line=dict(color='#1d8cf8', width=4),  # Line is slightly thicker
        marker=dict(size=6, color='rgba(29, 140, 248, 0.6)', line=dict(width=1.5, color='#1d8cf8'))  # Transparent blue
    ))
    
    fig.add_trace(go.Scatter(
        x=seat_df['hours_before_departure'],
        y=seat_df['expected_occupancy'],
        mode='lines+markers',
        name='Expected Occupancy',
        line=dict(color='#ff9f43', width=4, dash='dot'),  # Orange color, dotted line
        marker=dict(size=6, color='rgba(255, 159, 67, 0.6)', line=dict(width=1.5, color='#ff9f43'))  # Transparent orange
    ))
    
    # Update layout
    fig.update_layout(
        title=f"Occupancy Trend for {seat_types[0]}",
        **common_layout
    )
    
    # Add the chart to the container - full width for single seat type
    container.children[1].children = dcc.Graph(figure=fig)
```

### Multiple Seat Types Case

When there are multiple seat types, the function creates a separate chart for each seat type:
- Each chart shows actual and expected occupancy for a specific seat type
- Different colors are used for different seat types (from predefined color palettes)
- The charts are arranged in a grid with two charts per row
- A scrollable container is used if there are many charts

```python
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
            line=dict(color=actual_colors[color_idx], width=4),
            marker=dict(size=6, color=f'rgba{hex_to_rgba(actual_colors[color_idx], 0.6)}',
                    line=dict(width=1.5, color=actual_colors[color_idx]))
        ))
        
        fig.add_trace(go.Scatter(
            x=seat_df['hours_before_departure'],
            y=seat_df['expected_occupancy'],
            mode='lines+markers',
            name='Expected Occupancy',
            line=dict(color=expected_colors[color_idx], width=4, dash='dot'),
            marker=dict(size=6, color=f'rgba{hex_to_rgba(expected_colors[color_idx], 0.6)}',
                    line=dict(width=1.5, color=expected_colors[color_idx]))
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
```

## Graph Styling

The occupancy trend graphs use a consistent styling defined in the `common_layout` dictionary:
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
        title=dict(text="Occupancy (%)", font=dict(size=14, color="#eee")),
        color="#eee",
        gridcolor="rgba(255, 255, 255, 0.1)",
        zerolinecolor="rgba(255, 255, 255, 0.2)"
    )
)
```

## Integration with Dashboard

The occupancy trend graphs are integrated into the dashboard through callbacks in `main.py`. The graphs are updated whenever:
- A new schedule ID is selected
- The hours before departure value changes
- The date of journey changes

## User Interaction

Users can interact with the occupancy trend graphs in several ways:
1. **Hover**: Hovering over data points shows the exact occupancy values
2. **Zoom**: Users can zoom in on specific parts of the graph
3. **Pan**: Users can pan across the graph to view different time periods
4. **Download**: Users can download the graph as a PNG image using Plotly's built-in tools
5. **Compare**: Users can visually compare actual vs expected occupancy trends

## Business Value

The occupancy trend graphs provide valuable insights for bus operators:
1. **Performance Tracking**: Compare actual occupancy against expected occupancy
2. **Trend Analysis**: Identify patterns in how seats fill up as departure time approaches
3. **Seat Type Comparison**: Compare occupancy trends across different seat types
4. **Decision Support**: Help operators make informed decisions about pricing and capacity

## Technical Implementation Details

1. **Data Flow**:
   - User selects a schedule ID and other parameters
   - Dashboard calls `get_occupancy_data()` to retrieve data
   - `create_occupancy_chart()` processes the data and creates the graphs
   - Graphs are rendered in the dashboard UI

2. **Performance Considerations**:
   - Data is grouped and aggregated to reduce redundancy
   - Charts are created dynamically based on the number of seat types
   - Scrollable container prevents UI clutter with multiple charts

3. **Error Handling**:
   - Shows a placeholder message if no schedule ID is selected
   - Shows a different placeholder if no data is available for the selected schedule
   - Handles missing or null values by filtering them out

## Future Enhancements

Potential improvements for the occupancy trend graphs:
1. Add trend lines or moving averages to smooth out fluctuations
2. Implement date range filtering to compare occupancy across different dates
3. Add benchmarking against historical averages or similar routes
4. Incorporate predictive analytics to forecast future occupancy
5. Add interactive elements to drill down into specific time periods
