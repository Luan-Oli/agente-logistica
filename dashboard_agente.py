import streamlit as st
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from geopy.exc import GeocoderUnavailable, GeocoderTimedOut
import folium
from streamlit_folium import st_folium
import requests
import time
from datetime import datetime
import os

# --- CONFIGURAÇÃO INICIAL (Deve ser a primeira linha de comando Streamlit) ---
st.set_page_config(page_title="Agente Logística V4.1", layout="wide")

# --- FUNÇÕES DE SUPORTE ---
def carregar_excel_bruto(arquivo_ou_caminho):
    """Lê o Excel procurando a linha onde começa a tabela real."""
    try:
        df_raw = pd.read_excel(arquivo_ou_caminho, header=None)
        
        idx_cabecalho = -1
        for i, row in df_raw.iterrows():
            row_str = row.astype(str).str.lower()
            if row_str.str.contains('consultor').any() and row_str.str.contains('unidade').any():
                idx_cabecalho = i
                break
        
        if idx_cabecalho == -1: return None, "Cabeçalho 'Consultor/Unidade' não encontrado."

        df_final = df_raw.iloc[idx_cabecalho + 1:].copy()
        df_final.columns = df_raw.iloc[idx_cabecalho]
        df_final.columns = df_final.columns.astype(str).str.strip()
        df_final = df_final.dropna(how='all')
        
        return df_final, None
    except Exception as e:
        return None, str(e)

def geocodificar_seguro(geolocator, endereco, tentativas=3):
    """Tenta buscar endereço com múltiplas tentativas."""
    for i in range(tentativas):
        try:
            geolocator.user_agent = f"agente_v41_{int(time.time())}_{i}"
            return geolocator.geocode(endereco, timeout=10)
        except (GeocoderUnavailable, GeocoderTimedOut):
            time.sleep(2)
            continue
    return None

def buscar_rota_real(ponto_a, ponto_b):
    """Busca rota rodoviária via OSRM."""
    url = f"http://router.project-osrm.org/route/v1/driving/{ponto_a[1]},{ponto_a[0]};{ponto_b[1]},{ponto_b[0]}?overview=full&geometries=geojson"
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        if data['code'] == 'Ok':
            rota = [[p[1], p[0]] for p in data['routes'][0]['geometry']['coordinates']]
            distancia = data['routes'][0]['distance'] / 1000
            return rota, distancia
    except:
        return None, None

# --- STATE ---
if 'base' not in st.session_state: st.session_state.base = pd.DataFrame()
if 'resultado' not in st.session_state: st.session_state.resultado = None

st.title("🤖 Agente Logística: Painel de Controle V4.1")

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("📁 Fonte de Dados")
    
    # 1. Automático
    arquivo_auto = "dados_atualizados.xlsx"
    df_carregado = None
    fonte_dados = ""

    if os.path.exists(arquivo_auto):
        try:
            df_temp, erro_auto = carregar_excel_bruto(arquivo_auto)
            if df_temp is not None:
                df_carregado = df_temp
                fonte_dados = "📧 Automático (E-mail)"
                st.success(f"Dados do E-mail carregados! ({len(df_carregado)} reg.)")
        except:
            pass

    # 2. Manual (Prioritário)
    arquivo_manual = st.file_uploader("Ou carregue manualmente (.xlsx):", type=["xlsx"])
    if arquivo_manual:
        df_temp, erro_manual = carregar_excel_bruto(arquivo_manual)
        if df_temp is not None:
            df_carregado = df_temp
            fonte_dados = "📂 Upload Manual"
            st.success(f"Arquivo manual carregado! ({len(df_carregado)} reg.)")
        else:
            st.error(erro_manual)
            
    if df_carregado is not None:
        st.session_state.base = df_carregado

    # --- FINANCEIRO (Polo TSI) ---
    if not st.session_state.base.empty:
        st.divider()
        st.header("🚗 Custos (Polo TSI)")
        preco_combustivel = st.number_input("Gasolina (R$):", value=6.35, step=0.01, format="%.2f")
        consumo_carro = st.number_input("Consumo (km/l):", value=15.0, step=0.1, format="%.1f")
        
        st.divider()
        lista_meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
                       'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
        mes_atual_idx = datetime.now().month - 1
        mes_ref = st.selectbox("Mês de Referência:", options=lista_meses, index=mes_atual_idx)

    if st.button("Limpar Tudo"):
        st.session_state.base = pd.DataFrame()
        st.session_state.resultado = None
        st.rerun()

# --- ÁREA PRINCIPAL ---
if not st.session_state.base.empty:
    df = st.session_state.base.copy()

    col_mes = None
    for c in df.columns:
        if str(c).lower() == str(mes_ref).lower():
            col_mes = c
            break
            
    if col_mes:
        df['Ocupacao'] = (df[col_mes].astype(str).str.replace('%', '').str.replace(',', '.').str.strip())
        df['Ocupacao'] = pd.to_numeric(df['Ocupacao'], errors='coerce').fillna(0)
        if df['Ocupacao'].max() <= 1.5: df['Ocupacao'] = df['Ocupacao'] * 100
    else:
        st.warning(f"Mês '{mes_ref}' não encontrado. Usando 0%.")
        df['Ocupacao'] = 0.0

    st.caption(f"Fonte: {fonte_dados}")
    cols_view = [c for c in ['Consultor', 'Unidade', 'Ocupacao'] if c in df.columns]
    
    st.dataframe(
        df[cols_view], 
        use_container_width=True,
        column_config={"Ocupacao": st.column_config.NumberColumn("Ocupação (%)", format="%.2f %%")}
    )

    st.divider()
    destino = st.text_input("📍 Informe a Cidade do Cliente:", placeholder="Ex: Santa Maria")

    if st.button("CALCULAR LOGÍSTICA + CUSTOS", type="primary"):
        with st.status("Processando inteligência logística...", expanded=True) as status:
            geolocator = Nominatim(user_agent=f"agente_final_{int(time.time())}", timeout=10)
            
            st.write(f"🔍 Buscando: **{destino}**...")
            loc_dest = geocodificar_seguro(geolocator, f"{destino}, RS, Brasil")

            if loc_dest:
                st.write("✅ Destino localizado.")
                st.write("🗺️ Mapeando unidades (Cache Inteligente)...")
                
                unidades_unicas = df['Unidade'].dropna().unique()
                coords_cache = {}
                prog = st.progress(0)
                
                for i, u in enumerate(unidades_unicas):
                    u_str = str(u).strip()
                    if u_str and u_str.lower() != 'nan':
                        l = geocodificar_seguro(geolocator, f"{u_str}, RS, Brasil")
                        coords_cache[u_str] = (l.latitude, l.longitude) if l else None
                        time.sleep(1.1)
                    prog.progress((i + 1) / len(unidades_unicas))
                
                st.write("🚚 Calculando custos e trajetos...")
                
                def aplicar_rota(row):
                    uni = str(row.get('Unidade', '')).strip()
                    coords_origem = coords_cache.get(uni)
                    if coords_origem:
                        coords_dest = (loc_dest.latitude, loc_dest.longitude)
                        cam, km = buscar_rota_real(coords_origem, coords_dest)
                        if not km: km = geodesic(coords_origem, coords_dest).km
                        return pd.Series([km, coords_origem, cam])
                    return pd.Series([9999, None, None])

                df[['Distancia', 'Coords', 'Trajeto']] = df.apply(aplicar_rota, axis=1)
                validos = df[df['Distancia'] < 9000]
                
                if not validos.empty:
                    venc = validos.sort_values(by=['Ocupacao', 'Distancia']).iloc[0]
                    st.session_state.resultado = {'venc': venc, 'dest': (loc_dest.latitude, loc_dest.longitude)}
                    status.update(label="Concluído!", state="complete", expanded=False)
                else:
                    status.update(label="Erro: Sem rotas", state="error")
                    st.error("Nenhuma rota válida encontrada.")
            else:
                status.update(label="Destino não encontrado", state="error")
                st.error("Cidade não encontrada.")

    if st.session_state.resultado:
        res = st.session_state.resultado
        v = res['venc']
        cor = "orange" if v['Ocupacao'] > 80 else "green"
        
        dist_total = v['Distancia'] * 2
        litros = dist_total / consumo_carro
        custo = litros * preco_combustivel

        st.success(f"🏆 Melhor Indicação: **{v['Consultor']}** ({v['Unidade']})")
        c1, c2, c3 = st.columns(3)
        c1.metric("Distância (Ida)", f"{v['Distancia']:.1f} km")
        c2.metric("Ocupação", f"{v['Ocupacao']:.2f}%")
        c3.metric("Custo Total (Ida+Volta)", f"R$ {custo:.2f}")

        m = folium.Map(location=res['dest'], zoom_start=8)
        folium.Marker(res['dest'], tooltip="Cliente", icon=folium.Icon(color='red')).add_to(m)
        if v['Coords']:
            folium.Marker(v['Coords'], tooltip=f"{v['Consultor']} | R$ {custo:.0f}", icon=folium.Icon(color=cor, icon='user')).add_to(m)
            if v['Trajeto']:
                folium.PolyLine(v['Trajeto'], color="blue", weight=5, opacity=0.7).add_to(m)
        st_folium(m, width=1200, height=500, key="mapa_final")

else:
    st.info("💡 Aguardando dados. O sistema verificará o e-mail automaticamente ou faça upload manual.")
    
