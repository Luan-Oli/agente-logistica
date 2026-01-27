import streamlit as st
import pandas as pd
import time
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# Configuração da página
st.set_page_config(page_title="Agente Logística SENAI", layout="wide")
st.title("🤖 Agente de Logística SENAI")

# Link estável do SharePoint (Certifique-se que é "Qualquer pessoa com o link")
URL_CSV = "https://sesirs-my.sharepoint.com/:x:/g/personal/luan_oliveira_senairs_org_br/Documents/Automa%C3%A7%C3%A3o/ponte_dados.csv?download=1"

def processar():
    # Usamos info() em vez de toast() para garantir compatibilidade
    status_placeholder = st.empty()
    status_placeholder.info("⚡ Acedendo aos dados no SharePoint...")
    
    try:
        # 'latin1' resolve acentos e 'on_bad_lines' ignora as linhas grudadas
        df = pd.read_csv(URL_CSV, encoding='latin1', on_bad_lines='skip')
        
        if df.empty:
            st.warning("O ficheiro está vazio ou ainda não foi atualizado.")
            return

        geolocator = Nominatim(user_agent="agente_senai_v8_7", timeout=20)
        
        # Pega a demanda da primeira linha
        cidade_alvo = str(df.iloc[0]['Cidade_Demanda']).strip()
        cliente = str(df.iloc[0]['Empresa']).strip()
        
        st.subheader(f"📍 Demanda: {cliente} ({cidade_alvo})")
        
        loc_destino = geolocator.geocode(f"{cidade_alvo}, RS, Brasil")
        if not loc_destino:
            st.error(f"Não consegui localizar a cidade: {cidade_alvo}")
            return

        def calcular(row):
            time.sleep(1) # Respeita a API de mapas
            loc_origem = geolocator.geocode(f"{row['Unidade']}, RS, Brasil")
            if loc_origem:
                return geodesic((loc_destino.latitude, loc_destino.longitude), (loc_origem.latitude, loc_origem.longitude)).km
            return 9999

        with st.spinner("Calculando a melhor logística..."):
            df['KM'] = df.apply(calcular, axis=1)
            vencedor = df.sort_values(by='KM').iloc[0]

        st.success(f"🏆 Melhor opção: **{vencedor['Consultor']}**")
        st.write(f"Vindo de: **{vencedor['Unidade']}** | Distância: **{vencedor['KM']:.1f} km**")
        st.balloons()

    except Exception as e:
        st.error(f"Erro de leitura: {e}")
        st.info("Verifique se o ficheiro no SharePoint tem cabeçalhos corretos.")

# --- INTERFACE LATERAL ---
with st.sidebar:
    st.header("⚙️ Painel de Comando")
    if st.button("VERIFICAR NOVAS DEMANDAS", type="primary", use_container_width=True):
        processar()

st.markdown("---") # Substituto seguro para o st.divider()
st.subheader("📋 Dados Atuais (SharePoint)")
try:
    dados_preview = pd.read_csv(URL_CSV, encoding='latin1', on_bad_lines='skip')
    st.dataframe(dados_preview, use_container_width=True)
except:
    st.caption("Aguardando sincronização de dados...")
