import os
import pandas as pd
import streamlit as st
from datetime import timedelta
from io import BytesIO
import plotly.express as px

# Configuração inicial da página
st.set_page_config(
    page_title="Análise RIMA SBJU",
    layout="wide"
)

# Cabeçalho HTML com CSS
st.markdown("""
    <style>
        .header-container {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .title { 
            font-size: 36px; 
            font-weight: bold; 
            color: #333333; 
            text-align: left; 
        }
        .subtitle { 
            font-size: 18px; 
            font-style: italic; 
            color: #666666; 
            text-align: left; 
        }
        .logo {
            width: 250px;  
            max-width: 100%;  
            height: auto;
        }
    </style>
    <div class="header-container">
        <div>
            <div class="title">Análise RIMA - SBJU</div>
            <div class="subtitle">Operações simultâneas em intervalo de 45 minutos (Exclusivo RIMA)</div>
        </div>
        <img class="logo" src="https://i.imgur.com/YetM1cb.png" alt="Logotipo">
    </div>
    <hr style="border: 1px solid #cccccc;">
""", unsafe_allow_html=True) 

import pandas as pd
import streamlit as st
from io import BytesIO

# Estilo e título
st.markdown("""
    <style>
        .title-box {
            padding: 10px;
            border: 1px solid #cccccc;
            border-radius: 10px;
            background-color: #f9f9f9;
            font-weight: bold;
            color: #333333;
        }
        .highlight-red {
            color: red;
            font-weight: bold;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown(
    "<div style='color: red; font-weight: bold;'>Escolha um arquivo Excel para análise do RIMA:</div>", 
    unsafe_allow_html=True
)

# Uploader para arquivos Excel
rima_file = st.file_uploader("Carregue o arquivo (formato Excel)", type=["xls", "xlsx"])

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Dados')
    return output.getvalue()

# Função para processar pousos e decolagens consecutivos
def process_rima(data):
    valid_companies = ['AZU', 'GLO', 'PAM', 'TAM']
    data = data[data['AERONAVE_OPERADOR'].isin(valid_companies)].copy()

    data['CALCO_DATETIME'] = pd.to_datetime(
        data['CALCO_DATA'].astype(str) + ' ' + data['CALCO_HORARIO'].astype(str),
        errors='coerce'
    )

    data = data.dropna(subset=['CALCO_DATETIME'])

    data = data[data['SERVICE_TYPE'] != 'P']  # Excluir registros com código 'P' na coluna SERVICE_TYPE

    pax_mapping = {'738W': 186, 'A319': 140, 'AT45': 47, 'AT75': 70, 'AT76': 70,
                   'B38M': 186, 'B737': 138, 'B738': 186, 'E195': 118, 'E295': 136, 'A21N': 220, 'A321': 220}

    def map_seats_offered(row):
        if row['AERONAVE_TIPO'] in ['A20N', 'A320']:
            return 174 if row['AERONAVE_OPERADOR'] == 'AZU' else 176
        return pax_mapping.get(row['AERONAVE_TIPO'], 0)

    data['Seats Offered'] = data.apply(map_seats_offered, axis=1)

    def find_consecutive(df, operation_type):
        df = df[df['MOVIMENTO_TIPO'] == operation_type].sort_values(by='CALCO_DATETIME').reset_index(drop=True)
        results = []
        group_sizes = {}
        
        for i in range(len(df)):
            group = []
            seats_offered = 0
            occupied_seats = 0
            
            for j in range(i, len(df)):
                if (df.loc[j, 'CALCO_DATETIME'] - df.loc[i, 'CALCO_DATETIME']).total_seconds() / 60 <= 45:
                    group.append(j)
                    seats_offered += df.loc[j, 'Seats Offered']
                    occupied_seats += df.loc[j, 'PAX_LOCAL']

            if len(group) >= 3:
                group_size = len(group)
                group_sizes[group_size] = group_sizes.get(group_size, 0) + 1
                result = {
                    '1th DateTime': df.loc[group[0], 'CALCO_DATETIME'].strftime('%d/%m/%Y %H:%M'),
                    '1th Flight': f"{df.loc[group[0], 'AERONAVE_OPERADOR']} {int(df.loc[group[0], 'VOO_NUMERO'])} - {df.loc[group[0], 'AERONAVE_TIPO']}"
                }
                for idx, g in enumerate(group[1:], start=2):
                    result[f'{idx}th DateTime'] = df.loc[g, 'CALCO_DATETIME'].strftime('%d/%m/%Y %H:%M')
                    result[f'{idx}th Flight'] = f"{df.loc[g, 'AERONAVE_OPERADOR']} {int(df.loc[g, 'VOO_NUMERO'])} - {df.loc[g, 'AERONAVE_TIPO']}"
                result['Occupied Seats'] = occupied_seats
                result['Seats Offered'] = seats_offered
                results.append(result)

        results_df = pd.DataFrame(results)
        if not results_df.empty:
            final_columns = list(results_df.columns)
            final_columns.remove('Occupied Seats')
            final_columns.remove('Seats Offered')
            final_columns.extend(['Occupied Seats', 'Seats Offered'])
            results_df = results_df[final_columns]
            results_df.fillna('---', inplace=True)
        return results_df, group_sizes

    def find_combined_operations(data):
        data = data.sort_values(by='CALCO_DATETIME')

        combined_operations = []
        total_counts = {}

        for i in range(len(data)):
            group = [data.iloc[i]]
            total_pax = data.iloc[i]['PAX_LOCAL']
            seats_offered = data.iloc[i]['Seats Offered']
            arrivals, departures = 0, 0

            if data.iloc[i]['MOVIMENTO_TIPO'] == 'P':
                arrivals += 1
            else:
                departures += 1

            for j in range(i + 1, len(data)):
                if (data.iloc[j]['CALCO_DATETIME'] - group[0]['CALCO_DATETIME']).total_seconds() / 60 <= 45:
                    group.append(data.iloc[j])
                    total_pax += data.iloc[j]['PAX_LOCAL']
                    seats_offered += data.iloc[j]['Seats Offered']
                    if data.iloc[j]['MOVIMENTO_TIPO'] == 'P':
                        arrivals += 1
                    else:
                        departures += 1
                else:
                    break

            if len(group) >= 4 and arrivals > 0 and departures > 0:
                combination_type = f"{arrivals} Pousos e {departures} Decolagens"
                total_counts[combination_type] = total_counts.get(combination_type, 0) + 1
                record = {
                    'Combination Type': combination_type,
                    'Occupied Seats': total_pax,
                    'Seats Offered': seats_offered
                }
                for idx, flight in enumerate(group):
                    record[f'{idx+1}th DateTime'] = flight['CALCO_DATETIME'].strftime('%d/%m/%Y %H:%M')
                    record[f'{idx+1}th Flight'] = f"{flight['AERONAVE_OPERADOR']} {int(flight['VOO_NUMERO'])} ({flight['MOVIMENTO_TIPO']}) - {flight['AERONAVE_TIPO']}"
                combined_operations.append(record)

        combined_df = pd.DataFrame(combined_operations).fillna('---')
        if not combined_df.empty:
            cols = [col for col in combined_df.columns if col not in ['Combination Type', 'Occupied Seats', 'Seats Offered']]
            combined_df = combined_df[cols + ['Combination Type', 'Occupied Seats', 'Seats Offered']]
        return combined_df, total_counts

    pousos, pousos_group_sizes = find_consecutive(data, 'P')
    decolagens, decolagens_group_sizes = find_consecutive(data, 'D')
    combinados, combinados_group_sizes = find_combined_operations(data)

    return pousos, pousos_group_sizes, decolagens, decolagens_group_sizes, combinados, combinados_group_sizes

if rima_file is not None:
    try:
        rima_data = pd.read_excel(rima_file)
        rima_data['PAX_LOCAL'] = rima_data['PAX_LOCAL'].fillna(0).astype(int)

        pousos_result, pousos_group_sizes, decolagens_result, decolagens_group_sizes, combinados_result, combinados_group_sizes = process_rima(rima_data)

        st.markdown("<div class='title'>Pousos Consecutivos (A):</div>", unsafe_allow_html=True)
        if not pousos_result.empty:
            for size, count in sorted(pousos_group_sizes.items()):
                st.markdown(f"<div class='highlight-red'>Total de Operacões Consecutivas {size} Pousos: {count}</div>", unsafe_allow_html=True)
            styled_pousos = pousos_result.style.applymap(lambda x: 'color: red;' if isinstance(x, int) and x >= 484 else '', subset=['Occupied Seats'])
            st.dataframe(styled_pousos, use_container_width=True)
            st.download_button("Baixar Pousos Consecutivos", to_excel(pousos_result), file_name="pousos_consecutivos.xlsx")
        else:
            st.write("Nenhum pouso consecutivo identificado.")

        st.markdown("<div class='title'>Decolagens Consecutivas (D):</div>", unsafe_allow_html=True)
        if not decolagens_result.empty:
            for size, count in sorted(decolagens_group_sizes.items()):
                st.markdown(f"<div class='highlight-red'>Total de Operacões Consecutivas {size} Decolagens: {count}</div>", unsafe_allow_html=True)
            styled_decolagens = decolagens_result.style.applymap(lambda x: 'color: red;' if isinstance(x, int) and x >= 484 else '', subset=['Occupied Seats'])
            st.dataframe(styled_decolagens, use_container_width=True)
            st.download_button("Baixar Decolagens Consecutivas", to_excel(decolagens_result), file_name="decolagens_consecutivas.xlsx")
        else:
            st.write("Nenhuma decolagem consecutiva identificada.")

        st.markdown("<div class='title'>Operações Combinadas:</div>", unsafe_allow_html=True)
        if not combinados_result.empty:
            for combo, count in sorted(combinados_group_sizes.items()):
                st.markdown(f"<div class='highlight-red'>Total de {combo}: {count}</div>", unsafe_allow_html=True)
            styled_combinados = combinados_result.style.applymap(lambda x: 'color: red;' if isinstance(x, int) and x >= 580 else '', subset=['Occupied Seats'])
            st.dataframe(styled_combinados, use_container_width=True)
            st.download_button("Baixar Operações Combinadas", to_excel(combinados_result), file_name="operacoes_combinadas.xlsx")
        else:
            st.write("Nenhuma operação combinada identificada.")
    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")

import plotly.graph_objects as go

if rima_file is not None:
    try:
        # Carregar e preparar os dados
        if "rima_data" not in st.session_state:
            rima_data = pd.read_excel(rima_file)
            rima_data['PAX_LOCAL'] = pd.to_numeric(rima_data['PAX_LOCAL'], errors='coerce').fillna(0)
            rima_data['PAX_CONEXAO_DOMESTICO'] = pd.to_numeric(rima_data['PAX_CONEXAO_DOMESTICO'], errors='coerce').fillna(0)
            st.session_state["rima_data"] = rima_data

        rima_data = st.session_state["rima_data"]

        # Filtrar companhias desejadas
        valid_companies = ['AZU', 'GLO', 'PAM', 'TAM']
        df_filtered = rima_data[rima_data['AERONAVE_OPERADOR'].isin(valid_companies)].copy()

        # Calcular total de passageiros por companhia
        df_filtered['TOTAL_PAX'] = df_filtered['PAX_LOCAL'] + df_filtered['PAX_CONEXAO_DOMESTICO']
        company_pax = df_filtered.groupby('AERONAVE_OPERADOR')['TOTAL_PAX'].sum().reset_index()

        # Calcular o total geral
        total_geral = company_pax['TOTAL_PAX'].sum()

        # Adicionar coluna de percentual
        company_pax['PERCENTUAL'] = (company_pax['TOTAL_PAX'] / total_geral) * 100

        # Definir cores fixas para as companhias
        color_map = {
            'AZU': '#0073e6',  # Azul
            'GLO': '#ff7f0e',  # Laranja
            'TAM': '#d62728',  # Vermelho
            'PAM': '#ffdd44'   # Amarelo
        }

        # Criar gráfico de barras
        fig_bar = go.Figure()
        for _, row in company_pax.iterrows():
            total_pax_formatado = f"{row['TOTAL_PAX']:,.0f}".replace(",", ".")  # Formatar número corretamente
            texto = f"<b>{total_pax_formatado} - {row['PERCENTUAL']:.1f}%</b>"  # Texto em negrito
            
            fig_bar.add_trace(go.Bar(
                x=[row['AERONAVE_OPERADOR']],
                y=[row['TOTAL_PAX']],
                text=texto,
                textposition='inside',  # Dentro da barra
                marker_color=color_map.get(row['AERONAVE_OPERADOR'], '#333333'),
                textfont=dict(size=14, color="white")  # Ajusta a cor do texto
            ))

        fig_bar.update_layout(
            title="Passageiros Embarcados por Companhia",
            xaxis_title="Companhia Aérea",
            yaxis_title="Total de Passageiros",
            template="plotly_white",
            showlegend=False,
            xaxis=dict(showgrid=False),  # Remove grade do eixo X
            yaxis=dict(showgrid=False)   # Remove grade do eixo Y
        )

        # Exibir gráfico
        st.plotly_chart(fig_bar, use_container_width=True)

        # Exibir total geral centralizado e em preto
        total_geral_formatado = f"{total_geral:,.0f}".replace(",", ".")  # Ajusta o formato numérico
        st.markdown(
            f"<h2 style='text-align: center; color: black;'><b>Total Geral de Passageiros: {total_geral_formatado}</b></h2>",
            unsafe_allow_html=True
        )

    except Exception as e:
        st.error(f"Erro ao analisar passageiros embarcados: {e}")

import plotly.graph_objects as go
import streamlit as st

# Verificar se o arquivo já foi carregado
if rima_file is not None:
    try:
        # Recuperar os dados carregados anteriormente
        df_filtered = rima_data.copy()  # Agora considera todas as companhias aéreas

        # 📌 Criar seleção de companhia aérea com botões de opção (radio)
        companhia_selecionada = st.radio(
            "Selecione a Companhia Aérea",
            ["Todos"] + list(df_filtered["AERONAVE_OPERADOR"].unique()),
            horizontal=True  # Deixa os botões lado a lado
        )

        # 📌 Filtrar os dados conforme a seleção
        if companhia_selecionada == "Todos":
            df_box_filtered = df_filtered
        else:
            df_box_filtered = df_filtered[df_filtered["AERONAVE_OPERADOR"] == companhia_selecionada]

        # 📌 Contar quantas vezes cada BOX foi utilizado (independentemente de passageiros)
        df_box_summary = df_box_filtered.groupby("BOX").size().reset_index(name="TOTAL_UTILIZACOES")

        # 📌 Calcular percentual dentro do total
        total_box_geral = df_box_summary["TOTAL_UTILIZACOES"].sum()
        df_box_summary["PERCENTUAL"] = (df_box_summary["TOTAL_UTILIZACOES"] / total_box_geral) * 100

        # 📌 Criar gráfico de barras para utilização de posição (BOX)
        fig_box = go.Figure()
        for _, row in df_box_summary.iterrows():
            total_utilizacoes_formatado = f"{row['TOTAL_UTILIZACOES']:,.0f}".replace(",", ".")
            texto = f"<b>{total_utilizacoes_formatado} ({row['PERCENTUAL']:.1f}%)</b>"

            fig_box.add_trace(go.Bar(
                x=[row["BOX"]],
                y=[row["TOTAL_UTILIZACOES"]],
                text=texto,
                textposition="inside",
                marker_color="#17becf",  # Azul-claro para posição (BOX)
                textfont=dict(size=14, color="white")
            ))

        fig_box.update_layout(
            title=f"Utilização de Posição (BOX) - {companhia_selecionada}",
            xaxis_title="BOX",
            yaxis_title="Total de Utilizações",
            template="plotly_white",
            showlegend=False,
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=False)
        )

        # 📌 Exibir gráfico
        st.plotly_chart(fig_box, use_container_width=True)

    except Exception as e:
        st.error(f"Erro ao processar o gráfico de utilização de posição: {e}")

import plotly.express as px
import streamlit as st

# 📌 Garantir que os dados estejam carregados no estado da sessão
if "rima_data" not in st.session_state:
    st.stop()

# 📌 Recuperar os dados carregados
rima_data = st.session_state["rima_data"]

# 📌 Criar o dataframe filtrado e armazená-lo no session_state se ainda não estiver salvo
if "df_filtered" not in st.session_state:
    df_filtered = rima_data.copy()  # Considera todas as companhias aéreas
    st.session_state["df_filtered"] = df_filtered
else:
    df_filtered = st.session_state["df_filtered"]

# 📌 Criar layout com colunas para organizar os filtros lado a lado
col1, col2 = st.columns([1, 2])

with col1:
    movimento_tipo = st.radio(
        "Selecione o Tipo de Movimento",
        ["TODOS", "POUSO", "DECOLAGEM"],
        horizontal=True
    )

with col2:
    companhia_selecionada_cab = st.radio(
        "Selecione a Companhia Aérea para o gráfico de cabeceira",
        ["Todos"] + list(df_filtered["AERONAVE_OPERADOR"].unique()),
        horizontal=True
    )

# 📌 Filtrar os dados conforme a seleção de companhia aérea
if companhia_selecionada_cab == "Todos":
    df_cab_filtered = df_filtered
else:
    df_cab_filtered = df_filtered[df_filtered["AERONAVE_OPERADOR"] == companhia_selecionada_cab]

# 📌 Filtrar os dados conforme a seleção de tipo de movimento
if movimento_tipo == "POUSO":
    df_cab_filtered = df_cab_filtered[df_cab_filtered["MOVIMENTO_TIPO"] == "P"]
elif movimento_tipo == "DECOLAGEM":
    df_cab_filtered = df_cab_filtered[df_cab_filtered["MOVIMENTO_TIPO"] == "D"]

# 📌 Verificar se há dados para exibir
if not df_cab_filtered.empty:
    # 📌 Contar total de operações por CABECEIRA
    df_cab_summary = df_cab_filtered.groupby("CABECEIRA").size().reset_index(name="TOTAL_OPERACOES")

    # 📌 Calcular total geral para exibir na legenda
    total_operacoes_geral = df_cab_summary["TOTAL_OPERACOES"].sum()

    # 📌 Criar rótulo personalizado com **TOTAL + PERCENTUAL**
    df_cab_summary["LABEL"] = df_cab_summary.apply(
        lambda row: f"<b>{row['TOTAL_OPERACOES']} ({(row['TOTAL_OPERACOES'] / total_operacoes_geral) * 100:.1f}%)</b>", axis=1
    )

    # 📌 Definir um mapa de cores suaves para cada cabeceira
    cores_suaves = px.colors.qualitative.Pastel  # Paleta de cores suaves
    num_cabeceiras = len(df_cab_summary["CABECEIRA"].unique())
    cor_map = {df_cab_summary["CABECEIRA"].iloc[i]: cores_suaves[i % len(cores_suaves)] for i in range(num_cabeceiras)}

    # 📌 Criar gráfico de pizza com cores suaves e layout refinado
    fig_pizza = px.pie(
        df_cab_summary,
        names="CABECEIRA",
        values="TOTAL_OPERACOES",
        title=f"Distribuição de Operações por Cabaceira - {companhia_selecionada_cab} ({movimento_tipo})",
        hole=0.4,  # Criando um efeito de "rosca" para melhor visualização
        color="CABECEIRA",
        color_discrete_map=cor_map  # Aplicar cores suaves
    )

    fig_pizza.update_traces(
        text=df_cab_summary["LABEL"],  # Aplica o rótulo formatado (Total + Percentual)
        textinfo="label+percent",  # Exibe tanto o rótulo quanto o percentual
        hoverinfo="label+percent",  # Mantém percentual no hover
        textfont=dict(size=14, color="black")  # Ajusta a cor e tamanho do texto
    )

    # 📌 Exibir gráfico atualizado
    st.plotly_chart(fig_pizza, use_container_width=True)
