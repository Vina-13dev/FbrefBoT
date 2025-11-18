import streamlit as st
import json
import re
import time
import pandas as pd
from pathlib import Path

try:
    import cloudscraper
    from bs4 import BeautifulSoup
except ImportError:
    st.error("❌ Bibliotecas não instaladas. Execute: pip install cloudscraper beautifulsoup4")
    st.stop()


# Configuração da página
st.set_page_config(
    page_title="Bot FBref - Análise de xG",
    page_icon="⚽",
    layout="wide"
)

# Arquivo de times salvos
TIMES_FILE = Path("times_salvos.json")


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


def buscar_dados_fbref(url_base, nome_time, competicao):
    """Busca dados do FBref"""
    try:
        # Criar scraper
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            }
        )
        
        # Fazer requisição
        time.sleep(2)
        response = scraper.get(url_base, timeout=30)
        response.raise_for_status()
        
        # Limpar comentários HTML
        html_limpo = limpar_comentarios_html(response.text)
        soup = BeautifulSoup(html_limpo, 'html.parser')
        
        # Normalizar competição
        competicao_norm = normalizar_texto(competicao)
        
        # Procurar tabela
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
        
        # Processar dados
        dados = []
        competicoes_encontradas = set()
        
        for linha in tbody.find_all('tr'):
            if len(dados) >= 15:
                break
            
            # Buscar competição
            comp_cell = linha.find('td', {'data-stat': 'comp'})
            if not comp_cell:
                continue
            
            comp_text = comp_cell.get_text(strip=True)
            comp_norm = normalizar_texto(comp_text)
            competicoes_encontradas.add(comp_text)
            
            # Filtrar por competição
            if competicao_norm not in comp_norm:
                continue
            
            # Buscar dados
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
            
            # Processar local
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
        return None, f"Erro: {str(e)}"


# Interface principal
st.title("⚽ Bot de Análise FBref - Expected Goals (xG)")
st.markdown("---")

# Carregar times
times_salvos = carregar_times()

# Sidebar para configurações
with st.sidebar:
    st.header("⚙️ Configurações")
    
    # Modo de operação
    modo = st.radio(
        "Escolha o modo:",
        ["📋 Selecionar Time Salvo", "➕ Adicionar Novo Time", "🗑️ Gerenciar Times"]
    )
    
    st.markdown("---")
    st.markdown("### 📊 Times Cadastrados")
    st.info(f"Total: **{len(times_salvos)}** times")

# Área principal
if modo == "📋 Selecionar Time Salvo":
    st.header("📋 Busca Rápida")
    
    if not times_salvos:
        st.warning("⚠️ Nenhum time cadastrado ainda. Use 'Adicionar Novo Time' para começar!")
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            time_selecionado = st.selectbox(
                "🏆 Selecione o time:",
                options=sorted(times_salvos.keys()),
                help="Escolha um time da lista"
            )
        
        with col2:
            competicao = st.text_input(
                "🏅 Competição:",
                placeholder="Ex: Serie A, Premier League, Bundesliga",
                help="Digite o nome da competição (ou parte dele)"
            )
        
        if st.button("🔍 Buscar Dados", type="primary", use_container_width=True):
            if not competicao:
                st.error("❌ Por favor, digite a competição!")
            else:
                url = times_salvos[time_selecionado]
                
                with st.spinner(f"🔄 Buscando dados de {time_selecionado} na {competicao}..."):
                    dados, erro = buscar_dados_fbref(url, time_selecionado, competicao)
                
                if erro:
                    st.error(f"❌ {erro}")
                else:
                    st.success(f"✅ {len(dados)} jogo(s) encontrado(s)!")
                    
                    # Criar DataFrame
                    df = pd.DataFrame(dados)
                    
                    # Exibir tabela
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    
                    # Estatísticas rápidas
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
                    
                    # Download CSV
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv,
                        file_name=f"{time_selecionado}_{competicao}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )

elif modo == "➕ Adicionar Novo Time":  # Adicionar Novo Time
    st.header("➕ Adicionar Novo Time")
    
    col1, col2 = st.columns(2)
    
    with col1:
        novo_nome = st.text_input(
            "📝 Nome do Time:",
            placeholder="Ex: Corinthians",
            help="Digite o nome do time"
        )
    
    with col2:
        nova_url = st.text_input(
            "🔗 URL do FBref:",
            placeholder="https://fbref.com/en/squads/.../Team-Stats",
            help="Cole a URL da página do time no FBref"
        )
    
    if st.button("💾 Salvar Time", type="primary", use_container_width=True):
        if not novo_nome or not nova_url:
            st.error("❌ Preencha todos os campos!")
        elif novo_nome in times_salvos:
            st.warning(f"⚠️ O time '{novo_nome}' já existe!")
        else:
            times_salvos[novo_nome] = nova_url
            salvar_times(times_salvos)
            st.success(f"✅ Time '{novo_nome}' adicionado com sucesso!")
            st.balloons()
            time.sleep(1)
            st.rerun()

# Nova seção: Gerenciar Times
else:  # modo == "🗑️ Gerenciar Times"
    st.header("🗑️ Gerenciar Times")
    
    if not times_salvos:
        st.warning("⚠️ Nenhum time cadastrado ainda.")
    else:
        st.info(f"📋 Você tem **{len(times_salvos)}** times cadastrados")
        
        # Lista de times para excluir
        st.markdown("### Selecione os times para excluir:")
        
        times_para_excluir = []
        
        # Criar checkboxes para cada time
        for i, (nome_time, url_time) in enumerate(sorted(times_salvos.items())):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                if st.checkbox(f"🏆 {nome_time}", key=f"check_{i}"):
                    times_para_excluir.append(nome_time)
            
            with col2:
                st.caption(f"[Link]({url_time})")
        
        # Botão de excluir
        if times_para_excluir:
            st.markdown("---")
            st.warning(f"⚠️ Você vai excluir **{len(times_para_excluir)}** time(s)")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🗑️ Confirmar Exclusão", type="primary", use_container_width=True):
                    for time_nome in times_para_excluir:
                        del times_salvos[time_nome]
                    
                    salvar_times(times_salvos)
                    st.success(f"✅ {len(times_para_excluir)} time(s) excluído(s) com sucesso!")
                    time.sleep(1)
                    st.rerun()
            
            with col2:
                if st.button("❌ Cancelar", use_container_width=True):
                    st.rerun()
        else:
            st.info("👆 Marque os times que deseja excluir")

# Rodapé
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center'>
        <p>🤖 Bot de Análise FBref | Desenvolvido com ❤️ usando Streamlit</p>
    </div>
    """,
    unsafe_allow_html=True
)
