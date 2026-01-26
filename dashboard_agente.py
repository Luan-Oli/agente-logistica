import streamlit as st
import pandas as pd
import time
import os
from datetime import datetime
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Agente de Logística Cloud - SENAI", page_icon="🤖", layout="wide")

# --- 2. LINKS E CAMINHOS CLOUD ---
# Link do SharePoint convertido para Download Direto
URL_CSV_NUVEM = "https://sesirs-my.sharepoint.com/:x:/g/personal/luan_oliveira_senairs_org_br/Documents/Automa%C3%A7%C3%A3o/ponte_dados.csv?download=1"

# Nota: Na nuvem, o histórico e o resultado são salvos temporariamente no servidor.
# Para integração total com Power Automate Cloud, recomenda-se usar API do Graph ou Google Sheets.
ARQUIVO_HISTORICO = "historico_alocacoes.csv"
ARQUIVO_RESULTADO = "resultado_alocacao.csv"

# --- 3. FUNÇÕES DE APOIO ---
def registrar_historico(vencedor, cliente, cidade):
    """Registra a alocação no arquivo local do servidor cloud."""
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
    """Gera o arquivo de resultado para o Power Automate."""
    resultado = {
        'Consultor': [vencedor['Consultor']],
        'Cliente': [cliente],
        'Cidade': [cidade],
        'Distancia': [f"{vencedor['Distancia_KM']:.1f} km"],
        'Email_Notificacao': ["luan.oliveira@senairs.org.br"]
    }
    pd.DataFrame(resultado).to_csv(ARQUIVO_RESULTADO, index=False, encoding='utf-8-sig')

def processar_logistica():
    """Cérebro do Agente adaptado para leitura via URL."""
    st.toast("⚡ Acedendo aos dados no SharePoint...")
    try:
        # Lê os dados diretamente do link convertido
        df = pd.read_csv(URL_CSV_NUVEM)
        geolocator = Nominatim(user_agent="agente_senai_cloud_v8", timeout=20)
        
        cidade_alvo = str(df.iloc[0]['Cidade_Demanda']).strip()
        cliente = str(df.iloc[0]['Empresa']).strip()
        coord_dest = geolocator.geocode(f"{cidade_alvo}, RS, Brasil")
        
        if not coord_dest:
            st.error(f"❌ Cidade não localizada: {cidade_alvo}")
            return False

        def calc_km(row):
            time.sleep(1) # Respeita o limite da API de mapas
            loc = geolocator.geocode(f"{row['Unidade']}, RS, Brasil")
            return geodesic((coord_dest.latitude, coord_dest.longitude), (loc.latitude, loc.longitude)).km if loc else 9999

        df['Distancia_KM'] = df.apply(calc_km, axis=1)
        df['Folga_Real'] = 160 - pd.to_numeric(df['Horas_Mes'], errors='coerce').fillna(160)
        
        vencedor = df.sort_values(by=['Distancia_KM', 'Folga_Real'], ascending=[True, False]).iloc[0]
        
        registrar_historico(vencedor, cliente, cidade_alvo)
        gerar_saida_power_automate(vencedor, cliente, cidade_alvo)
        return True
    except Exception as e:
        st.error(f"❌ Erro ao processar dados da nuvem: {e}")
        return False

# --- 4. INTERFACE DO DASHBOARD ---
st.title("🤖 Painel Cloud: Agente de Logística SENAI")
st.markdown("Monitorando base de dados institucional via SharePoint.")

if 'rodando' not in st.session_state:
    st.session_state.rodando = False

with st.sidebar:
    st.header("⚙️ Controle")
    if st.button("LIGAR AGENTE" if not st.session_state.rodando else "DESLIGAR AGENTE", type="primary", use_container_width=True):
        st.session_state.rodando = not st.session_state.rodando
        st.rerun()
    
    status_cor = "green" if st.session_state.rodando else "red"
    st.markdown(f"### Status: :{status_cor}[{'ATIVO' if st.session_state.rodando else 'DESATIVADO'}]")

status_msg = st.empty()

if st.session_state.rodando:
    status_msg.info("👁️ O Agente está online e vigiando o arquivo no SharePoint...")
    # Em produção Cloud, o polling é feito por tempo ou por interação
    if st.button("VERIFICAR NOVAS DEMANDAS"):
        with st.spinner("📦 Analisando rotas e disponibilidades..."):
            if processar_logistica():
                st.success("✅ Alocação concluída! Verifique o e-mail via Power Automate.")
                st.balloons()
else:
    status_msg.warning("💤 O Agente está em repouso.")

st.markdown("---")
st.subheader("📊 Histórico de Alocações (Sessão Atual)")
if os.path.exists(ARQUIVO_HISTORICO):
    st.dataframe(pd.read_csv(ARQUIVO_HISTORICO), use_container_width=True)
else:
    st.info("Nenhuma alocação registrada nesta sessão.")
