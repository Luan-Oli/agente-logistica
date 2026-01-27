import streamlit as st
import pandas as pd
import time
import os
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

st.set_page_config(page_title="Agente Logística SENAI", layout="wide")
st.title("🤖 Agente de Logística SENAI")

# Link RAW do seu GitHub (O link que você já está usando e que funcionou na tabela!)
URL_CSV = "https://raw.githubusercontent.com/Luan-Oli/ponte_dados.csv/refs/heads/main/ponte_dados.csv"

def processar():
    st.info("⚡ Iniciando geolocalização...")
    try:
        # 'utf-8-sig' corrige o erro de 'Bento GonÃ§alves'
        df = pd.read_csv(URL_CSV, encoding='utf-8-sig', on_bad_lines='skip', sep=',')
        
        # Criamos um identificador único para você não ser bloqueado (Erro 403)
        identificador_unico = f"agente_luan_senai_{int(time.time())}"
        geolocator = Nominatim(user_agent=identificador_unico, timeout=20)
        
        cidade_alvo = str(df.iloc[0]['Cidade_Demanda']).strip()
        st.subheader(f"📍 Calculando rota para: {cidade_alvo}")
        
        loc_dest = geolocator.geocode(f"{cidade_alvo}, RS, Brasil")

        with st.spinner("Calculando distâncias..."):
            def calc(row):
                time.sleep(1.1) # Pausa para o mapa não nos bloquear novamente
                unidade = str(row['Unidade']).replace('Ã§', 'ç')
                l = geolocator.geocode(f"{unidade}, RS, Brasil")
                return geodesic((loc_dest.latitude, loc_dest.longitude), (l.latitude, l.longitude)).km if l else 9999
            
            df['KM'] = df.apply(calc, axis=1)
            vencedor = df.sort_values(by='KM').iloc[0]

        st.success(f"🏆 Melhor Consultor: **{vencedor['Consultor']}**")
        st.metric("Distância", f"{vencedor['KM']:.1f} km")
        st.balloons()
    except Exception as e:
        st.error(f"Erro no processamento: {e}")

# Botão principal
if st.button("VERIFICAR NOVAS DEMANDAS", type="primary"):
    processar()

st.markdown("---")
st.subheader("📋 Dados Atuais (Visualização)")
try:
    # Mostra a tabela que já está funcionando na sua imagem
    preview = pd.read_csv(URL_CSV, encoding='utf-8-sig', on_bad_lines='skip')
    st.dataframe(preview, use_container_width=True)
except:
    st.caption("Sincronizando dados...")

