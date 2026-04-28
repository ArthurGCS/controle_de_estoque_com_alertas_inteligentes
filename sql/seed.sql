USE estoque_monitor;

INSERT INTO categories (name) VALUES
  ('Informatica'),
  ('Escritorio'),
  ('Limpeza')
ON DUPLICATE KEY UPDATE name = VALUES(name);

INSERT INTO suppliers (name, contact_name, email, phone) VALUES
  ('Fornecedor Alpha', 'Marina Lopes', 'compras@alpha.example', '+55 11 3000-1000'),
  ('Distribuidora Beta', 'Rafael Costa', 'vendas@beta.example', '+55 11 3000-2000'),
  ('Suprimentos Delta', 'Camila Souza', 'contato@delta.example', '+55 11 3000-3000')
ON DUPLICATE KEY UPDATE
  contact_name = VALUES(contact_name),
  email = VALUES(email),
  phone = VALUES(phone);

INSERT INTO products
  (sku, name, category_id, supplier_id, unit, minimum_stock, target_stock, unit_cost)
VALUES
  (
    'TEC-001',
    'Teclado USB',
    (SELECT id FROM categories WHERE name = 'Informatica'),
    (SELECT id FROM suppliers WHERE name = 'Fornecedor Alpha'),
    'un',
    10,
    30,
    55.00
  ),
  (
    'MOU-001',
    'Mouse Optico',
    (SELECT id FROM categories WHERE name = 'Informatica'),
    (SELECT id FROM suppliers WHERE name = 'Fornecedor Alpha'),
    'un',
    15,
    40,
    32.00
  ),
  (
    'PAP-001',
    'Papel A4 500 folhas',
    (SELECT id FROM categories WHERE name = 'Escritorio'),
    (SELECT id FROM suppliers WHERE name = 'Distribuidora Beta'),
    'pct',
    20,
    80,
    24.90
  ),
  (
    'CAN-001',
    'Caneta azul',
    (SELECT id FROM categories WHERE name = 'Escritorio'),
    (SELECT id FROM suppliers WHERE name = 'Distribuidora Beta'),
    'cx',
    8,
    25,
    18.50
  ),
  (
    'DET-001',
    'Detergente 5L',
    (SELECT id FROM categories WHERE name = 'Limpeza'),
    (SELECT id FROM suppliers WHERE name = 'Suprimentos Delta'),
    'gal',
    5,
    15,
    21.00
  )
ON DUPLICATE KEY UPDATE
  name = VALUES(name),
  category_id = VALUES(category_id),
  supplier_id = VALUES(supplier_id),
  minimum_stock = VALUES(minimum_stock),
  target_stock = VALUES(target_stock),
  unit_cost = VALUES(unit_cost);

INSERT IGNORE INTO stock_movements
  (product_id, movement_type, quantity, unit_cost, document_ref, notes, movement_at)
SELECT id, 'IN', 20, unit_cost, 'NF-1001', 'Carga inicial', DATE_SUB(NOW(), INTERVAL 10 DAY)
FROM products WHERE sku = 'TEC-001'
UNION ALL
SELECT id, 'OUT', 13, unit_cost, 'REQ-2201', 'Uso interno', DATE_SUB(NOW(), INTERVAL 2 DAY)
FROM products WHERE sku = 'TEC-001'
UNION ALL
SELECT id, 'IN', 50, unit_cost, 'NF-1002', 'Carga inicial', DATE_SUB(NOW(), INTERVAL 8 DAY)
FROM products WHERE sku = 'MOU-001'
UNION ALL
SELECT id, 'OUT', 20, unit_cost, 'REQ-2202', 'Vendas', DATE_SUB(NOW(), INTERVAL 1 DAY)
FROM products WHERE sku = 'MOU-001'
UNION ALL
SELECT id, 'IN', 60, unit_cost, 'NF-1003', 'Carga inicial', DATE_SUB(NOW(), INTERVAL 12 DAY)
FROM products WHERE sku = 'PAP-001'
UNION ALL
SELECT id, 'OUT', 43, unit_cost, 'REQ-2203', 'Consumo administrativo', DATE_SUB(NOW(), INTERVAL 1 DAY)
FROM products WHERE sku = 'PAP-001'
UNION ALL
SELECT id, 'IN', 25, unit_cost, 'NF-1004', 'Carga inicial', DATE_SUB(NOW(), INTERVAL 9 DAY)
FROM products WHERE sku = 'CAN-001'
UNION ALL
SELECT id, 'OUT', 5, unit_cost, 'REQ-2204', 'Consumo administrativo', DATE_SUB(NOW(), INTERVAL 1 DAY)
FROM products WHERE sku = 'CAN-001'
UNION ALL
SELECT id, 'IN', 15, unit_cost, 'NF-1005', 'Carga inicial', DATE_SUB(NOW(), INTERVAL 7 DAY)
FROM products WHERE sku = 'DET-001'
UNION ALL
SELECT id, 'OUT', 12, unit_cost, 'REQ-2205', 'Limpeza predial', DATE_SUB(NOW(), INTERVAL 1 DAY)
FROM products WHERE sku = 'DET-001';
