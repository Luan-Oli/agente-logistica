import streamlit as st
import pandas as pd
import time
from datetime import datetime

# Configuração visual da página
st.set_page_config(page_title="Agente de Logística SENAI", page_icon="🤖", layout="wide")

st.title("🤖 Painel de Controle: Agente de Logística")
st.markdown("---")

# Colunas para organizar o layout
col1, col2 = st.columns([1, 3])

with col1:
    st.header("Controle")
    # Estado do Robô (Salvo na sessão do navegador)
    if 'robo_ativo' not in st.session_state:
        st.session_state.robo_ativo = False

    def alternar_robo():
        st.session_state.robo_ativo = not st.session_state.robo_ativo

    st.button(
        "LIGAR AGENTE" if not st.session_state.robo_ativo else "DESLIGAR AGENTE", 
        on_click=alternar_robo,
        type="primary" if not st.session_state.robo_ativo else "secondary"
    )

    status = "🟢 OPERANDO" if st.session_state.robo_ativo else "🔴 EM REPOUSO"
    st.subheader(f"Status: {status}")
    
    st.info("O robô processa automaticamente as demandas vindas do Power Automate.")

with col2:
    st.header("Monitor de Atividades (Tempo Real)")
    
    # Simulação de Logs (Isso será conectado à sua lógica de cálculo)
    log_container = st.container(border=True)
    
    if st.session_state.robo_ativo:
        with log_container:
            st.write(f"⏱️ {datetime.now().strftime('%H:%M:%S')} - Agente ativado. Vigiando base de dados...")
            # Aqui mostraremos os últimos resultados, como o caso da Fernanda Machado
            st.success("✅ Última alocação: Fernanda Machado | Destino: Encantado | 35.5 km")
    else:
        log_container.write("💤 Sistema pausado pelo coordenador.")

# Área de Histórico (Visualização rápida para todos)
st.markdown("---")
st.header("📊 Histórico Recente")
# Exemplo de como os dados aparecerão para todos
dados_exemplo = pd.DataFrame({
    'Data': ['26/01/2026', '25/01/2026'],
    'Cliente': ['RAQUEL', 'EMPRESA TESTE'],
    'Consultor': ['Fernanda Machado', 'João Silva'],
    'KM': [35.5, 12.2]
})
st.table(dados_exemplo)