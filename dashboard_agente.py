import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Agente de Logística SENAI", page_icon="🤖", layout="wide")

# --- LINK DO SHAREPOINT (DOWNLOAD DIRETO) ---
# Link convertido para garantir que o Streamlit Cloud acesse os dados
URL_CSV = "https://sesirs-my.sharepoint.com/:x:/g/personal/luan_oliveira_senairs_org_br/Documents/Automa%C3%A7%C3%A3o/ponte_dados.csv?download=1"

# Arquivos de saída (salvos temporariamente no servidor cloud)
ARQUIVO_HISTORICO = "historico_alocacoes.csv"

def processar_logistica():
    st.toast("⚡ Acessando dados no SharePoint...")
    try:
        # PROTEÇÃO: 'latin1' resolve acentos e 'on_bad_lines' evita erros de 'tripa' de texto
        df = pd.read_csv(URL_CSV, encoding='latin1', on_bad_lines='skip', sep=',')
        
        if df.empty:
            st.error("⚠️ O arquivo ponte_dados.csv parece estar vazio.")
            return

        geolocator = Nominatim(user_agent="agente_senai_v8_5", timeout=20)
        
        # Pega a demanda da primeira linha
        cidade_alvo = str(df.iloc[0]['Cidade_Demanda']).strip()
        cliente = str(df.iloc[0]['Empresa']).strip()
        
        st.write(f"🔍 Buscando consultores para: **{cliente}** em **{cidade_alvo}**")
        
        coord_dest = geolocator.geocode(f"{cidade_alvo}, RS, Brasil")
        if not coord_dest:
            st.error(f"❌ Não localizei a cidade: {cidade_alvo}")
            return

        def calc_km(row):
            time.sleep(1) # Respeita o limite da API
            loc = geolocator.geocode(f"{row['Unidade']}, RS, Brasil")
            return geodesic((coord_dest.latitude, coord_dest.longitude), (loc.latitude, loc.longitude)).km if loc else 9999

        with st.status("🗺️ Calculando distâncias geográficas..."):
            df['Distancia_KM'] = df.apply(calc_km, axis=1)
            # Lógica de folga baseada em 160h mensais
            df['Folga_Real'] = 160 - pd.to_numeric(df['Horas_Mes'], errors='coerce').fillna(160)
            vencedor = df.sort_values(by=['Distancia_KM', 'Folga_Real'], ascending=[True, False]).iloc[0]

        # EXIBIÇÃO DO RESULTADO
        st.success(f"🏆 Consultor ideal encontrado: **{vencedor['Consultor']}**")
        col1, col2, col3 = st.columns(3)
        col1.metric("Distância", f"{vencedor['Distancia_KM']:.1f} km")
        col2.metric("Unidade Base", vencedor['Unidade'])
        col3.metric("Folga Mensal", f"{vencedor['Folga_Real']:.1f} h")

        # Salva histórico na sessão atual
        registrar_local(vencedor, cliente)
        st.balloons()

    except Exception as e:
        st.error(f"❌ Erro ao processar: {e}")
        st.info("Dica: Verifique se o Power Automate adicionou o 'Enter' ao final do arquivo.")

def registrar_local(vencedor, cliente):
    dados = {'Data': [datetime.now().strftime('%d/%m/%Y %H:%M')], 'Cliente': [cliente], 'Vencedor': [vencedor['Consultor']]}
    df_h = pd.DataFrame(dados)
    df_h.to_csv(ARQUIVO_HISTORICO, mode='a', index=False, header=not os.path.exists(ARQUIVO_HISTORICO))

# --- INTERFACE ---
st.title("🤖 Painel de Controle: Agente de Logística")
st.info("Este painel monitora o SharePoint e calcula a melhor logística para suas demandas.")

with st.sidebar:
    st.header("⚙️ Ações")
    if st.button("VERIFICAR NOVAS DEMANDAS", type="primary", use_container_width=True):
        processar_logistica()

st.divider()
st.subheader("📊 Histórico desta Sessão")
if os.path.exists(ARQUIVO_HISTORICO):
    st.dataframe(pd.read_csv(ARQUIVO_HISTORICO), use_container_width=True)
else:
    st.caption("Nenhuma alocação realizada ainda.")
