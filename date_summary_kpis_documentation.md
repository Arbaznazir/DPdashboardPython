# Date Summary KPIs Documentation

## Overview

The Date Summary KPIs feature in the DP-Dashboard provides a comprehensive view of pricing data for a selected past date. This feature displays six KPI cards organized in two rows, showing the total historic prices, model prices, and their delta (difference) at both the schedule level and seat level.

## Key Features

- Only appears when a past date is selected (not for current or future dates)
- Shows aggregated pricing data across all schedule IDs for the selected date
- Displays both schedule-level and seat-level pricing information
- Uses color-coding to indicate whether price differences are favorable or unfavorable

## Data Source and Retrieval

The Date Summary KPIs retrieve data from two main tables:
1. `seat_prices_raw` - For schedule-level pricing information
2. `seat_wise_prices_raw` - For individual seat-level pricing information

### Data Retrieval Process

1. When a past date is selected, the system retrieves all schedule IDs operating on that date
2. For each schedule ID, it gets the latest pricing snapshot for each seat type and seat number
3. The system uses `DISTINCT ON` with proper ordering by `TimeAndDateStamp DESC` to ensure only the latest records are used
4. It then calculates the sum of actual prices, model prices, and their delta

```python
# Example query for schedule-level prices (simplified)
WITH latest_snapshots AS (
    SELECT DISTINCT ON (sp.schedule_id, sp.seat_type) 
        sp.schedule_id, 
        sp.seat_type,
        sp."TimeAndDateStamp"
    FROM seat_prices_raw sp
    WHERE sp.schedule_id IN %(schedule_ids)s
    AND doj.date_of_journey = %(date_of_journey)s
    ORDER BY sp.schedule_id, sp.seat_type, sp."TimeAndDateStamp" DESC
)
SELECT 
    sp.schedule_id,
    sp.seat_type,
    CAST(sp.actual_fare AS NUMERIC) as actual_price,
    CAST(sp.price AS NUMERIC) as model_price
FROM seat_prices_raw sp
JOIN latest_snapshots ls ON 
    sp.schedule_id = ls.schedule_id AND 
    sp.seat_type = ls.seat_type AND 
    sp."TimeAndDateStamp" = ls."TimeAndDateStamp"
```

## KPI Card Creation

The system creates six KPI cards:

### Schedule Level (First Row)
1. **Total Historic Price (Schedule)** - Sum of all actual prices across all schedules
2. **Total Model Price (Schedule)** - Sum of all model prices across all schedules
3. **Total Price Delta (Schedule)** - Difference between historic and model prices

### Seat Level (Second Row)
4. **Total Historic Price (Seat)** - Sum of all actual prices across all individual seats
5. **Total Model Price (Seat)** - Sum of all model prices across all individual seats
6. **Total Price Delta (Seat)** - Difference between historic and model seat prices

## Price Delta Calculation and Color Logic

The price delta is calculated as:
```
delta = actual_price - model_price
```

### Business Logic for Color Coding

The color of the price delta KPI cards follows this business logic:

- **Red (Danger)** - When actual price > model price (positive delta)
  - This indicates the company is charging more than the model recommends
  - Considered unfavorable from a business perspective (potential loss of customers due to overpricing)

- **Green (Success)** - When actual price < model price (negative delta)
  - This indicates the company is charging less than the model recommends
  - Considered favorable from a business perspective (competitive pricing)

- **Light/Neutral** - When there's no difference between actual and model prices

```python
# Color determination logic
delta_color = "danger" if delta > 0 else "success" if delta < 0 else "light"
```

## Implementation Details

The Date Summary KPIs are implemented in two main files:

1. `db_utils_summary.py` - Contains the `get_price_summary_by_date()` function that:
   - Retrieves schedule IDs for the selected date
   - Executes SQL queries to get the latest price data
   - Calculates sums and deltas for both schedule and seat level prices

2. `date_summary_kpis.py` - Contains the `create_date_summary_kpis()` function that:
   - Checks if the selected date is in the past
   - Gets price summary data from `get_price_summary_by_date()`
   - Creates KPI cards with appropriate colors based on delta values
   - Arranges the cards in a responsive layout

## User Interaction

1. User selects a past date from the date picker
2. The system checks if the date is in the past
3. If it's a past date, the system retrieves price data for all schedules on that date
4. The Date Summary KPIs section appears, showing the six KPI cards
5. The user can see at a glance the total historic prices, model prices, and their deltas

## Business Value

The Date Summary KPIs provide valuable insights for business analysts and decision-makers:

- **Performance Assessment** - Quickly see how actual pricing compared to model recommendations
- **Revenue Analysis** - Understand the total revenue generated on a specific date
- **Pricing Strategy Evaluation** - Evaluate if pricing strategies were effective
- **Cross-Date Comparison** - By selecting different dates, users can compare performance across time

## Technical Notes

- The feature only appears for past dates to ensure complete data is available
- All calculations use the latest available pricing data to avoid duplicates
- The system handles both single and multiple schedule IDs correctly
- Proper error handling ensures the dashboard remains functional even if data is missing

## Future Enhancements

Potential improvements to the Date Summary KPIs feature could include:

- Adding trend indicators to show how the current date compares to previous periods
- Incorporating occupancy data to provide context for pricing decisions
- Adding drill-down capabilities to see details for specific schedule IDs or seat types
- Implementing date range selection to view aggregated data over multiple days
