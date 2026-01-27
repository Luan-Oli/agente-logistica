import streamlit as st
import pandas as pd
import time
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

st.set_page_config(page_title="Agente Logística SENAI", layout="wide")
st.title("🤖 Agente de Logística SENAI")

URL_CSV = "https://sesirs-my.sharepoint.com/:x:/g/personal/luan_oliveira_senairs_org_br/Documents/Automa%C3%A7%C3%A3o/ponte_dados.csv?download=1"

def processar():
    st.info("⚡ Acessando dados no SharePoint...")
    try:
        # 'latin1' e 'on_bad_lines' protegem contra erros de formatação
        df = pd.read_csv(URL_CSV, encoding='latin1', on_bad_lines='skip')
        
        if df.empty:
            st.warning("Arquivo vazio ou em atualização.")
            return

        geolocator = Nominatim(user_agent="agente_senai_v9_final", timeout=20)
        cidade = str(df.iloc[0]['Cidade_Demanda']).strip()
        
        st.subheader(f"📍 Destino: {cidade}")
        loc_dest = geolocator.geocode(f"{cidade}, RS, Brasil")

        with st.spinner("Calculando melhor logística..."):
            def calc(row):
                time.sleep(1)
                l = geolocator.geocode(f"{row['Unidade']}, RS, Brasil")
                return geodesic((loc_dest.latitude, loc_dest.longitude), (l.latitude, l.longitude)).km if l else 9999
            
            df['KM'] = df.apply(calc, axis=1)
            vencedor = df.sort_values(by='KM').iloc[0]

        st.success(f"🏆 Sugestão: **{vencedor['Consultor']}** ({vencedor['KM']:.1f} km)")
        st.balloons()
    except Exception as e:
        st.error(f"Erro ao ler dados: {e}")

if st.button("VERIFICAR NOVAS DEMANDAS", type="primary"):
    processar()

st.markdown("---") 
st.subheader("📋 Dados Atuais")
try:
    st.dataframe(pd.read_csv(URL_CSV, encoding='latin1', on_bad_lines='skip'), use_container_width=True)
except:
    st.caption("Aguardando sincronização...")
