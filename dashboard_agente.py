import streamlit as st
import pandas as pd
import time
import os
from datetime import datetime
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Agente de Logística SENAI", page_icon="🤖", layout="wide")

# --- CONFIGURAÇÕES DE CAMINHOS (ONEDRIVE LOCAL) ---
# Caminhos baseados na estrutura de pastas detectada
PASTA_AUTO = r"C:\Users\luan.oliveira\OneDrive - SISTEMA FIERGS\Automação"
ARQUIVO_ENTRADA = os.path.join(PASTA_AUTO, "ponte_dados.csv")
ARQUIVO_HISTORICO = os.path.join(PASTA_AUTO, "historico_alocacoes.csv")
ARQUIVO_RESULTADO = os.path.join(PASTA_AUTO, "resultado_alocacao.csv")

# --- FUNÇÕES DE APOIO ---
def registrar_historico(vencedor, cliente, cidade):
    """Salva a alocação no arquivo de histórico permanente."""
    dados = {
        'Data': [datetime.now().strftime('%d/%m/%Y %H:%M')],
        'Cliente': [cliente],
        'Consultor': [vencedor['Consultor']],
        'KM': [round(vencedor['Distancia_KM'], 2)]
    }
    df_h = pd.DataFrame(dados)
    header = not os.path.exists(ARQUIVO_HISTORICO)
    df_h.to_csv(ARQUIVO_HISTORICO, mode='a', index=False, header=header, encoding='utf-8-sig')

def gerar_saida_power_automate(vencedor, cliente, cidade):
    """Gera o CSV que servirá de gatilho para o e-mail no Power Automate."""
    resultado = {
        'Consultor': [vencedor['Consultor']],
        'Cliente': [cliente],
        'Cidade': [cidade],
        'Distancia': [f"{vencedor['Distancia_KM']:.1f} km"],
        'Email_Notificacao': ["luan.oliveira@senairs.org.br"]
    }
    pd.DataFrame(resultado).to_csv(ARQUIVO_RESULTADO, index=False, encoding='utf-8-sig')

def processar_logistica():
    """O 'Cérebro' do robô: calcula distâncias e seleciona o consultor."""
    st.toast("⚡ Nova demanda detectada! Iniciando cálculos...")
    time.sleep(10) # Tempo para o OneDrive sincronizar o download

    try:
        df = pd.read_csv(ARQUIVO_ENTRADA)
        geolocator = Nominatim(user_agent="agente_senai_v8", timeout=20)
        
        cidade_alvo = str(df.iloc[0]['Cidade_Demanda']).strip()
        cliente = str(df.iloc[0]['Empresa']).strip()
        coord_dest = geolocator.geocode(f"{cidade_alvo}, RS, Brasil")
        
        if not coord_dest:
            st.error(f"❌ Não foi possível localizar a cidade: {cidade_alvo}")
            return

        def calc_km(row):
            time.sleep(1) # Respeita o limite do servidor de mapas
            loc = geolocator.geocode(f"{row['Unidade']}, RS, Brasil")
            return geodesic((coord_dest.latitude, coord_dest.longitude), (loc.latitude, loc.longitude)).km if loc else 9999

        df['Distancia_KM'] = df.apply(calc_km, axis=1)
        # Lógica: 160h mensais menos as horas já ocupadas
        df['Folga_Real'] = 160 - pd.to_numeric(df['Horas_Mes'], errors='coerce').fillna(160)
        
        # Critério: Menor distância e, em caso de empate, maior folga
        vencedor = df.sort_values(by=['Distancia_KM', 'Folga_Real'], ascending=[True, False]).iloc[0]
        
        # Ações Finais
        registrar_historico(vencedor, cliente, cidade_alvo)
        gerar_saida_power_automate(vencedor, cliente, cidade_alvo)
        
        st.success(f"🏆 Sucesso! {vencedor['Consultor']} alocado para {cliente}.")
        return True
    except Exception as e:
        st.error(f"❌ Erro no processamento: {e}")
        return False

# --- INTERFACE STREAMLIT ---
st.title("🤖 Painel de Controle: Agente de Logística")
st.markdown(f"**Vigiando pasta:** `{PASTA_AUTO}`")
st.markdown("---")

if 'rodando' not in st.session_state:
    st.session_state.rodando = False
if 'ultima_mod' not in st.session_state:
    st.session_state.ultima_mod = 0

with st.sidebar:
    st.header("⚙️ Configurações")
    if st.button("LIGAR AGENTE" if not st.session_state.rodando else "DESLIGAR AGENTE", type="primary"):
        st.session_state.rodando = not st.session_state.rodando
    
    status_cor = "green" if st.session_state.rodando else "red"
    st.markdown(f"### Status: :{status_cor}[{'ATIVO' if st.session_state.rodando else 'DESATIVADO'}]")

# Lógica de Monitoramento (Polling)
if st.session_state.rodando:
    if os.path.exists(ARQUIVO_ENTRADA):
        mod_atual = os.path.getmtime(ARQUIVO_ENTRADA)
        
        if mod_atual != st.session_state.ultima_mod:
            if processar_logistica():
                st.session_state.ultima_mod = mod_atual
    
    time.sleep(10)
    st.rerun()

# Exibição do Histórico
st.subheader("📊 Últimas Alocações Registradas")
if os.path.exists(ARQUIVO_HISTORICO):
    df_visualizacao = pd.read_csv(ARQUIVO_HISTORICO)
    st.dataframe(df_visualizacao.tail(10), use_container_width=True)
else:
    st.info("Aguardando a primeira alocação para gerar o histórico.")
