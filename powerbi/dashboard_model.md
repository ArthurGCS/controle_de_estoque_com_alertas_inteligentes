# Dashboard Power BI

## Fonte de dados

Opcoes:

1. Conectar direto no MySQL e importar as views:
   - `v_inventory_status`
   - `v_stock_movements_enriched`
   - `alert_history`
2. Rodar `python -m estoque_monitor.export_powerbi` e importar os CSVs em `powerbi/data/`.

## Relacionamentos

- `inventory_status[product_id]` 1:N `stock_movements[product_id]`
- `inventory_status[product_id]` 1:N `alerts_history[product_id]`

## Medidas DAX sugeridas

```DAX
Produtos Ativos = COUNTROWS(FILTER(inventory_status, inventory_status[is_active] = TRUE()))

Produtos Baixo Estoque =
COUNTROWS(
    FILTER(
        inventory_status,
        inventory_status[is_active] = TRUE()
            && inventory_status[stock_status] IN {"BAIXO", "CRITICO"}
    )
)

Valor em Estoque = SUM(inventory_status[stock_value])

Qtd a Repor = SUM(inventory_status[suggested_reorder_qty])

Alertas Enviados =
COUNTROWS(FILTER(alerts_history, alerts_history[status] = "sent"))
```

## Visuais recomendados

- Cards: Produtos Baixo Estoque, Valor em Estoque, Qtd a Repor, Alertas Enviados.
- Tabela: SKU, Produto, Fornecedor, Estoque Atual, Minimo, Reposicao Sugerida, Status.
- Grafico de barras: Produtos em baixo estoque por categoria.
- Linha temporal: movimentacoes por data e tipo.
- Segmentadores: Categoria, Fornecedor, Status.
