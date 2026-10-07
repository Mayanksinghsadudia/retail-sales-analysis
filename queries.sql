-- QUERY: kpis
-- Positive sale value is not net revenue; cancelled and nonpositive lines were excluded.
SELECT ROUND(SUM(sales_value), 2) AS sales_gbp,
       COUNT(DISTINCT InvoiceNo) AS orders,
       COUNT(DISTINCT CustomerID) AS identified_customers,
       ROUND(SUM(sales_value) / COUNT(DISTINCT InvoiceNo), 2) AS average_order_value
FROM sales;

-- QUERY: monthly_sales
SELECT invoice_month AS month, ROUND(SUM(sales_value), 2) AS sales_gbp,
       COUNT(DISTINCT InvoiceNo) AS orders
FROM sales GROUP BY invoice_month ORDER BY invoice_month;

-- QUERY: country_sales
SELECT Country AS country, ROUND(SUM(sales_value), 2) AS sales_gbp,
       COUNT(DISTINCT InvoiceNo) AS orders
FROM sales GROUP BY Country ORDER BY sales_gbp DESC;

-- QUERY: top_products
SELECT StockCode AS stock_code, MAX(Description) AS description,
       SUM(Quantity) AS units, ROUND(SUM(sales_value), 2) AS sales_gbp
FROM sales GROUP BY StockCode ORDER BY sales_gbp DESC LIMIT 10;

-- QUERY: customer_summary
WITH customers AS (
    SELECT CustomerID, COUNT(DISTINCT InvoiceNo) AS purchases
    FROM sales WHERE CustomerID IS NOT NULL GROUP BY CustomerID
)
SELECT COUNT(*) AS identified_customers,
       SUM(CASE WHEN purchases > 1 THEN 1 ELSE 0 END) AS repeat_customers,
       ROUND(100.0 * SUM(CASE WHEN purchases > 1 THEN 1 ELSE 0 END) / COUNT(*), 2) AS repeat_customer_pct
FROM customers;
