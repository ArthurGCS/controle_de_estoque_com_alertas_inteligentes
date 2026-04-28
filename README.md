# 📦 Controle de Estoque com Alertas Inteligentes

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-005C84?style=for-the-badge&logo=mysql&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Power BI](https://img.shields.io/badge/Power_BI-F2C811?style=for-the-badge&logo=powerbi&logoColor=black)

> Um sistema automatizado para monitoramento pró-ativo de estoque, envio de alertas inteligentes (E-mail e WhatsApp) e visualização de dados em tempo real. Desenvolvido para resolver o problema de ruptura de estoque (stockout) e auxiliar na tomada de decisões rápidas de reposição.

---

## 🎯 O Problema que este projeto resolve

Na gestão de suprimentos e varejo, descobrir que um produto acabou apenas quando o cliente tenta comprar (ou quando a produção para) gera prejuízos e insatisfação. 
Este projeto atua de forma **preventiva**: monitora o banco de dados de estoque de forma contínua e notifica os responsáveis *antes* que o produto falte, além de fornecer dashboards analíticos para a equipe gerencial.

---

## ✨ Principais Funcionalidades

- **Monitoramento Contínuo:** Consulta o banco de dados (MySQL) para identificar produtos que atingiram ou estão abaixo do nível mínimo de segurança.
- **Alertas Multicanal:** Disparo automatizado de notificações via **E-mail (SMTP)** e **WhatsApp (API)** para os gestores responsáveis.
- **Dashboard Web (Streamlit):** Interface intuitiva em Python rodando direto no navegador para acompanhamento em tempo real dos níveis de estoque, valor imobilizado e histórico de alertas.
- **Integração com Power BI:** Exportação de bases tratadas (CSV/XLSX) e views prontas no MySQL para criação de relatórios gerenciais avançados.
- **Prevenção de Spam:** Sistema inteligente que registra alertas anteriores (tabela `alert_history`) para evitar envios duplicados no mesmo intervalo de horas.

---

## 📸 Demonstração

*(Adicione aqui um GIF ou prints da tela do Dashboard Streamlit e do Power BI. Exemplos do que adicionar:)*
- **[Print 1]** Tela inicial do Dashboard Streamlit mostrando os KPIs.
- **[Print 2]** Exemplo de notificação de alerta chegando no WhatsApp/E-mail.
- **[Print 3]** Relatório gerencial no Power BI.

---

## 🏗️ Arquitetura e Tecnologias

O sistema é dividido em três camadas principais:
1. **Banco de Dados (MySQL):** Armazena produtos, movimentações de estoque (entradas e saídas) e histórico de alertas. Utiliza `Views` estruturadas para facilitar consultas analíticas.
2. **Motor de Processamento (Python + Pandas):** Roda em segundo plano (agendado via Task Scheduler/Cron). Conecta ao banco, calcula os níveis atuais cruzando entradas e saídas, verifica regras de negócio e realiza integrações com APIs de mensageria.
3. **Visualização:** 
   - **Streamlit:** Dashboard web interativo e rápido para a operação diária.
   - **Power BI:** Conexão direta ao banco ou via arquivos gerados para análise aprofundada (Business Intelligence).

---

## 🚀 Como Executar Localmente

### Pré-requisitos
- Python 3.9+
- Servidor MySQL rodando local (ou nuvem)

### Passo a Passo

1. **Clone o repositório e configure o ambiente virtual:**
   ```powershell
   git clone https://github.com/SEU_USUARIO/controle-estoque-alertas.git
   cd controle-estoque-alertas
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   pip install -e .
   ```

2. **Configuração de Variáveis de Ambiente:**
   Copie o arquivo de exemplo e configure suas credenciais de banco e APIs:
   ```powershell
   Copy-Item .env.example .env
   ```
   *(Edite o arquivo `.env` gerado com os dados do MySQL e credenciais de SMTP/WhatsApp).*

3. **Banco de Dados:**
   Crie as tabelas e popule com os dados de teste fornecidos:
   ```powershell
   mysql -u root -p < sql/schema.sql
   mysql -u root -p estoque_monitor < sql/seed.sql
   ```

4. **Rodando o Dashboard Web:**
   Execute o script prático:
   ```powershell
   .\scripts\run_dashboard.ps1
   ```
   *O painel abrirá automaticamente em `http://localhost:8501`.*

5. **Testando o Monitor de Alertas:**
   O modo `DRY_RUN=true` vem ativado por padrão no `.env` para simular os envios no console sem disparar mensagens reais.
   ```powershell
   .\.venv\Scripts\python.exe -m estoque_monitor.main
   ```

---

## 📊 Exportação para Power BI

Para atualizar as bases estáticas consumidas pelo Power BI:
```powershell
.\.venv\Scripts\python.exe -m estoque_monitor.export_powerbi
```
*Os arquivos CSV tratados estarão disponíveis na pasta `powerbi/data/`.*

---

## 💡 Próximos Passos (Evoluções Possíveis)
- [ ] Implementar previsão de demanda utilizando Machine Learning (ex: Prophet/Scikit-learn).
- [ ] Criar API REST (FastAPI) para receber novas movimentações de estoque de outros sistemas (ERPs, PDVs).
- [ ] Containerizar a aplicação completa com Docker e Docker Compose.

---

## 👨‍💻 Autor

**Arthur Silva**

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/SEU_LINKEDIN_AQUI)
[![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/SEU_GITHUB_AQUI)

*Se você achou este projeto interessante, sinta-se à vontade para deixar uma ⭐️ no repositório e me adicionar no LinkedIn para conversarmos sobre Python, Dados e Automação!*
