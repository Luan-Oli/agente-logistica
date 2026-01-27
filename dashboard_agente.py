import streamlit as st
import pandas as pd
import time
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

st.set_page_config(page_title="Agente Logística SENAI", layout="wide")
st.title("🤖 Agente de Logística SENAI")

# Link estável do SharePoint
# Este link é público e não exige senha, ideal para testarmos a lógica agora
URL_CSV = "https://raw.githubusercontent.com/Luan-Oli/ponte_dados.csv/refs/heads/main/ponte_dados.csv"

def processar():
    st.info("⚡ Sincronizando com SharePoint...")
    try:
        # 'latin1' corrige acentos e 'on_bad_lines' evita o ParserError
        df = pd.read_csv(URL_CSV, encoding='latin1', on_bad_lines='skip', sep=',')
        
        if df.empty:
            st.warning("Aguardando novos dados formatados...")
            return

        geolocator = Nominatim(user_agent="agente_senai_v9_final", timeout=20)
        cidade = str(df.iloc[0]['Cidade_Demanda']).strip()
        loc_dest = geolocator.geocode(f"{cidade}, RS, Brasil")

        with st.spinner("📦 Calculando melhor logística..."):
            def calc_km(row):
                time.sleep(1)
                l = geolocator.geocode(f"{row['Unidade']}, RS, Brasil")
                return geodesic((loc_dest.latitude, loc_dest.longitude), (l.latitude, l.longitude)).km if l else 9999
            
            df['KM'] = df.apply(calc_km, axis=1)
            vencedor = df.sort_values(by='KM').iloc[0]

        st.success(f"🏆 Sugestão: **{vencedor['Consultor']}** ({vencedor['KM']:.1f} km)")
        st.balloons()
    except Exception as e:
        st.error(f"Erro ao ler dados: {e}")

if st.button("VERIFICAR NOVAS DEMANDAS", type="primary"):
    processar()

st.markdown("---") 
st.subheader("📋 Dados Atuais (SharePoint)")
try:
    st.dataframe(pd.read_csv(URL_CSV, encoding='latin1', on_bad_lines='skip'), use_container_width=True)
except:
    st.caption("Sincronizando dados...")



