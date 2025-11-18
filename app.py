import streamlit as st
import json
import re
import time
import random
import pandas as pd
from pathlib import Path
import io

try:
    import cloudscraper
    from bs4 import BeautifulSoup
except ImportError:
    st.error("❌ Bibliotecas não instaladas.")
    st.stop()


# Configuração da página
st.set_page_config(
    page_title="Bot FBref - Análise de xG",
    page_icon="⚽",
    layout="wide"
)

# Arquivo de times salvos
TIMES_FILE = Path("times_salvos.json")

# Lista de User-Agents realistas
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
]


def carregar_times():
    """Carrega times do arquivo JSON"""
    if TIMES_FILE.exists():
        with open(TIMES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def salvar_times(times):
    """Salva times no arquivo JSON"""
    with open(TIMES_FILE, 'w', encoding='utf-8') as f:
        json.dump(times, f, indent=2, ensure_ascii=False)


def limpar_comentarios_html(html_content):
    """Remove comentários HTML"""
    html_limpo = re.sub(r'<!--', '', html_content)
    html_limpo = re.sub(r'-->', '', html_limpo)
    return html_limpo


def normalizar_texto(texto):
    """Normaliza texto para comparação"""
    texto = texto.lower().strip()
    texto = texto.replace('é', 'e').replace('á', 'a').replace('ã', 'a')
    texto = texto.replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
    texto = ' '.join(texto.split())
    return texto


def criar_scraper_avancado():
    """Cria um scraper com configurações anti-detecção melhoradas"""
    user_agent = random.choice(USER_AGENTS)
    
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'mobile': False,
            'desktop': True
        },
        delay=random.uniform(3, 6)
    )
    
    scraper.headers.update({
        'User-Agent': user_agent,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
    })
    
    return scraper


def buscar_dados_fbref(url_base, nome_time, competicao):
    """Busca dados do FBref com proteção anti-bot melhorada"""
    try:
        scraper = criar_scraper_avancado()
        time.sleep(random.uniform(4, 7))
        
        response = scraper.get(url_base, timeout=45)
        response.raise_for_status()
        
        time.sleep(random.uniform(2, 4))
        
        html_limpo = limpar_comentarios_html(response.text)
        soup = BeautifulSoup(html_limpo, 'html.parser')
        
        competicao_norm = normalizar_texto(competicao)
        
        tabela_principal = None
        for table in soup.find_all('table'):
            table_id = table.get('id', '')
            caption = table.find('caption')
            
            if table_id.startswith('matchlogs_') or table_id.startswith('sched_') or 'scores' in table_id.lower():
                if caption:
                    caption_text = caption.get_text().strip()
                    if 'all competitions' in caption_text.lower() or 'scores' in caption_text.lower() or 'fixtures' in caption_text.lower():
                        tabela_principal = table
                        break
        
        if not tabela_principal:
            return None, "Tabela de Match Logs não encontrada"
        
        tbody = tabela_principal.find('tbody')
        if not tbody:
            return None, "Corpo da tabela não encontrado"
        
        dados = []
        competicoes_encontradas = set()
        
        for linha in tbody.find_all('tr'):
            if len(dados) >= 15:
                break
            
            comp_cell = linha.find('td', {'data-stat': 'comp'})
            if not comp_cell:
                continue
            
            comp_text = comp_cell.get_text(strip=True)
            comp_norm = normalizar_texto(comp_text)
            competicoes_encontradas.add(comp_text)
            
            if competicao_norm not in comp_norm:
                continue
            
            venue_cell = linha.find('td', {'data-stat': 'venue'})
            xg_for_cell = linha.find('td', {'data-stat': 'xg_for'})
            xg_against_cell = linha.find('td', {'data-stat': 'xg_against'})
            
            if not xg_for_cell or not xg_against_cell:
                continue
            
            xg_feitos = xg_for_cell.get_text(strip=True)
            xg_sofridos = xg_against_cell.get_text(strip=True)
            
            if not xg_feitos or not xg_sofridos or xg_feitos in ['', '-', '—'] or xg_sofridos in ['', '-', '—']:
                continue
            
            try:
                float(xg_feitos)
                float(xg_sofridos)
            except (ValueError, TypeError):
                continue
            
            local = ""
            if venue_cell:
                venue_text = venue_cell.get_text(strip=True)
                if venue_text == "Home":
                    local = "casa"
                elif venue_text == "Away":
                    local = "fora"
                else:
                    continue
            else:
                continue
            
            dados.append({
                'time': nome_time,
                'local': local,
                'xg_feitos': xg_feitos,
                'xg_sofridos': xg_sofridos
            })
        
        if not dados:
            comp_list = "\n".join([f"• {c}" for c in sorted(competicoes_encontradas)])
            return None, f"Nenhum jogo encontrado.\n\nCompetições disponíveis:\n{comp_list}"
        
        return dados, None
        
    except Exception as e:
        erro_msg = str(e)
        
        if '403' in erro_msg or 'Forbidden' in erro_msg:
            return None, (
                "⚠️ O FBref bloqueou o acesso automático.\n\n"
                "💡 Use o **MODO MANUAL** abaixo:\n"
                "Faça upload de um CSV com os dados!"
            )
        elif '429' in erro_msg or 'Too Many' in erro_msg:
            return None, "⚠️ Muitas requisições. Aguarde alguns minutos."
        else:
            return None, f"❌ Erro: {erro_msg}"


def processar_csv_upload(arquivo_csv, nome_time):
    """Processa CSV enviado pelo usuário"""
    try:
        df = pd.read_csv(arquivo_csv)
        
        # Verificar colunas necessárias
        colunas_necessarias = ['local', 'xg_feitos', 'xg_sofridos']
        if not all(col in df.columns for col in colunas_necessarias):
            return None, "❌ CSV deve ter as colunas: local, xg_feitos, xg_sofridos"
        
        # Adicionar nome do time
        df['time'] = nome_time
        
        # Reorganizar colunas
        df = df[['time', 'local', 'xg_feitos', 'xg_sofridos']]
        
        # Converter para lista de dicionários
        dados = df.to_dict('records')
        
        return dados, None
        
    except Exception as e:
        return None, f"❌ Erro ao processar CSV: {str(e)}"


# Interface principal
st.title("⚽ Bot de Análise FBref - Expected Goals (xG)")
st.markdown("---")

# Carregar times
times_salvos = carregar_times()

# Sidebar
with st.sidebar:
    st.header("⚙️ Configurações")
    
    modo = st.radio(
        "Escolha o modo:",
        ["🔍 Buscar Dados", "➕ Adicionar Time", "🗑️ Gerenciar Times"]
    )
    
    st.markdown("---")
    st.markdown("### 📊 Times Cadastrados")
    st.info(f"Total: **{len(times_salvos)}** times")

# Área principal
if modo == "🔍 Buscar Dados":
    st.header("🔍 Buscar Dados de xG")
    
    if not times_salvos:
        st.warning("⚠️ Nenhum time cadastrado. Use 'Adicionar Time' primeiro!")
    else:
        # Seleção de time
        time_selecionado = st.selectbox(
            "🏆 Selecione o time:",
            options=sorted(times_salvos.keys())
        )
        
        # Abas para os dois modos
        tab1, tab2 = st.tabs(["🤖 Modo Automático", "📤 Modo Manual (Upload CSV)"])
        
        # TAB 1: MODO AUTOMÁTICO
        with tab1:
            st.markdown("### 🤖 Busca Automática")
            st.info("O bot tenta buscar automaticamente. Se der erro 403, use o Modo Manual!")
            
            competicao = st.text_input(
                "🏅 Competição:",
                placeholder="Ex: Serie A, Premier League",
                key="comp_auto"
            )
            
            if st.button("🔍 Buscar Automaticamente", type="primary"):
                if not competicao:
                    st.error("❌ Digite a competição!")
                else:
                    url = times_salvos[time_selecionado]
                    
                    with st.spinner(f"🔄 Buscando dados... (até 15s)"):
                        dados, erro = buscar_dados_fbref(url, time_selecionado, competicao)
                    
                    if erro:
                        st.error(erro)
                    else:
                        st.success(f"✅ {len(dados)} jogo(s) encontrado(s)!")
                        
                        df = pd.DataFrame(dados)
                        
                        st.subheader("📊 Tabela de Dados")
                        st.dataframe(df, use_container_width=True, hide_index=True)
                        
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Total de Jogos", len(dados))
                        with col2:
                            jogos_casa = len([d for d in dados if d['local'] == 'casa'])
                            st.metric("Jogos em Casa", jogos_casa)
                        with col3:
                            jogos_fora = len([d for d in dados if d['local'] == 'fora'])
                            st.metric("Jogos Fora", jogos_fora)
                        with col4:
                            media_xg = sum([float(d['xg_feitos']) for d in dados]) / len(dados)
                            st.metric("Média xG", f"{media_xg:.2f}")
                        
                        st.markdown("---")
                        st.subheader("📋 Dados CSV (Copiar)")
                        csv_text = df.to_csv(index=False)
                        st.text_area("👇 Copie:", value=csv_text, height=200)
                        
                        st.download_button(
                            "📥 Download CSV",
                            data=csv_text,
                            file_name=f"{time_selecionado}_{competicao}.csv",
                            mime="text/csv"
                        )
        
        # TAB 2: MODO MANUAL
        with tab2:
            st.markdown("### 📤 Upload Manual de CSV")
            
            st.info(
                "💡 **Como usar:**\n"
                "1. Acesse o FBref no navegador normalmente\n"
                "2. Copie os dados da tabela\n"
                "3. Cole no Excel/Google Sheets\n"
                "4. Salve como CSV com as colunas: `local`, `xg_feitos`, `xg_sofridos`\n"
                "5. Faça upload aqui!"
            )
            
            # Exemplo de formato
            with st.expander("📋 Ver exemplo de formato CSV"):
                exemplo = pd.DataFrame({
                    'local': ['casa', 'fora', 'casa'],
                    'xg_feitos': ['1.5', '2.3', '1.8'],
                    'xg_sofridos': ['0.8', '1.2', '1.5']
                })
                st.dataframe(exemplo)
                st.caption("Cole os dados nesse formato e salve como CSV")
            
            # Upload
            arquivo_upload = st.file_uploader(
                "📁 Escolha o arquivo CSV:",
                type=['csv'],
                help="Arquivo CSV com colunas: local, xg_feitos, xg_sofridos"
            )
            
            if arquivo_upload:
                st.success("✅ Arquivo carregado!")
                
                if st.button("📊 Processar Dados", type="primary"):
                    dados, erro = processar_csv_upload(arquivo_upload, time_selecionado)
                    
                    if erro:
                        st.error(erro)
                    else:
                        st.success(f"✅ {len(dados)} jogo(s) processado(s)!")
                        
                        df = pd.DataFrame(dados)
                        
                        st.subheader("📊 Tabela de Dados")
                        st.dataframe(df, use_container_width=True, hide_index=True)
                        
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Total de Jogos", len(dados))
                        with col2:
                            jogos_casa = len([d for d in dados if d['local'] == 'casa'])
                            st.metric("Jogos em Casa", jogos_casa)
                        with col3:
                            jogos_fora = len([d for d in dados if d['local'] == 'fora'])
                            st.metric("Jogos Fora", jogos_fora)
                        with col4:
                            media_xg = sum([float(d['xg_feitos']) for d in dados]) / len(dados)
                            st.metric("Média xG", f"{media_xg:.2f}")
                        
                        st.markdown("---")
                        csv_text = df.to_csv(index=False)
                        st.download_button(
                            "📥 Download Resultado",
                            data=csv_text,
                            file_name=f"{time_selecionado}_processado.csv",
                            mime="text/csv"
                        )

elif modo == "➕ Adicionar Time":
    st.header("➕ Adicionar Novo Time")
    
    col1, col2 = st.columns(2)
    
    with col1:
        novo_nome = st.text_input("📝 Nome do Time:", placeholder="Ex: Corinthians")
    
    with col2:
        nova_url = st.text_input("🔗 URL do FBref:", placeholder="https://fbref.com/en/squads/.../")
    
    if st.button("💾 Salvar Time", type="primary"):
        if not novo_nome or not nova_url:
            st.error("❌ Preencha todos os campos!")
        elif novo_nome in times_salvos:
            st.warning(f"⚠️ O time '{novo_nome}' já existe!")
        else:
            times_salvos[novo_nome] = nova_url
            salvar_times(times_salvos)
            st.success(f"✅ Time '{novo_nome}' adicionado!")
            st.balloons()
            time.sleep(1)
            st.rerun()

else:  # Gerenciar Times
    st.header("🗑️ Gerenciar Times")
    
    if not times_salvos:
        st.warning("⚠️ Nenhum time cadastrado.")
    else:
        st.info(f"📋 Você tem **{len(times_salvos)}** times")
        
        times_para_excluir = []
        
        for i, (nome_time, url_time) in enumerate(sorted(times_salvos.items())):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                if st.checkbox(f"🏆 {nome_time}", key=f"check_{i}"):
                    times_para_excluir.append(nome_time)
            
            with col2:
                st.caption(f"[Link]({url_time})")
        
        if times_para_excluir:
            st.markdown("---")
            st.warning(f"⚠️ Excluir **{len(times_para_excluir)}** time(s)?")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🗑️ Confirmar", type="primary"):
                    for time_nome in times_para_excluir:
                        del times_salvos[time_nome]
                    
                    salvar_times(times_salvos)
                    st.success(f"✅ {len(times_para_excluir)} time(s) excluído(s)!")
                    time.sleep(1)
                    st.rerun()
            
            with col2:
                if st.button("❌ Cancelar"):
                    st.rerun()

# Rodapé
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center'>
        <p>🤖 Bot de Análise FBref | Multi-Modo</p>
    </div>
    """,
    unsafe_allow_html=True
)
