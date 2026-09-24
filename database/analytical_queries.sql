-- =====================================================
-- QUERY 1
-- TOP 10 HOTELS BY REVENUE
-- =====================================================

SELECT
    hotel_name,
    COUNT(*) AS total_bookings,
    SUM(price) AS total_revenue
FROM hotel_bookings
WHERE status IN ('Confirmed', 'Completed')
GROUP BY hotel_name
ORDER BY total_revenue DESC
LIMIT 10;


-- =====================================================
-- QUERY 2
-- MONTHLY REVENUE GROWTH
-- =====================================================

WITH monthly_revenue AS (

    SELECT
        DATE_TRUNC('month', booking_date) AS month,
        SUM(price) AS revenue

    FROM hotel_bookings

    WHERE status IN ('Confirmed', 'Completed')

    GROUP BY DATE_TRUNC('month', booking_date)
)

SELECT
    month,
    revenue,

    LAG(revenue) OVER (
        ORDER BY month
    ) AS previous_month_revenue,

    ROUND(
        (
            (
                revenue -
                LAG(revenue) OVER (
                    ORDER BY month
                )
            )
            /
            NULLIF(
                LAG(revenue) OVER (
                    ORDER BY month
                ),
                0
            )
        ) * 100,
        2
    ) AS growth_percentage

FROM monthly_revenue

ORDER BY month;


-- =====================================================
-- QUERY 3
-- AVERAGE RATING BY COUNTRY
-- =====================================================

SELECT
    country,
    COUNT(*) AS total_bookings,
    ROUND(AVG(rating), 2) AS average_rating

FROM hotel_bookings

GROUP BY country

ORDER BY average_rating DESC;


-- =====================================================
-- QUERY 4
-- REVENUE BY ROOM TYPE
-- =====================================================

SELECT
    room_type,
    COUNT(*) AS total_bookings,
    SUM(price) AS total_revenue,
    ROUND(AVG(price), 2) AS average_price

FROM hotel_bookings

WHERE status IN ('Confirmed', 'Completed')

GROUP BY room_type

ORDER BY total_revenue DESC;


-- =====================================================
-- QUERY 5
-- BOOKING STATUS DISTRIBUTION
-- =====================================================

SELECT
    status,
    COUNT(*) AS booking_count,

    ROUND(
        COUNT(*) * 100.0 /
        SUM(COUNT(*)) OVER (),
        2
    ) AS percentage

FROM hotel_bookings

GROUP BY status

ORDER BY booking_count DESC;


-- =====================================================
-- PERFORMANCE TEST
-- DATE FILTER
-- =====================================================

EXPLAIN ANALYZE

SELECT
    booking_id,
    hotel_name,
    price,
    booking_date

FROM hotel_bookings

WHERE booking_date >= '2026-01-01'
AND booking_date < '2026-04-01';