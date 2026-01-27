import streamlit as st
import pandas as pd
import time
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# Configuração moderna da página
st.set_page_config(page_title="Agente Logística SENAI", layout="wide")
st.title("🤖 Agente de Logística SENAI")

# Link RAW do seu GitHub que funcionou perfeitamente
URL_CSV = "https://raw.githubusercontent.com/Luan-Oli/ponte_dados.csv/refs/heads/main/ponte_dados.csv"

def processar():
    st.info("⚡ Iniciando geolocalização...")
    try:
        # 'utf-8-sig' limpa os caracteres estranhos como 'Ã§'
        df = pd.read_csv(URL_CSV, encoding='utf-8-sig', on_bad_lines='skip')
        
        # Identificador único para evitar o erro 403
        geolocator = Nominatim(user_agent=f"senai_logistica_luan_{int(time.time())}", timeout=20)
        
        cidade_alvo = str(df.iloc[0]['Cidade_Demanda']).strip()
        st.subheader(f"📍 Calculando rota para: {cidade_alvo}")
        
        loc_dest = geolocator.geocode(f"{cidade_alvo}, RS, Brasil")

        with st.spinner("📦 Mapeando consultores disponíveis..."):
            def calc(row):
                time.sleep(1.2) # Pausa segura para o serviço de mapas
                unidade = str(row['Unidade'])
                l = geolocator.geocode(f"{unidade}, RS, Brasil")
                return geodesic((loc_dest.latitude, loc_dest.longitude), (l.latitude, l.longitude)).km if l else 9999
            
            df['KM'] = df.apply(calc, axis=1)
            vencedor = df.sort_values(by='KM').iloc[0]

        st.success(f"🏆 Melhor Consultor: **{vencedor['Consultor']}**")
        st.metric("Distância", f"{vencedor['KM']:.1f} km")
        st.balloons()
        
    except Exception as e:
        st.error(f"Erro no cálculo: {e}")

# Botão principal
if st.button("VERIFICAR NOVAS DEMANDAS", type="primary"):
    processar()

st.markdown("---")
st.subheader("📋 Dados Atuais (Visualização)")
try:
    # Ajustado para evitar o aviso 'use_container_width' dos logs
    preview = pd.read_csv(URL_CSV, encoding='utf-8-sig', on_bad_lines='skip')
    st.dataframe(preview)
except:
    st.caption("Sincronizando dados...")

