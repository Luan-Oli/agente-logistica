import streamlit as st
import pandas as pd
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="SENAI - Agente Logística Cloud", page_icon="🤖", layout="wide")

# --- 1. CONFIGURAÇÕES CRÍTICAS (NUVEM) ---
# Substitua pelo link de "Download Direto" do seu arquivo no OneDrive/SharePoint
URL_CSV_NUVEM = "COLE_AQUI_O_LINK_DO_SEU_CSV" 

# --- 2. FUNÇÃO: ENVIAR E-MAIL VIA SMTP (SEM OUTLOOK LOCAL) ---
def enviar_email_cloud(vencedor, cliente, cidade):
    try:
        # Puxa as credenciais seguras das configurações do Streamlit
        email_user = st.secrets["EMAIL_USER"]
        email_pass = st.secrets["EMAIL_PASS"]
        
        msg = MIMEMultipart()
        msg['From'] = email_user
        msg['To'] = "luan.oliveira@senairs.org.br"
        msg['Subject'] = f"✅ Consultor Alocado: {cliente}"
        
        corpo = f"O Agente Cloud selecionou {vencedor['Consultor']} para {cliente} em {cidade}."
        msg.attach(MIMEText(corpo, 'plain'))
        
        server = smtplib.SMTP('smtp.office365.com', 587)
        server.starttls()
        server.login(email_user, email_pass)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Falha no e-mail: {e}")
        return False

# --- 3. INTERFACE E LÓGICA ---
st.title("🤖 Agente de Logística SENAI - Operação Cloud")

if 'rodando' not in st.session_state:
    st.session_state.rodando = False

with st.sidebar:
    st.header("Controle")
    if st.button("LIGAR AGENTE" if not st.session_state.rodando else "DESLIGAR AGENTE"):
        st.session_state.rodando = not st.session_state.rodando
    
    status = "🟢 ATIVO" if st.session_state.rodando else "🔴 DESATIVADO"
    st.subheader(f"Status: {status}")

if st.session_state.rodando:
    st.info("👁️ Monitorando base de dados via link de nuvem...")
    
    try:
        # Lê o CSV diretamente da internet
        df = pd.read_csv(URL_CSV_NUVEM)
        
        # Lógica de Geolocalização (Mesma da V7.0)
        geolocator = Nominatim(user_agent="agente_senai_cloud_v1", timeout=20)
        cidade_alvo = str(df.iloc[0]['Cidade_Demanda']).strip()
        cliente = str(df.iloc[0]['Empresa']).strip()
        
        st.write(f"📍 Processando demanda para: **{cliente}** em **{cidade_alvo}**")
        
        # (O restante da lógica de cálculo de KM entra aqui...)
        # Para testes, vamos simular a conclusão:
        if st.button("Simular Processamento"):
            enviar_email_cloud({'Consultor': 'Fernanda Machado'}, cliente, cidade_alvo)
            st.success("✅ Processado com sucesso na nuvem!")

    except Exception as e:
        st.error(f"Aguardando arquivo válido: {e}")
    
    time.sleep(30)
    st.rerun()
