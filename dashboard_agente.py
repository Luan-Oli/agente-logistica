import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Agente de Logística SENAI - Cloud", page_icon="🤖", layout="wide")

# --- LINKS E ARQUIVOS ---
# Link direto do seu SharePoint (ajustado para download=1)
URL_CSV_NUVEM = "https://sesirs-my.sharepoint.com/:x:/g/personal/luan_oliveira_senairs_org_br/Documents/Automa%C3%A7%C3%A3o/ponte_dados.csv?download=1"
ARQUIVO_HISTORICO = "historico_alocacoes.csv"

# --- FUNÇÕES DE APOIO ---
def processar_logistica():
    """Lógica principal com proteção contra erros de formatação."""
    st.toast("⚡ Acessando dados no SharePoint...")
    try:
        # 'latin1' corrige erros de acentos e 'on_bad_lines' evita o erro de 'tripa de texto'
        df = pd.read_csv(URL_CSV_NUVEM, encoding='latin1', on_bad_lines='skip')
        
        if df.empty:
            st.error("⚠️ O arquivo no SharePoint está vazio.")
            return False

        geolocator = Nominatim(user_agent="agente_senai_cloud_v8", timeout=20)
        
        # Extração de dados da primeira linha (demanda atual)
        cidade_alvo = str(df.iloc[0]['Cidade_Demanda']).strip()
        cliente = str(df.iloc[0]['Empresa']).strip()
        
        st.write(f"🔍 Localizando: **{cidade_alvo}** para o cliente **{cliente}**")
        
        coord_dest = geolocator.geocode(f"{cidade_alvo}, RS, Brasil")
        if not coord_dest:
            st.error(f"❌ Não foi possível geolocalizar a cidade: {cidade_alvo}")
            return False

        def calc_km(row):
            time.sleep(1) # Respeita o limite do servidor de mapas
            loc = geolocator.geocode(f"{row['Unidade']}, RS, Brasil")
            return geodesic((coord_dest.latitude, coord_dest.longitude), (loc.latitude, loc.longitude)).km if loc else 9999

        df['Distancia_KM'] = df.apply(calc_km, axis=1)
        df['Folga_Real'] = 160 - pd.to_numeric(df['Horas_Mes'], errors='coerce').fillna(160)
        
        # Critério de seleção: Menor distância e maior folga
        vencedor = df.sort_values(by=['Distancia_KM', 'Folga_Real'], ascending=[True, False]).iloc[0]
        
        # Salva o resultado no histórico da sessão
        salvar_historico_local(vencedor, cliente)
        
        st.success(f"🏆 Vencedor: {vencedor['Consultor']} ({vencedor['Distancia_KM']:.1f} km)")
        return True

    except Exception as e:
        st.error(f"❌ Erro de processamento: {e}")
        st.info("Dica: Verifique se o seu Power Automate está gerando o CSV com quebras de linha.")
        return False

def salvar_historico_local(vencedor, cliente):
    dados = {
        'Data': [datetime.now().strftime('%d/%m/%Y %H:%M')],
        'Cliente': [cliente],
        'Consultor': [vencedor['Consultor']],
        'Distancia': [round(vencedor['Distancia_KM'], 2)]
    }
    df_h = pd.DataFrame(dados)
    header = not os.path.exists(ARQUIVO_HISTORICO)
    df_h.to_csv(ARQUIVO_HISTORICO, mode='a', index=False, header=header, encoding='utf-8-sig')

# --- INTERFACE ---
st.title("🤖 Painel Cloud: Agente de Logística")
st.markdown("Este painel monitora sua planilha no SharePoint e calcula a melhor alocação.")

if 'ativo' not in st.session_state:
    st.session_state.ativo = False

with st.sidebar:
    st.header("⚙️ Configurações")
    if st.button("LIGAR AGENTE" if not st.session_state.ativo else "DESLIGAR AGENTE", type="primary"):
        st.session_state.ativo = not st.session_state.ativo
    
    status_cor = "green" if st.session_state.ativo else "red"
    st.markdown(f"Status: :{status_cor}[{'ONLINE' if st.session_state.ativo else 'OFFLINE'}]")

if st.session_state.ativo:
    st.info("👁️ O Agente está pronto para verificar novas demandas.")
    if st.button("VERIFICAR SHAREPOINT AGORA"):
        processar_logistica()
else:
    st.warning("💤 Agente pausado. Clique em LIGAR para monitorar.")

st.markdown("---")
st.subheader("📊 Últimas Alocações Registradas")
if os.path.exists(ARQUIVO_HISTORICO):
    # Proteção extra para o histórico não quebrar o site
    df_hist = pd.read_csv(ARQUIVO_HISTORICO, on_bad_lines='skip')
    st.dataframe(df_hist.tail(10), use_container_width=True)
else:
    st.info("Nenhuma alocação registrada nesta sessão.")
