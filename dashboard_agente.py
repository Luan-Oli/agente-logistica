import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# Configuração básica
st.set_page_config(page_title="Agente de Logística SENAI", layout="wide")
st.title("🤖 Agente de Logística SENAI")
st.markdown("Este painel monitora o SharePoint e calcula a melhor logística.")

# Link estável do seu SharePoint (Download Direto)
URL_CSV = "https://sesirs-my.sharepoint.com/:x:/g/personal/luan_oliveira_senairs_org_br/Documents/Automa%C3%A7%C3%A3o/ponte_dados.csv?download=1"

def processar():
    st.toast("⚡ Acessando dados...")
    try:
        # 'latin1' resolve os acentos e 'on_bad_lines' evita o ParserError
        df = pd.read_csv(URL_CSV, encoding='latin1', on_bad_lines='skip')
        
        if df.empty:
            st.warning("O arquivo no SharePoint está vazio.")
            return

        geolocator = Nominatim(user_agent="agente_senai_v8", timeout=20)
        cidade_alvo = str(df.iloc[0]['Cidade_Demanda']).strip()
        cliente = str(df.iloc[0]['Empresa']).strip()
        
        st.info(f"Calculando rota para: **{cliente}** em **{cidade_alvo}**")
        
        loc_alvo = geolocator.geocode(f"{cidade_alvo}, RS, Brasil")
        if not loc_alvo:
            st.error(f"Cidade não encontrada: {cidade_alvo}")
            return

        def get_dist(row):
            time.sleep(1) # Respeita limite da API
            loc = geolocator.geocode(f"{row['Unidade']}, RS, Brasil")
            return geodesic((loc_alvo.latitude, loc_alvo.longitude), (loc.latitude, loc.longitude)).km if loc else 9999

        df['KM'] = df.apply(get_dist, axis=1)
        vencedor = df.sort_values(by='KM').iloc[0]

        st.success(f"🏆 Melhor opção: **{vencedor['Consultor']}** ({vencedor['Unidade']})")
        st.metric("Distância estimada", f"{vencedor['KM']:.1f} km")
        st.balloons()

    except Exception as e:
        st.error(f"Erro ao ler SharePoint: {e}")

# Botão de comando
if st.button("VERIFICAR NOVAS DEMANDAS", type="primary"):
    processar()

st.markdown("---") # Substituto seguro para o st.divider()
st.subheader("📋 Visualização dos Dados Atuais")
try:
    preview = pd.read_csv(URL_CSV, encoding='latin1', on_bad_lines='skip')
    st.dataframe(preview, use_container_width=True)
except:
    st.write("Aguardando sincronização do SharePoint...")
