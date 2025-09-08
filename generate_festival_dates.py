# -*- coding: utf-8 -*-
# ================================================
# Análise RIMA — Operações Simultâneas (janela variável)
# Ajustes: inclui ACN (Azul Conecta, C208=9 assentos) e NÃO restringe por cia (exclui apenas "GERAL")
# ================================================

import hashlib
import json
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED
from datetime import datetime
import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Análise RIMA", layout="wide")
title_placeholder = st.empty()

st.markdown(
    """
    <style>
    [data-testid="stSidebar"] { min-width: 400px; max-width: 400px; padding-top: 0rem !important; }
    [data-testid="stSidebar"] .block-container { padding-top: 0rem !important; padding-bottom: 0rem !important; }
    section[data-testid="stSidebar"][aria-expanded="false"] { display: none; }
    .header-container { display: flex; justify-content: space-between; align-items: center; }
    .title { font-size: 36px; font-weight: bold; color: #1a2732; text-align: left; }
    .subtitle { font-size: 16px; color: #5b6b7b; text-align: left; }
    .logo { width: 220px; max-width: 100%; height: auto; }
    </style>
    """,
    unsafe_allow_html=True
)

DEFAULT_WINDOW_MIN = 45
DEFAULT_MIN_CONSEC = 3
DEFAULT_MIN_COMB = 4
THRESH_PAX_CONSEC_DEFAULT = 484
THRESH_PAX_COMBI_DEFAULT = 580

DEFAULT_COLORS = ["#0073e6", "#d62728", "#ff7f0e", "#2ca02c", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"]
PREFERRED_COLORS = {"AZU": "#0073e6","ACN":"#0073e6","TAM": "#d62728","GLO": "#ff7f0e","PAM": "#ffdd44"}

def fmt_int(x):
    try:
        return f"{int(x):,}".replace(",", ".")
    except Exception:
        return str(x)

def df_to_excel_bytes(df, sheet="Dados"):
    out = BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet)
    return out.getvalue()

def make_zip(files):
    bio = BytesIO()
    with ZipFile(bio, "w", compression=ZIP_DEFLATED) as zf:
        for name, content in files:
            zf.writestr(name, content)
    return bio.getvalue()

@st.cache_data(show_spinner=False)
def read_excel_and_hash(file_bytes):
    sha = hashlib.sha256(file_bytes).hexdigest()
    df = pd.read_excel(BytesIO(file_bytes))
    return df, sha

def prepare_rima_dataframe(df_in: pd.DataFrame):
    df = df_in.copy()
    required = ['AERONAVE_OPERADOR','MOVIMENTO_TIPO','CALCO_DATA','CALCO_HORARIO','VOO_NUMERO','AERONAVE_TIPO','SERVICE_TYPE','PAX_LOCAL']
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError("Colunas ausentes no Excel RIMA: " + ", ".join(missing))

    for col in ['AERONAVE_OPERADOR','MOVIMENTO_TIPO','VOO_NUMERO','AERONAVE_TIPO','SERVICE_TYPE']:
        df[col] = df[col].astype(str).str.strip()

    # Numéricos
    df['PAX_LOCAL'] = pd.to_numeric(df['PAX_LOCAL'], errors='coerce').fillna(0).astype(int)
    if 'PAX_CONEXAO_DOMESTICO' in df.columns:
        df['PAX_CONEXAO_DOMESTICO'] = pd.to_numeric(df['PAX_CONEXAO_DOMESTICO'], errors='coerce').fillna(0).astype(int)
    else:
        df['PAX_CONEXAO_DOMESTICO'] = 0

    # Filtros de escopo:
    df['AERONAVE_OPERADOR'] = df['AERONAVE_OPERADOR'].str.upper().str.strip()
    # ❌ NÃO restringe por lista de cias — ✅ remove apenas "GERAL"
    df = df[~df['AERONAVE_OPERADOR'].isin(['GERAL','GENERAL','AVIAÇÃO GERAL','AVIACAO GERAL'])]
    # Mantém a exclusão de SERVICE_TYPE == 'P' conforme sua lógica original
    df = df[df['SERVICE_TYPE'].str.upper() != 'P']

    df['_discard_reason'] = ""

    # --- PARSE ROBUSTO DO CALCO_DATETIME ---
    date_parsed = pd.to_datetime(df['CALCO_DATA'], errors='coerce').dt.normalize()
    hora_raw = df['CALCO_HORARIO'].astype(str).str.extract(r'(\d{1,2}:\d{2}(?::\d{2}(?:\.\d{1,6})?)?)')[0]
    time_parsed = pd.to_datetime(hora_raw, errors='coerce')

    td = (pd.to_timedelta(time_parsed.dt.hour.fillna(0).astype(int), unit='h') +
          pd.to_timedelta(time_parsed.dt.minute.fillna(0).astype(int), unit='m') +
          pd.to_timedelta(time_parsed.dt.second.fillna(0).astype(int), unit='s'))

    df['CALCO_DATETIME'] = date_parsed + td
    invalid_dt = date_parsed.isna() | time_parsed.isna()
    df.loc[invalid_dt, '_discard_reason'] += "Data/Hora inválida; "

    # Assentos ofertados (inclui C208 = 9 e mantém regras A20N/A320 por cia)
    pax_mapping = {
        'C208': 9,  # Azul Conecta
        '738W': 186,'A319': 140,'AT45': 47,'AT75': 70,'AT76': 70,
        'B38M': 186,'B737': 138,'B738': 186,'E195': 118,'E295': 136,
        'A21N': 220,'A321': 220
    }
    def map_seats_offered(op, typ):
        typ = str(typ).upper().strip()
        if typ in ['A20N','A320']:
            return 174 if str(op).upper().strip() == 'AZU' else 176
        return pax_mapping.get(typ, 0)
    df['SEATS_OFFERED'] = df.apply(lambda r: map_seats_offered(r['AERONAVE_OPERADOR'], r['AERONAVE_TIPO']), axis=1)

    discarded = df[df['_discard_reason'] != ""].copy()
    discarded['_discard_reason'] = discarded['_discard_reason'].str.rstrip("; ").str.strip()

    clean = df[df['_discard_reason'] == ""].copy().sort_values('CALCO_DATETIME').reset_index(drop=True)

    clean['Date'] = clean['CALCO_DATETIME'].dt.date
    clean['DateTime'] = clean['CALCO_DATETIME']
    clean['ArrDep'] = clean['MOVIMENTO_TIPO'].str.upper().map({'P':'A','D':'D'})
    clean['Company'] = clean['AERONAVE_OPERADOR'].astype(str).str.strip()
    clean['Fltno'] = clean['VOO_NUMERO'].astype(str).str.strip()
    clean['Actyp'] = clean['AERONAVE_TIPO'].astype(str).str.strip()

    cols_keep = ['CALCO_DATA','CALCO_HORARIO','AERONAVE_OPERADOR','MOVIMENTO_TIPO','VOO_NUMERO','AERONAVE_TIPO','SERVICE_TYPE','PAX_LOCAL','PAX_CONEXAO_DOMESTICO','BOX','CABECEIRA','_discard_reason']
    cols_keep = [c for c in cols_keep if c in discarded.columns]
    return clean, discarded[cols_keep], None

def consecutive_groups(df, tipo, window_min, min_size):
    sub = df[df['ArrDep']==tipo].reset_index(drop=True)
    res, counts, start = [], {}, 0
    for end in range(len(sub)):
        while (sub.loc[end,'DateTime'] - sub.loc[start,'DateTime']).total_seconds() > window_min*60:
            start += 1
        size = end-start+1
        if size>=min_size:
            counts[size] = counts.get(size,0)+1
            block=sub.iloc[start:end+1]
            rec={}
            for i, (_, r) in enumerate(block.iterrows(), start=1):
                rec[f"{i}th DateTime"]=r['DateTime'].strftime('%d/%m/%Y %H:%M')
                rec[f"{i}th Flight"]=f"{r['AERONAVE_OPERADOR']} {r['Fltno']} - {r['Actyp']}"
            rec['PAX (Local)']=int(block['PAX_LOCAL'].sum())
            rec['Seats Offered']=int(block['SEATS_OFFERED'].sum())
            res.append(rec)
    out=pd.DataFrame(res).fillna('---')
    if not out.empty:
        cols=[c for c in out.columns if c not in ['PAX (Local)','Seats Offered']]
        out=out[cols+['PAX (Local)','Seats Offered']]
    return out, dict(sorted(counts.items(), reverse=True))

def combined_groups(df, window_min, min_ops):
    res, counts, start = [], {}, 0
    for end in range(len(df)):
        while (df.loc[end,'DateTime'] - df.loc[start,'DateTime']).total_seconds() > window_min*60:
            start += 1
        block=df.iloc[start:end+1]
        if len(block)>=min_ops:
            a=(block['ArrDep']=='A').sum(); d=(block['ArrDep']=='D').sum()
            if a>0 and d>0:
                combo=f"{int(a)} Pousos e {int(d)} Decolagens"
                counts[combo]=counts.get(combo,0)+1
                rec={}
                for i,(_,r) in enumerate(block.iterrows(), start=1):
                    sig="(A)" if r['ArrDep']=='A' else "(D)"
                    rec[f"{i}th DateTime"]=r['DateTime'].strftime('%d/%m/%Y %H:%M')
                    rec[f"{i}th Flight"]=f"{r['AERONAVE_OPERADOR']} {r['Fltno']} {sig} - {r['Actyp']}"
                rec['Combination Type']=combo
                rec['PAX (Local)']=int(block['PAX_LOCAL'].sum())
                rec['Seats Offered']=int(block['SEATS_OFFERED'].sum())
                res.append(rec)
    out=pd.DataFrame(res).fillna('---')
    if not out.empty:
        cols=[c for c in out.columns if c not in ['Combination Type','PAX (Local)','Seats Offered']]
        out=out[cols+['Combination Type','PAX (Local)','Seats Offered']]
    return out, counts

def days_four_plus_positions(df):
    rows=[]
    for date,g in df.sort_values('DateTime').groupby(df['DateTime'].dt.date):
        current=0
        for _,r in g.iterrows():
            if r['ArrDep']=='A':
                current+=1
                if current>=4:
                    rows.append({'Date':pd.to_datetime(date).strftime('%d/%m/%Y'),
                                 'Time':r['DateTime'].strftime('%H:%M'),
                                 'Last Flight':f"{r['AERONAVE_OPERADOR']} {r['Fltno']}",
                                 'Positions':current})
            else:
                current-=1
    return pd.DataFrame(rows)

with st.sidebar:
    st.header("Parâmetros")
    window_min = st.slider("Janela (min)", 30, 120, DEFAULT_WINDOW_MIN, 5)
    min_consec = st.number_input("Mínimo de voos (Consecutivos)", value=DEFAULT_MIN_CONSEC, min_value=2, step=1)
    min_comb = st.number_input("Mínimo de operações (Combinados A+D)", value=DEFAULT_MIN_COMB, min_value=3, step=1)
    THRESH_PAX_CONSEC = st.number_input("Limiar PAX Local (Consecutivos)", value=THRESH_PAX_CONSEC_DEFAULT, step=10)
    THRESH_PAX_COMBI = st.number_input("Limiar PAX Local (Combinados)", value=THRESH_PAX_COMBI_DEFAULT, step=10)
    only_over_threshold = st.checkbox("Mostrar apenas grupos com PAX ≥ limiar")
    uploaded = st.file_uploader("Carregue o RIMA (xls/xlsx)", type=["xls","xlsx"])

if uploaded is None:
    title_placeholder.markdown(
        f"""
        <div class="header-container">
            <div>
                <div class="title">Análise RIMA</div>
                <div class="subtitle">Operações simultâneas em janela de {int(window_min)} minutos • PAX Local</div>
            </div>
            <img class="logo" src="https://i.imgur.com/YetM1cb.png" alt="Logotipo">
        </div>
        <hr style="border: 1px solid #cccccc;">
        """,
        unsafe_allow_html=True
    )
    st.stop()

file_bytes = uploaded.getvalue() if hasattr(uploaded,"getvalue") else uploaded.read()
raw_df, sha = read_excel_and_hash(file_bytes)
sha12 = sha[:12]

try:
    df, discarded_df, _ = prepare_rima_dataframe(raw_df)
except Exception as e:
    st.error(f"Erro ao preparar o arquivo: {e}")
    st.stop()

title_placeholder.markdown(
    f"""
    <div class="header-container">
        <div>
            <div class="title">Análise RIMA</div>
            <div class="subtitle">Operações simultâneas em janela de {int(window_min)} minutos • PAX Local</div>
        </div>
        <img class="logo" src="https://i.imgur.com/YetM1cb.png" alt="Logotipo">
    </div>
    <hr style="border: 1px solid #cccccc;">
    """,
    unsafe_allow_html=True
)

with st.expander("Saúde do dado • integridade e qualidade", expanded=True):
    st.write(f"**Hash do arquivo (SHA-256):** `{sha12}`")
    c1,c2,c3 = st.columns(3)
    c1.metric("Linhas totais", fmt_int(len(raw_df)))
    c2.metric("Linhas válidas", fmt_int(len(df)))
    c3.metric("Descartadas", fmt_int(len(discarded_df)))
    if len(discarded_df)>0:
        st.markdown("**Registros descartados (com motivo):**")
        st.dataframe(discarded_df.rename(columns={'_discard_reason':'Motivo'}), use_container_width=True, hide_index=True)
        st.download_button("Baixar descartados (XLSX)", data=df_to_excel_bytes(discarded_df.rename(columns={'_discard_reason':'Motivo'})), file_name="descartados.xlsx")

companies = sorted(df['Company'].unique().tolist())
if 'color_map' not in st.session_state:
    auto = {}
    i=0
    for label in companies:
        auto[label] = PREFERRED_COLORS.get(label, DEFAULT_COLORS[i % len(DEFAULT_COLORS)])
        i+=1
    st.session_state.color_map = auto
color_map = st.session_state.color_map

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Pousos Consecutivos (A)","Decolagens Consecutivas (D)","Operações Combinadas (A+D)","4+ Posições","Gráficos & KPIs"])

with tab1:
    A_df, A_cnt = consecutive_groups(df,'A', window_min, int(min_consec))
    if only_over_threshold and not A_df.empty:
        A_df = A_df[A_df['PAX (Local)']>=THRESH_PAX_CONSEC]
    if A_df.empty:
        st.info("Sem ocorrências de pousos consecutivos.")
    else:
        for k,v in A_cnt.items():
            st.markdown(f"**Total de {k:02d} pousos consecutivos:** {fmt_int(v)}")
        view = A_df.reset_index(drop=True)
        st.dataframe(view.style.applymap(lambda v: 'color: red; font-weight: bold;' if isinstance(v,int) and v>=THRESH_PAX_CONSEC else '', subset=['PAX (Local)']), use_container_width=True, hide_index=True)
        st.download_button("Baixar XLSX", data=df_to_excel_bytes(view), file_name="Pousos_Consecutivos.xlsx")

with tab2:
    D_df, D_cnt = consecutive_groups(df,'D', window_min, int(min_consec))
    if only_over_threshold and not D_df.empty:
        D_df = D_df[D_df['PAX (Local)']>=THRESH_PAX_CONSEC]
    if D_df.empty:
        st.info("Sem ocorrências de decolagens consecutivas.")
    else:
        for k,v in D_cnt.items():
            st.markdown(f"**Total de {k:02d} decolagens consecutivas:** {fmt_int(v)}")
        view = D_df.reset_index(drop=True)
        st.dataframe(view.style.applymap(lambda v: 'color: red; font-weight: bold;' if isinstance(v,int) and v>=THRESH_PAX_CONSEC else '', subset=['PAX (Local)']), use_container_width=True, hide_index=True)
        st.download_button("Baixar XLSX", data=df_to_excel_bytes(view), file_name="Decolagens_Consecutivas.xlsx")

with tab3:
    C_df, C_cnt = combined_groups(df, window_min, int(min_comb))
    if only_over_threshold and not C_df.empty:
        C_df = C_df[C_df['PAX (Local)']>=THRESH_PAX_COMBI]
    if C_df.empty:
        st.info("Sem ocorrências de operações combinadas.")
    else:
        for combo,total in C_cnt.items():
            st.markdown(f"**Total de {combo}:** {fmt_int(total)}")
        view = C_df.reset_index(drop=True)
        st.dataframe(view.style.applymap(lambda v: 'color: red; font-weight: bold;' if isinstance(v,int) and v>=THRESH_PAX_COMBI else '', subset=['PAX (Local)']), use_container_width=True, hide_index=True)
        st.download_button("Baixar XLSX", data=df_to_excel_bytes(view), file_name="Operacoes_Combinadas.xlsx")

with tab4:
    pos_df = days_four_plus_positions(df)
    if pos_df.empty:
        st.info("Nenhuma data com 4+ posições ocupadas.")
    else:
        counts = pos_df['Positions'].value_counts().sort_index()
        for k, v in counts.items():
            st.markdown(f"**Total de {k:02d} posições ocupadas:** {fmt_int(v)}")
        view = pos_df.reset_index(drop=True)
        st.dataframe(view.style.applymap(lambda v: 'color: red; font-weight: bold;', subset=['Positions']), use_container_width=True, hide_index=True)
        st.download_button("Baixar XLSX", data=df_to_excel_bytes(view), file_name="Dias_Com_4_Posicoes.xlsx")

with tab5:
    st.subheader("KPIs Gerais (PAX Local)")
    colf1, colf2 = st.columns([1,2])
    with colf1:
        tipo = st.radio("Tipo de movimento", ["Todos", "Pousos (P)", "Decolagens (D)"], horizontal=True)
    with colf2:
        sel_comp = st.multiselect("Companhias", options=companies, default=companies)
    df_kpi = df.copy()
    if tipo=="Pousos (P)":
        df_kpi = df_kpi[df_kpi['ArrDep']=='A']
    elif tipo=="Decolagens (D)":
        df_kpi = df_kpi[df_kpi['ArrDep']=='D']
    df_kpi = df_kpi[df_kpi['Company'].isin(sel_comp)]
    c1,c2,c3 = st.columns(3)
    c1.metric("Total de operações", fmt_int(len(df_kpi)))
    c2.metric("PAX Local (somatório)", fmt_int(df_kpi['PAX_LOCAL'].sum()))
    c3.metric("Companhias ativas", fmt_int(df_kpi['Company'].nunique()))
    st.markdown("---")
    st.subheader("Operações Mensais por Companhia")
    df_kpi['Month'] = df_kpi['DateTime'].dt.to_period('M').astype(str)
    ops_month = df_kpi.groupby(['Month','Company'])['ArrDep'].count().reset_index(name='Operacoes')
    fig_ops = px.bar(ops_month, x='Month', y='Operacoes', color='Company', text=ops_month['Operacoes'].map(fmt_int), color_discrete_map=color_map, barmode='group')
    fig_ops.update_traces(textposition='outside')
    fig_ops.update_layout(xaxis_title="Mês", yaxis_title="Operações", showlegend=True)
    st.plotly_chart(fig_ops, use_container_width=True)

    st.subheader("PAX Local por Companhia (Mensal)")
    pax_month = df_kpi.groupby(['Month','Company'])['PAX_LOCAL'].sum().reset_index(name='PAX')
    fig_pax = px.bar(pax_month, x='Month', y='PAX', color='Company', text=pax_month['PAX'].map(fmt_int), color_discrete_map=color_map, barmode='group')
    fig_pax.update_traces(textposition='outside')
    fig_pax.update_layout(xaxis_title="Mês", yaxis_title="PAX Local", showlegend=True)
    st.plotly_chart(fig_pax, use_container_width=True)

    st.subheader("Total de Operações por Companhia (Período Filtrado)")
    total_ops_cia = df_kpi.groupby('Company')['ArrDep'].count().reset_index(name='Operacoes').sort_values('Operacoes', ascending=False)
    fig_total = px.bar(total_ops_cia, x='Company', y='Operacoes', text=total_ops_cia['Operacoes'].map(fmt_int), color='Company', color_discrete_map=color_map)
    fig_total.update_traces(textposition='outside', showlegend=False)
    fig_total.update_layout(xaxis_title="Companhia", yaxis_title="Operações")
    st.plotly_chart(fig_total, use_container_width=True)

    st.subheader("Passageiros Embarcados por Companhia (Local + Conexão Doméstica)")
    use_conn = st.checkbox("Incluir PAX de conexão doméstica", value=True)
    pax_col = 'PAX_TOTAL_calc'
    df_kpi[pax_col] = df_kpi['PAX_LOCAL'] + (df_kpi['PAX_CONEXAO_DOMESTICO'] if use_conn else 0)
    company_pax = df_kpi.groupby('Company')[pax_col].sum().reset_index().rename(columns={pax_col:'TOTAL_PAX'})
    fig_bar = go.Figure()
    for _, row in company_pax.iterrows():
        txt = f"<b>{fmt_int(int(row['TOTAL_PAX']))}</b>"
        fig_bar.add_trace(go.Bar(x=[row['Company']], y=[row['TOTAL_PAX']], text=txt, textposition='inside', marker_color=color_map.get(row['Company'],'#333333'), textfont=dict(size=14, color="white")))
    fig_bar.update_layout(title="Passageiros Embarcados por Companhia", xaxis_title="Companhia Aérea", yaxis_title="Total de Passageiros", template="plotly_white", showlegend=False, xaxis=dict(showgrid=False), yaxis=dict(showgrid=False))
    st.plotly_chart(fig_bar, use_container_width=True)
    total_geral = int(company_pax['TOTAL_PAX'].sum())
    st.markdown(f"<h3 style='text-align:center;'><b>Total Geral de Passageiros: {fmt_int(total_geral)}</b></h3>", unsafe_allow_html=True)

st.subheader("Exportar pacote de auditoria")
meta = {"hash_sha256": sha, "hash_prefix": sha12, "window_min": int(window_min), "min_consecutivos": int(min_consec), "min_combinados": int(min_comb), "threshold_pax_consecutivos": int(THRESH_PAX_CONSEC), "threshold_pax_combinados": int(THRESH_PAX_COMBI), "generated_at_utc": datetime.utcnow().isoformat()+"Z", "rows_original": int(len(raw_df)), "rows_clean": int(len(df)), "rows_discarded": int(len(discarded_df)), "airport": "RIMA", "metric_note": "PAX (Local) = embarque local conforme RIMA"}
files = [("metadata.json", json.dumps(meta, ensure_ascii=False, indent=2).encode("utf-8"))]
if 'A_df' in locals() and isinstance(A_df, pd.DataFrame) and not A_df.empty: files.append(("pousos_consecutivos.xlsx", df_to_excel_bytes(A_df.reset_index(drop=True))))
if 'D_df' in locals() and isinstance(D_df, pd.DataFrame) and not D_df.empty: files.append(("decolagens_consecutivas.xlsx", df_to_excel_bytes(D_df.reset_index(drop=True))))
if 'C_df' in locals() and isinstance(C_df, pd.DataFrame) and not C_df.empty: files.append(("operacoes_combinadas.xlsx", df_to_excel_bytes(C_df.reset_index(drop=True))))
if 'pos_df' in locals() and isinstance(pos_df, pd.DataFrame) and not pos_df.empty: files.append(("dias_4_posicoes.xlsx", df_to_excel_bytes(pos_df.reset_index(drop=True))))
if len(discarded_df)>0: files.append(("descartados.xlsx", df_to_excel_bytes(discarded_df.rename(columns={'_discard_reason':'Motivo'}))))
zip_bytes = make_zip(files)
st.download_button(f"Baixar pacote ZIP", data=zip_bytes, file_name=f"auditoria_rima_{int(window_min)}min.zip")
