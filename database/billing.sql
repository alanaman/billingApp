-- SELECT bill_id, COUNT(*) as cnt FROM bill_items group by bill_id having cnt > 2;
select bill_id, SUM(quantity * unit_price) from bill_items group by bill_id;