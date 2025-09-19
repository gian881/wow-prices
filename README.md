# WoW Prices - Análise de Preços para World of Warcraft

[![Python](https://img.shields.io/badge/Python-3.12-3776AB.svg?style=for-the-badge&logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116.1-009688.svg?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Vue.js](https://img.shields.io/badge/Vue.js-3.5-4FC08D.svg?style=for-the-badge&logo=vue.js)](https://vuejs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.8-3178C6.svg?style=for-the-badge&logo=typescript)](https://www.typescriptlang.org/)

Aplicação web full-stack para análise de preços da API da Blizzard, com backend em FastAPI (Python) e frontend em Vue.js. O sistema coleta e armazena dados em PostgreSQL, apresentando-os em gráficos interativos com atualizações em tempo real via WebSockets.

## 🎯 Principais Funcionalidades

-   **Coleta de Dados Automatizada:** Um serviço de fundo busca periodicamente dados de preços da API oficial da Blizzard, garantindo que as informações estejam sempre atualizadas.
-   **Visualização de Dados Interativa:** Frontend construído com Vue.js que utiliza Plotly.js para renderizar heatmaps e gráficos de linha, mostrando a variação de preços e quantidades por hora e dia da semana.
-   **Notificações em Tempo Real:** A aplicação usa WebSockets para notificar o frontend instantaneamente quando novos dados são processados, permitindo que os usuários atualizem suas visualizações sem recarregar a página.
-   **Configurações Personalizadas:** Os usuários podem definir configurações por item, como alertas de preço e intenção de compra ou venda.
-   **Armazenamento de Arquivos na Nuvem:** As imagens dos itens são salvas de forma persistente no Supabase Storage, com um sistema de verificação na inicialização do servidor para garantir a integridade dos dados.

## 🛠️ Tecnologias Utilizadas

### **Backend**

-   **Framework:** FastAPI
-   **Linguagem:** Python
-   **Banco de Dados:** PostgreSQL (gerenciado pelo Supabase)
-   **ORM:** SQLModel (baseado em SQLAlchemy e Pydantic)
-   **Comunicação Real-Time:** WebSockets

### **Frontend**

-   **Framework:** Vue.js 3 (com Composition API)
-   **Linguagem:** TypeScript
-   **Build Tool:** Vite
-   **Visualização de Dados:** Plotly.js
-   **Estilização:** Tailwind CSS & Shadcn UI

### **Infraestrutura e Deploy**

-   **Banco de Dados & Storage:** Supabase
-   **Containerização:** Docker (para ambiente de desenvolvimento com PostgreSQL)
-   **Hospedagem (Backend):** Render
-   **Hospedagem (Frontend):** Vercel

## ⚙️ Configuração e Instalação Local

Para rodar este projeto localmente, siga os passos abaixo.

#### **Pré-requisitos**

-   [Git](https://git-scm.com/)
-   [Python 3.10+](https://www.python.org/)
-   [Node.js 18+](https://nodejs.org/) (com pnpm)
-   [Docker](https://www.docker.com/) (para o banco de dados PostgreSQL)

#### **1. Clonar o Repositório**

```bash
git clone [https://github.com/gian881/wow-prices.git](https://github.com/gian881/wow-prices.git)
cd wow-prices
```

#### **2. Configurar o Banco de Dados (Docker)**

1.  Inicie um container PostgreSQL usando Docker:
    ```bash
    docker run --name wow-db -e POSTGRES_USER=seu_usuario -e POSTGRES_PASSWORD=sua_senha -p 5432:5432 -d postgres
    ```
2.  Conecte-se ao banco de dados e execute o schema SQL para criar as tabelas e tipos necessários.

#### **3. Configurar o Backend**

1.  Navegue até a pasta do backend e crie um ambiente virtual:
    ```bash
    cd backend
    python -m venv venv
    source venv/bin/activate  # No Windows: venv\Scripts\activate
    ```
2.  Instale as dependências:
    ```bash
    pip install -r requirements.txt
    ```
3.  Crie um arquivo `.env` a partir do `.env.example` e preencha com suas credenciais (API da Blizzard, URL do banco de dados, etc.).
4.  Inicie o servidor:
    ```bash
    uvicorn app.main:app --reload
    ```

#### **4. Configurar o Frontend**

1.  Em um novo terminal, navegue até a pasta do frontend:
    ```bash
    cd frontend
    ```
2.  Instale as dependências:
    ```bash
    npm install
    ```
3.  Crie um arquivo `.env.local` a partir do `.env.example` e configure a URL do seu backend.
4.  Inicie o servidor de desenvolvimento:
    ```bash
    npm run dev
    ```

A aplicação frontend estará disponível em `http://localhost:5173` e o backend em `http://localhost:8000`.

## 🚀 Planos Futuros

-   [ ] **🗓️ Período Configurável:** Adicionar uma opção para que o usuário defina o período de tempo (ex: últimos 7 dias, último mês) a ser considerado para o cálculo do "melhor dia/hora".
-   [ ] **📊 Filtros nos Gráficos:** Implementar filtros interativos diretamente nos gráficos para analisar dados de forma mais granular.
-   [ ] **🔐 Contas:** Permitir que o usuário consiga criar uma conta e consiga rastrear seus próprios itens.
-   [ ] **🌐 Configuração de Timezone:** Permitir que os usuários configurem seu fuso horário local para que as análises de "melhor hora" seja baseada na sua região.
-   [ ] **🗓️ Período Configurável:** Adicionar uma opção para que o usuário defina o período de tempo (ex: últimos 7 dias, último mês) a ser considerado para o cálculo do "melhor dia/hora".
-   [ ] **📱 Suporte Mobile:** Melhorar a responsividade da interface para garantir uma experiência de uso otimizada em dispositivos móveis.
