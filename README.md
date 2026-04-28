# Monitor de Estoque com Alertas

Sistema em Python + Pandas que consulta o estoque no MySQL, identifica produtos abaixo do minimo e envia alertas automaticos por e-mail SMTP ou WhatsApp API. Tambem exporta bases prontas para uso no Power BI.

## Estrutura

- `sql/schema.sql`: tabelas, indices e views do MySQL.
- `sql/seed.sql`: dados de exemplo para testar.
- `src/estoque_monitor/main.py`: rotina principal de monitoramento.
- `src/estoque_monitor/export_powerbi.py`: exporta CSV/XLSX para dashboard.
- `src/estoque_monitor/dashboard.py`: dashboard Python em navegador com Streamlit.
- `powerbi/dashboard_model.md`: sugestao de modelo, medidas e visuais.
- `.env.example`: variaveis de ambiente.

## Instalacao

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
Copy-Item .env.example .env
```

Edite o arquivo `.env` com o acesso ao MySQL e ao canal de alerta.

## Banco de dados

Crie o schema e carregue dados de teste:

```powershell
mysql -u root -p < sql/schema.sql
mysql -u root -p estoque_monitor < sql/seed.sql
```

## Executar o monitor

O `.env.example` vem com `DRY_RUN=true`, entao a primeira execucao apenas mostra o que seria enviado.

```powershell
.\.venv\Scripts\python.exe -m estoque_monitor.main
```

Evite executar o arquivo diretamente com `src\estoque_monitor\main.py`, porque nesse modo o Python pode nao encontrar o pacote `estoque_monitor`. Use sempre `-m estoque_monitor.main` a partir da raiz do projeto.

## Solucao de problemas

### `ModuleNotFoundError: No module named 'estoque_monitor'`

Execute pela raiz do projeto e use o Python da `.venv`:

```powershell
.\.venv\Scripts\python.exe -m estoque_monitor.main
```

Se ainda aparecer, instale o pacote no ambiente:

```powershell
.\.venv\Scripts\python.exe -m pip install -e .
```

### `Can't connect to MySQL server on 'localhost'` ou `WinError 10061`

Esse erro indica que nao existe MySQL aceitando conexoes em `localhost:3306`. Verifique:

```powershell
Get-Service | Where-Object { $_.Name -match 'mysql|maria' -or $_.DisplayName -match 'mysql|maria' }
```

Se existir um servico como `MySQL80`, inicie-o em um PowerShell como administrador:

```powershell
Start-Service MySQL80
```

Se nenhum servico aparecer, instale o MySQL Server ou use uma instancia existente alterando `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD` e `MYSQL_DATABASE` no arquivo `.env`.

Para enviar de verdade, configure SMTP ou WhatsApp e altere:

```env
DRY_RUN=false
```

## Exportar dados para o Power BI

```powershell
.\.venv\Scripts\python.exe -m estoque_monitor.export_powerbi
```

Os arquivos serao gerados em `powerbi/data/`. No Power BI Desktop, use **Obter dados > Texto/CSV** e importe:

- `inventory_status.csv`
- `alerts_history.csv`
- `stock_movements.csv`
- `products.csv`

Tambem e possivel conectar direto no MySQL usando as views `v_inventory_status` e `v_stock_movements_enriched`.

## Dashboard Python no navegador

O projeto tambem tem um dashboard em Python com Streamlit. Ele pode ler o MySQL ao vivo ou os CSVs gerados em `powerbi/data/`.

Instale as dependencias atualizadas:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -e .
```

Abra o dashboard:

```powershell
.\scripts\run_dashboard.ps1
```

Se o PowerShell bloquear scripts por politica de execucao, use o `.bat`:

```powershell
.\scripts\run_dashboard.bat
```

Ou rode o `.ps1` com bypass apenas para este comando:

```powershell
powershell.exe -ExecutionPolicy Bypass -File ".\scripts\run_dashboard.ps1"
```

O Streamlit abrira o navegador automaticamente. Se preferir abrir manualmente, acesse:

```text
http://localhost:8501
```

Tambem da para rodar sem o script:

```powershell
.\.venv\Scripts\python.exe -m streamlit run src\estoque_monitor\dashboard.py
```

## Agendamento

No Windows Task Scheduler, crie uma tarefa para rodar a cada hora:

```powershell
powershell.exe -ExecutionPolicy Bypass -File "C:\Users\Arthur Silva\Documents\New project\scripts\run_monitor.ps1"
```

## Como funciona

1. O script calcula o estoque atual a partir de `stock_movements`.
2. Produtos ativos com `current_stock <= minimum_stock` entram no alerta.
3. O historico em `alert_history` evita repetir alertas dentro de `ALERT_REPEAT_HOURS`.
4. O alerta e enviado pelos canais configurados em `ALERT_CHANNELS`.
5. As views e exports alimentam o dashboard do Power BI.
