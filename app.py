import streamlit as st
import json
import pandas as pd
from pathlib import Path
import asyncio
import aiohttp
from datetime import datetime

try:
    from understat import Understat
except ImportError:
    st.error("❌ Biblioteca 'understat' não instalada. Verificando requirements.txt...")
    st.stop()

# Configuração da página
st.set_page_config(
    page_title="Bot Understat - Análise de xG",
    page_icon="⚽",
    layout="wide"
)

# Arquivo de times salvos
TIMES_FILE = Path("times_salvos.json")

# Mapeamento de ligas
LIGAS_DISPONIVEIS = {
    "Premier League": "EPL",
    "La Liga": "La_liga",
    "Bundesliga": "Bundesliga",
    "Serie A": "Serie_A",
    "Ligue 1": "Ligue_1",
    "Russian Premier League": "RFPL"
}


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


def normalizar_nome_time(nome):
    """Normaliza nome do time para comparação"""
    return nome.lower().strip().replace(' ', '_')


async def buscar_dados_understat(nome_time, liga_code, temporada):
    """Busca dados do Understat usando API"""
    try:
        async with aiohttp.ClientSession() as session:
            understat = Understat(session)
            
            # Buscar times da liga
            teams = await understat.get_league_teams(liga_code, temporada)
            
            # Encontrar o time
            team_id = None
            team_name_real = None
            nome_normalizado = normalizar_nome_time(nome_time)
            
            for team in teams:
                if normalizar_nome_time(team['title']) == nome_normalizado:
                    team_id = team['id']
                    team_name_real = team['title']
                    break
            
            if not team_id:
                times_disponiveis = [t['title'] for t in teams]
                return None, f"❌ Time '{nome_time}' não encontrado.\n\n📋 Times disponíveis:\n" + "\n".join([f"• {t}" for t in sorted(times_disponiveis)])
            
            # Buscar jogos do time
            matches = await understat.get_team_results(
                team_name_real.replace(' ', '_'),
                temporada
            )
            
            # Processar dados
            dados = []
            for match in matches[:15]:  # Últimos 15 jogos
                # Determinar se é casa ou fora
                is_home = match['side'] == 'h'
                local = 'casa' if is_home else 'fora'
                
                # xG feitos e sofridos
                if is_home:
                    xg_feitos = match['xG']
                    xg_sofridos = match['xGA']
                else:
                    xg_feitos = match['xG']
                    xg_sofridos = match['xGA']
                
                dados.append({
                    'time': team_name_real,
                    'local': local,
                    'xg_feitos': f"{float(xg_feitos):.2f}",
                    'xg_sofridos': f"{float(xg_sofridos):.2f}"
                })
            
            if not dados:
                return None, f"❌ Nenhum jogo encontrado para {team_name_real} na temporada {temporada}/{int(temporada)+1}"
            
            return dados, None
            
    except Exception as e:
        return None, f"❌ Erro ao buscar dados: {str(e)}"


def executar_busca_async(nome_time, liga_code, temporada):
    """Wrapper para executar função async"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(buscar_dados_understat(nome_time, liga_code, temporada))
    except Exception as e:
        return None, f"❌ Erro: {str(e)}"


# Interface principal
st.title("⚽ Bot Understat - Análise de xG")
st.markdown("---")

# Aviso sobre cobertura
st.info("📊 **Cobertura:** Premier League, La Liga, Bundesliga, Serie A, Ligue 1, Russian PL (desde 2014/15)")

# Carregar times salvos
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
    
    st.markdown("---")
    st.markdown("### 🌍 Ligas Disponíveis")
    for liga in LIGAS_DISPONIVEIS.keys():
        st.caption(f"• {liga}")

# Área principal
if modo == "🔍 Buscar Dados":
    st.header("🔍 Buscar Dados de xG")
    
    if not times_salvos:
        st.warning("⚠️ Nenhum time cadastrado. Use 'Adicionar Time' primeiro!")
        
        st.markdown("---")
        st.markdown("### 💡 Como adicionar times:")
        st.markdown("""
        1. Vá em **➕ Adicionar Time**
        2. Digite o **nome exato** do time (ex: Manchester United, Liverpool, Barcelona)
        3. Selecione a **liga**
        4. Salve!
        """)
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            time_selecionado = st.selectbox(
                "🏆 Selecione o time:",
                options=sorted(times_salvos.keys()),
                help="Escolha um time da lista"
            )
        
        with col2:
            # Pegar a liga do time selecionado
            liga_time = times_salvos[time_selecionado]['liga']
            st.text_input(
                "🏅 Liga:",
                value=liga_time,
                disabled=True,
                help="Liga do time selecionado"
            )
        
        # Seletor de temporada
        ano_atual = datetime.now().year
        temporadas = list(range(2014, ano_atual + 1))
        temporada_default = ano_atual - 1 if datetime.now().month < 8 else ano_atual
        
        temporada = st.selectbox(
            "📅 Temporada:",
            options=temporadas,
            index=temporadas.index(temporada_default),
            help=f"Selecione o ano de INÍCIO da temporada (ex: 2023 = temporada 2023/24)"
        )
        
        if st.button("🔍 Buscar Dados", type="primary", use_container_width=True):
            liga_code = LIGAS_DISPONIVEIS[liga_time]
            nome_time = times_salvos[time_selecionado]['nome']
            
            with st.spinner(f"🔄 Buscando dados de {nome_time} na {liga_time} ({temporada}/{temporada+1})..."):
                dados, erro = executar_busca_async(nome_time, liga_code, temporada)
            
            if erro:
                st.error(erro)
            else:
                st.success(f"✅ {len(dados)} jogo(s) encontrado(s)!")
                
                # Criar DataFrame
                df = pd.DataFrame(dados)
                
                # Exibir tabela
                st.subheader("📊 Tabela de Dados")
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
                
                st.markdown("---")
                
                # ÁREA DE CÓPIA CSV
                st.subheader("📋 Dados em Formato CSV")
                st.caption("👇 Formato: time, local, xg_feitos, xg_sofridos")
                
                # Gerar CSV
                csv_text = df.to_csv(index=False, sep=',')
                
                # Exibir em text_area
                st.text_area(
                    label="Copie os dados (Ctrl+A → Ctrl+C):",
                    value=csv_text,
                    height=300,
                    help="Selecione tudo e copie para usar em Excel, Google Sheets, etc."
                )
                
                st.info("💡 **Dica:** Cole direto no Excel ou Google Sheets!")
                
                # Botão de download
                st.download_button(
                    label="📥 Download CSV",
                    data=csv_text,
                    file_name=f"{nome_time}_{liga_time}_{temporada}.csv",
                    mime="text/csv",
                    use_container_width=True
                )

elif modo == "➕ Adicionar Time":
    st.header("➕ Adicionar Novo Time")
    
    st.info("💡 **Dica:** Digite o nome EXATO do time em inglês (ex: Manchester United, Barcelona, Bayern Munich)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        novo_nome_display = st.text_input(
            "📝 Nome do Time (para exibir):",
            placeholder="Ex: Manchester United",
            help="Nome que aparecerá na lista"
        )
        
        novo_nome_busca = st.text_input(
            "🔍 Nome do Time (para busca):",
            value=novo_nome_display,
            placeholder="Ex: Manchester_United",
            help="Nome usado na busca (geralmente igual, mas com _ no lugar de espaços)"
        )
    
    with col2:
        nova_liga = st.selectbox(
            "🏅 Liga:",
            options=list(LIGAS_DISPONIVEIS.keys()),
            help="Selecione a liga do time"
        )
    
    if st.button("💾 Salvar Time", type="primary", use_container_width=True):
        if not novo_nome_display or not novo_nome_busca:
            st.error("❌ Preencha todos os campos!")
        elif novo_nome_display in times_salvos:
            st.warning(f"⚠️ O time '{novo_nome_display}' já existe!")
        else:
            times_salvos[novo_nome_display] = {
                'nome': novo_nome_busca,
                'liga': nova_liga
            }
            salvar_times(times_salvos)
            st.success(f"✅ Time '{novo_nome_display}' adicionado com sucesso!")
            st.balloons()
            st.rerun()

else:  # Gerenciar Times
    st.header("🗑️ Gerenciar Times")
    
    if not times_salvos:
        st.warning("⚠️ Nenhum time cadastrado.")
    else:
        st.info(f"📋 Você tem **{len(times_salvos)}** times cadastrados")
        
        st.markdown("### Selecione os times para excluir:")
        
        times_para_excluir = []
        
        for i, (nome_display, info) in enumerate(sorted(times_salvos.items())):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                if st.checkbox(f"🏆 {nome_display}", key=f"check_{i}"):
                    times_para_excluir.append(nome_display)
            
            with col2:
                st.caption(f"{info['liga']}")
        
        if times_para_excluir:
            st.markdown("---")
            st.warning(f"⚠️ Excluir **{len(times_para_excluir)}** time(s)?")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🗑️ Confirmar", type="primary", use_container_width=True):
                    for time_nome in times_para_excluir:
                        del times_salvos[time_nome]
                    
                    salvar_times(times_salvos)
                    st.success(f"✅ {len(times_para_excluir)} time(s) excluído(s)!")
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
        <p>🤖 Bot Understat | Dados confiáveis de xG</p>
        <p style='font-size: 12px; color: gray;'>📊 Cobertura: 6 ligas europeias desde 2014/15</p>
    </div>
    """,
    unsafe_allow_html=True
)
