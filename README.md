# ⚽ FBref Bot - Análise de Expected Goals (xG)

Bot automatizado para análise de dados de Expected Goals (xG) de times de futebol usando dados do **FBref**.

## 🚀 Funcionalidades

✅ **Busca Automática de Dados** - Coleta dados de xG direto do FBref  
✅ **Gerenciamento de Times** - Salve seus times favoritos para buscas rápidas  
✅ **Filtro por Competição** - Busque dados de ligas específicas  
✅ **Análise de Mandante/Visitante** - Separa dados de jogos em casa e fora  
✅ **Exportação CSV** - Copie e cole dados diretamente ou faça download  
✅ **Interface Intuitiva** - Fácil de usar, não precisa de conhecimento técnico  

## 📊 Dados Coletados

O bot coleta os seguintes dados de cada jogo:
- **Time** - Nome do time
- **Local** - Casa ou Fora
- **xG Feitos** - Expected Goals criados
- **xG Sofridos** - Expected Goals sofridos

## 🎯 Como Usar

### 1️⃣ Adicionar um Time
1. Vá em "➕ Adicionar Novo Time"
2. Digite o nome do time
3. Cole a URL da página do time no FBref
4. Clique em "💾 Salvar Time"

### 2️⃣ Buscar Dados
1. Vá em "📋 Selecionar Time Salvo"
2. Escolha o time na lista
3. Digite a competição (ex: "Serie A", "Premier League")
4. Clique em "🔍 Buscar Dados"

### 3️⃣ Copiar Dados
- Use a área de texto para copiar (Ctrl+A + Ctrl+C)
- Cole no Excel, Google Sheets ou qualquer planilha
- Ou faça download do CSV

## 🔗 Como Encontrar a URL do FBref

1. Acesse [FBref.com](https://fbref.com)
2. Busque pelo time desejado
3. Vá na aba "Scores & Fixtures" ou "Squad Stats"
4. Copie a URL completa da barra de endereços

Exemplo de URL válida:
```
https://fbref.com/en/squads/7cee947c/2024-2025/Corinthians-Stats
```

## 🛠️ Tecnologias

- **Python 3.13**
- **Streamlit** - Interface web
- **CloudScraper** - Web scraping avançado
- **BeautifulSoup4** - Parse de HTML
- **Pandas** - Manipulação de dados

## 📝 Notas

- O bot busca os **últimos 15 jogos** do time na competição especificada
- Os dados são coletados em tempo real do FBref
- É recomendado respeitar os termos de uso do FBref

## 👨‍💻 Desenvolvido por

**Vina-13dev**  
Desenvolvido com ❤️ usando Streamlit

---

⭐ **Se você gostou, deixe uma estrela no repositório!**
