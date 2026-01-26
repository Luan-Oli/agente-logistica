import streamlit as st
import pandas as pd
import time
import os
from datetime import datetime
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# --- 1. CONFIGURAÇÃO DA PÁGINA (Sempre primeiro) ---
st.set_page_config(page_title="Agente de Logística SENAI", page_icon="🤖", layout="wide")

# --- 2. DEFINIÇÃO DE VARIÁVEIS (Para evitar o NameError) ---
PASTA_AUTO = r"C:\Users\luan.oliveira\OneDrive - SISTEMA FIERGS\Automação"
ARQUIVO_ENTRADA = os.path.join(PASTA_AUTO, "ponte_dados.csv")
ARQUIVO_HISTORICO = os.path.join(PASTA_AUTO, "historico_alocacoes.csv")
ARQUIVO_RESULTADO = os.path.join(PASTA_AUTO, "resultado_alocacao.csv")

# --- 3. FUNÇÕES DE APOIO ---
def registrar_historico(vencedor, cliente, cidade):
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
    resultado = {
        'Consultor': [vencedor['Consultor']],
        'Cliente': [cliente],
        'Cidade': [cidade],
        'Distancia': [f"{vencedor['Distancia_KM']:.1f} km"],
        'Email_Notificacao': ["luan.oliveira@senairs.org.br"]
    }
    pd.DataFrame(resultado).to_csv(ARQUIVO_RESULTADO, index=False, encoding='utf-8-sig')

def processar_logistica():
    st.toast("⚡ Nova demanda detectada! Iniciando cálculos...")
    time.sleep(5) 
    try:
        df = pd.read_csv(ARQUIVO_ENTRADA)
        geolocator = Nominatim(user_agent="agente_senai_v8", timeout=20)
        cidade_alvo = str(df.iloc[0]['Cidade_Demanda']).strip()
        cliente = str(df.iloc[0]['Empresa']).strip()
        coord_dest = geolocator.geocode(f"{cidade_alvo}, RS, Brasil")
        
        def calc_km(row):
            time.sleep(1)
            loc = geolocator.geocode(f"{row['Unidade']}, RS, Brasil")
            return geodesic((coord_dest.latitude, coord_dest.longitude), (loc.latitude, loc.longitude)).km if loc else 9999

        df['Distancia_KM'] = df.apply(calc_km, axis=1)
        df['Folga_Real'] = 160 - pd.to_numeric(df['Horas_Mes'], errors='coerce').fillna(160)
        vencedor = df.sort_values(by=['Distancia_KM', 'Folga_Real'], ascending=[True, False]).iloc[0]
        
        registrar_historico(vencedor, cliente, cidade_alvo)
        gerar_saida_power_automate(vencedor, cliente, cidade_alvo)
        return True
    except Exception as e:
        st.error(f"❌ Erro no processamento: {e}")
        return False

# --- 4. INTERFACE DO DASHBOARD ---
st.title("🤖 Painel de Controle: Agente de Logística")
st.markdown(f"**Vigiando pasta:** `{PASTA_AUTO}`") # Agora PASTA_AUTO já foi definida acima!

if 'rodando' not in st.session_state:
    st.session_state.rodando = False
if 'ultima_mod' not in st.session_state:
    st.session_state.ultima_mod = 0

with st.sidebar:
    st.header("⚙️ Configurações")
    if st.button("LIGAR" if not st.session_state.rodando else "DESLIGAR", type="primary", use_container_width=True):
        st.session_state.rodando = not st.session_state.rodando
        st.rerun()
    
    status_cor = "green" if st.session_state.rodando else "red"
    st.markdown(f"### Status: :{status_cor}[{'ATIVO' if st.session_state.rodando else 'DESATIVADO'}]")

status_msg = st.empty()
log_msg = st.empty()

if st.session_state.rodando:
    status_msg.info("👁️ O Agente está monitorando mudanças no OneDrive...")
    if os.path.exists(ARQUIVO_ENTRADA):
        mod_atual = os.path.getmtime(ARQUIVO_ENTRADA)
        log_msg.caption(f"Última verificação: {datetime.now().strftime('%H:%M:%S')}")
        if mod_atual != st.session_state.ultima_mod:
            with st.spinner("📦 Processando nova demanda..."):
                if processar_logistica():
                    st.session_state.ultima_mod = mod_atual
                    st.success("✅ Alocação concluída e e-mail disparado via Power Automate!")
                    st.balloons()
    time.sleep(5)
    st.rerun()
else:
    status_msg.warning("💤 O Agente está pausado. Ligue-o para iniciar.")

st.markdown("---")
st.subheader("📊 Histórico de Alocações")
if os.path.exists(ARQUIVO_HISTORICO):
    try:
        # Adicionamos 'on_bad_lines' para ignorar linhas com erro em vez de travar o site
        df_hist = pd.read_csv(ARQUIVO_HISTORICO, on_bad_lines='skip', encoding='utf-8-sig')
        st.dataframe(df_hist.tail(10), use_container_width=True)
    except Exception as e:
        st.warning("⚠️ O arquivo de histórico está sendo atualizado ou contém erros de formatação.")
else:
    st.info("Aguardando a primeira alocação para gerar o histórico.")
