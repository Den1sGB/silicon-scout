# Silicon Scout

Um web scraper em Python criado para rastrear preços de peças de hardware nas maiores lojas do Brasil (KaBuM, Pichau e Terabyte) e enviar alertas de promoções diretamente no Discord.

Diferente de scrapers comuns que são rapidamente derrubados pelas defesas das lojas, o Silicon Scout foi arquitetado com evasão de Cloudflare e anti-bots, permitindo um monitoramento contínuo e silencioso para você nunca perder uma queda de preço.

## Como funciona

Em vez de fazer requisições HTTP simples ou brigar com os elementos da barra de pesquisa, o script usa uma abordagem diferente:
- **Sessão Persistente:** Usa o Playwright para manter uma pasta de perfil do Chromium. Isso guarda os cookies de sessão e evita que o Cloudflare veja o bot como um visitante novo a cada 5 minutos.
- **Injeção de Rota:** O scraper entra na página inicial da loja, ganha o "selo de humano" no cookie e depois injeta a URL de busca diretamente na barra de endereços.
- **Cache Local:** Como o navegador não fecha entre os ciclos, ele não baixa as imagens da loja de novo, o que deixa a leitura do DOM muito rápida (geralmente 1 a 2 segundos).
- **Alerta de Preço:** Filtra o menor preço PIX da página e salva no PostgreSQL. Se for menor que a última leitura, dispara um webhook pro Discord.

## ⚠️ Aviso de Rate-Limiting (Modo Instantâneo)

O painel de controle permite configurar a varredura para o **Modo Instantâneo** (loop contínuo sem pausas). O uso prolongado dessa configuração **resultará em bloqueios de IP (Greylisting)**, afetando principalmente a **Pichau**, que possui o firewall mais rigoroso. 

Quando o bloqueio de rede ocorre, a página base carrega, mas os servidores da loja recusam o envio do catálogo de produtos, causando falhas de renderização e erros de timeout no terminal. 

Para um monitoramento seguro e contínuo (24/7), é estritamente recomendado manter o intervalo de varredura entre **5 e 10 minutos**.

## Stack

- **Python 3.12**
- **Playwright** (Automação e bypass)
- **PostgreSQL / SQLAlchemy** (Banco de dados e ORM)
- **Streamlit** (Dashboard para cadastrar os links/termos)

## Como rodar

### 1. Dependências
Crie seu ambiente virtual e instale os pacotes:

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

Baixe o binário do navegador do Playwright:
playwright install chromium

### 2. Banco de Dados
Suba o container do PostgreSQL via Docker:

docker-compose up -d

### 3. Rodando o projeto
O sistema exige a execução de dois processos simultâneos.

Terminal 1 (A Interface):
Para abrir o painel, gerenciar os alvos e alterar o tempo de busca:

streamlit run app.py

Terminal 2 (O Scraper):
Para rodar o motor que varre as lojas em background:

python main.py

*(Opcional: Para receber os alertas de queda de preço, defina a URL do seu Webhook do Discord na variável DISCORD_WEBHOOK_URL localizada no topo do arquivo main.py).*

## Autor
**DenisGB**
