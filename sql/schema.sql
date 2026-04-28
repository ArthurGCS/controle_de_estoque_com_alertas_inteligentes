CREATE DATABASE IF NOT EXISTS estoque_monitor
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE estoque_monitor;

CREATE TABLE IF NOT EXISTS categories (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(120) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS suppliers (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(160) NOT NULL UNIQUE,
  contact_name VARCHAR(120),
  email VARCHAR(180),
  phone VARCHAR(40),
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS products (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  sku VARCHAR(60) NOT NULL UNIQUE,
  name VARCHAR(180) NOT NULL,
  category_id BIGINT UNSIGNED,
  supplier_id BIGINT UNSIGNED,
  unit VARCHAR(20) NOT NULL DEFAULT 'un',
  minimum_stock DECIMAL(12,2) NOT NULL DEFAULT 0,
  target_stock DECIMAL(12,2) NOT NULL DEFAULT 0,
  unit_cost DECIMAL(12,2) NOT NULL DEFAULT 0,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_products_category
    FOREIGN KEY (category_id) REFERENCES categories (id),
  CONSTRAINT fk_products_supplier
    FOREIGN KEY (supplier_id) REFERENCES suppliers (id)
);

CREATE TABLE IF NOT EXISTS stock_movements (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  product_id BIGINT UNSIGNED NOT NULL,
  movement_type ENUM('IN', 'OUT', 'ADJUSTMENT') NOT NULL,
  quantity DECIMAL(12,2) NOT NULL,
  unit_cost DECIMAL(12,2),
  document_ref VARCHAR(100),
  notes VARCHAR(255),
  movement_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_stock_movements_product
    FOREIGN KEY (product_id) REFERENCES products (id),
  UNIQUE KEY uq_stock_movements_product_doc_type (product_id, document_ref, movement_type),
  INDEX idx_stock_movements_product_at (product_id, movement_at),
  INDEX idx_stock_movements_type (movement_type)
);

CREATE TABLE IF NOT EXISTS alert_history (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  product_id BIGINT UNSIGNED NOT NULL,
  channel VARCHAR(30) NOT NULL,
  recipient VARCHAR(180) NOT NULL,
  status VARCHAR(30) NOT NULL,
  message TEXT NOT NULL,
  error_message TEXT,
  sent_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_alert_history_product
    FOREIGN KEY (product_id) REFERENCES products (id),
  INDEX idx_alert_history_product_sent (product_id, sent_at),
  INDEX idx_alert_history_status (status)
);

CREATE OR REPLACE VIEW v_inventory_status AS
SELECT
  p.id AS product_id,
  p.sku,
  p.name AS product_name,
  c.name AS category_name,
  s.name AS supplier_name,
  p.unit,
  COALESCE(st.current_stock, 0) AS current_stock,
  p.minimum_stock,
  p.target_stock,
  GREATEST(p.target_stock - COALESCE(st.current_stock, 0), 0) AS suggested_reorder_qty,
  p.unit_cost,
  COALESCE(st.current_stock, 0) * p.unit_cost AS stock_value,
  CASE
    WHEN COALESCE(st.current_stock, 0) <= 0 THEN 'CRITICO'
    WHEN COALESCE(st.current_stock, 0) <= p.minimum_stock THEN 'BAIXO'
    WHEN COALESCE(st.current_stock, 0) <= p.minimum_stock * 1.25 THEN 'ATENCAO'
    ELSE 'OK'
  END AS stock_status,
  p.is_active,
  NOW() AS snapshot_at
FROM products p
LEFT JOIN categories c ON c.id = p.category_id
LEFT JOIN suppliers s ON s.id = p.supplier_id
LEFT JOIN (
  SELECT
    product_id,
    SUM(
      CASE
        WHEN movement_type = 'IN' THEN quantity
        WHEN movement_type = 'OUT' THEN -quantity
        WHEN movement_type = 'ADJUSTMENT' THEN quantity
        ELSE 0
      END
    ) AS current_stock
  FROM stock_movements
  GROUP BY product_id
) st ON st.product_id = p.id;

CREATE OR REPLACE VIEW v_stock_movements_enriched AS
SELECT
  sm.id,
  sm.product_id,
  p.sku,
  p.name AS product_name,
  c.name AS category_name,
  sm.movement_type,
  sm.quantity,
  CASE
    WHEN sm.movement_type = 'IN' THEN sm.quantity
    WHEN sm.movement_type = 'OUT' THEN -sm.quantity
    WHEN sm.movement_type = 'ADJUSTMENT' THEN sm.quantity
    ELSE 0
  END AS signed_quantity,
  sm.unit_cost,
  sm.document_ref,
  sm.notes,
  sm.movement_at,
  sm.created_at
FROM stock_movements sm
JOIN products p ON p.id = sm.product_id
LEFT JOIN categories c ON c.id = p.category_id;
