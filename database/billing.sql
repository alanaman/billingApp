-- SELECT bill_id, COUNT(*) as cnt FROM bill_items group by bill_id having cnt > 2;

-- select * from product;

select SUM(amt) from
(
select bill_id, timestamp, SUM(quantity * unit_price) as amt
from bills natural join bill_items 
-- WHERE strftime('%Y-%m', timestamp) = '2025-05'
group by bill_id
) as cbills;