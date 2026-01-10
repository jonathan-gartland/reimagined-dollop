-- Useful queries for the liquor database

-- ===== COLLECTION OVERVIEW =====

-- Total number of bottles
SELECT
    SUM(count) as total_bottles,
    COUNT(*) as unique_items
FROM liquor;

-- Total investment
SELECT
    SUM(count) as total_bottles,
    SUM(price_cost * count) as total_spent,
    SUM(replacement_cost * count) as replacement_value,
    SUM(replacement_cost * count) - SUM(price_cost * count) as potential_gain
FROM liquor
WHERE price_cost IS NOT NULL;

-- Collection by country
SELECT
    country_of_origin,
    SUM(count) as bottle_count,
    COUNT(*) as unique_items,
    SUM(price_cost * count) as total_value
FROM liquor
GROUP BY country_of_origin
ORDER BY bottle_count DESC;

-- Collection by category/style
SELECT
    category_style,
    SUM(count) as bottle_count,
    COUNT(*) as unique_items,
    SUM(price_cost * count) as total_value
FROM liquor
GROUP BY category_style
ORDER BY bottle_count DESC;

-- ===== BY DISTILLERY =====

-- Collection by distillery
SELECT
    distillery,
    SUM(count) as bottle_count,
    COUNT(*) as unique_expressions,
    SUM(price_cost * count) as total_invested
FROM liquor
WHERE distillery IS NOT NULL
GROUP BY distillery
ORDER BY bottle_count DESC;

-- Most valuable distilleries
SELECT
    distillery,
    SUM(count) as bottles,
    SUM(price_cost * count) as total_cost,
    SUM(replacement_cost * count) as replacement_value,
    SUM(replacement_cost * count) - SUM(price_cost * count) as appreciation
FROM liquor
WHERE distillery IS NOT NULL
GROUP BY distillery
ORDER BY replacement_value DESC NULLS LAST
LIMIT 10;

-- ===== OPENED VS UNOPENED =====

-- Opened vs unopened breakdown
SELECT
    opened_closed,
    SUM(count) as bottle_count,
    COUNT(*) as unique_items,
    SUM(price_cost * count) as total_value
FROM liquor
GROUP BY opened_closed
ORDER BY opened_closed;

-- Most valuable unopened bottles
SELECT
    name,
    count,
    distillery,
    age,
    replacement_cost,
    price_cost,
    replacement_cost - price_cost as appreciation
FROM liquor
WHERE opened_closed = 'unopened'
    AND replacement_cost IS NOT NULL
ORDER BY replacement_cost DESC
LIMIT 20;

-- ===== VALUABLE BOTTLES =====

-- Most expensive bottles (by purchase price)
SELECT
    name,
    count,
    distillery,
    category_style,
    age,
    price_cost,
    replacement_cost,
    opened_closed
FROM liquor
WHERE price_cost IS NOT NULL
ORDER BY price_cost DESC
LIMIT 20;

-- Best appreciation (replacement value vs cost)
SELECT
    name,
    count,
    distillery,
    price_cost,
    replacement_cost,
    replacement_cost - price_cost as appreciation,
    ROUND(((replacement_cost - price_cost) / NULLIF(price_cost, 0) * 100)::numeric, 1) as appreciation_pct
FROM liquor
WHERE price_cost IS NOT NULL
    AND replacement_cost IS NOT NULL
    AND price_cost > 0
ORDER BY appreciation DESC
LIMIT 20;

-- ===== SEARCH QUERIES =====

-- Search by name
SELECT name, count, distillery, category_style, age, abv, price_cost, opened_closed
FROM liquor
WHERE name ILIKE '%laphroaig%'
ORDER BY name;

-- Search by distillery
SELECT name, count, age, abv, volume, price_cost, opened_closed
FROM liquor
WHERE distillery ILIKE '%heaven hill%'
ORDER BY name, age;

-- Find all bourbon
SELECT name, count, distillery, age, price_cost, opened_closed
FROM liquor
WHERE category_style ILIKE '%bourbon%'
ORDER BY distillery, name;

-- Find all scotch
SELECT name, count, region, distillery, age, price_cost, opened_closed
FROM liquor
WHERE category_style ILIKE '%scotch%'
ORDER BY region, distillery, name;

-- ===== BY REGION =====

-- Scotch by region
SELECT
    region,
    SUM(count) as bottle_count,
    COUNT(*) as unique_items,
    SUM(price_cost * count) as total_value
FROM liquor
WHERE category_style ILIKE '%scotch%'
    AND region IS NOT NULL
GROUP BY region
ORDER BY bottle_count DESC;

-- ===== AGE ANALYSIS =====

-- Find aged statements
SELECT name, count, distillery, age, category_style, price_cost, opened_closed
FROM liquor
WHERE age IS NOT NULL
    AND age != '-'
ORDER BY
    CASE
        WHEN age ~ '^\d+' THEN CAST(substring(age from '^\d+') AS INTEGER)
        ELSE 0
    END DESC,
    name;

-- ===== PURCHASE HISTORY =====

-- Recent purchases
SELECT name, count, distillery, purchased_approx, price_cost, opened_closed
FROM liquor
WHERE purchased_approx IS NOT NULL
ORDER BY purchased_approx DESC
LIMIT 20;

-- Purchases by year
SELECT
    EXTRACT(YEAR FROM purchased_approx) as year,
    SUM(count) as bottles_purchased,
    SUM(price_cost * count) as amount_spent
FROM liquor
WHERE purchased_approx IS NOT NULL
GROUP BY year
ORDER BY year DESC;

-- ===== SPECIFIC SERIES =====

-- All Elijah Craig Barrel Proof
SELECT name, count, age, abv, errata, purchased_approx, price_cost, opened_closed
FROM liquor
WHERE name ILIKE '%elijah craig barrel proof%'
ORDER BY purchased_approx DESC NULLS LAST;

-- All Blanton's variants
SELECT name, count, errata, abv, volume, price_cost, replacement_cost, opened_closed
FROM liquor
WHERE name ILIKE '%blanton%'
ORDER BY name;

-- ===== HIGH ABV =====

-- Highest proof bottles
SELECT name, count, distillery, abv, category_style, opened_closed
FROM liquor
WHERE abv IS NOT NULL
ORDER BY abv DESC
LIMIT 20;

-- Cask strength bottles (typically 50%+ ABV)
SELECT name, count, distillery, abv, price_cost, opened_closed
FROM liquor
WHERE abv >= 50.0
ORDER BY abv DESC;
