import pandas as pd
import streamlit as st
from datetime import timedelta
from io import BytesIO
import matplotlib.pyplot as plt
import seaborn as sns

# Configuração inicial da página
st.set_page_config(
    page_title="Análise de Operações e Passageiros",
    layout="wide"
)

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
            width: 250px;  /* Aumente o tamanho aqui */
            max-width: 100%;  /* Mantém a proporção original */
            height: auto;
        }
        .stats-container {
            display: flex;
            justify-content: space-around;
            margin-top: 20px;
        }
        .stat {
            text-align: center;
            font-size: 20px;
            color: #333333;
        }
        .stat-title {
            font-weight: bold;
            color: #666666;
        }
        .general-stats {
            text-align: center;
            font-size: 22px;
            margin-top: 30px;
            color: #333333;
            font-weight: bold;
        }
    </style>
    <div class="header-container">
        <div>
            <div class="title">Análise de Operações e Passageiros - SBJU</div>
            <div class="subtitle">Operações simultâneas em intervalo de 45 minutos</div>
        </div>
        <img class="logo" src="https://i.imgur.com/YetM1cb.png" alt="Logotipo">
    </div>
    <hr style="border: 1px solid #cccccc;">
""", unsafe_allow_html=True)

# Carregamento do arquivo
st.markdown(
    "<div style='color: red; font-weight: bold;'>Escolha um arquivo Excel para análise da Malha:</div>", 
    unsafe_allow_html=True
)
uploaded_file = st.file_uploader("Carregue o arquivo (apenas Excel)", type=["xls", "xlsx"])

# Controle de abas
selected_tab = st.selectbox("", ["Operações & Passageiros", "Gráficos por Companhia Aérea"])

if selected_tab == "Operações & Passageiros":
    if uploaded_file is not None:
        st.subheader("Operações e Passageiros")
        st.write("Análise de operações e passageiros carregada.")
    else:
        st.subheader("Operações e Passageiros")
        st.write("Insira aqui a análise de operações e passageiros.")

if selected_tab == "Gráficos por Companhia Aérea":
    if uploaded_file is not None:
        try:
            # Carregar os dados
            data = pd.read_excel(uploaded_file)

            # Verificar colunas necessárias
            required_columns = ['Airl.Desig', 'ArrDep', 'Seats', 'Date']
            if not all(col in data.columns for col in required_columns):
                st.error("O arquivo não possui as colunas necessárias para a análise.")
            else:
                # Preparar os dados para o gráfico
                data['Date'] = pd.to_datetime(data['Date'], format='%d/%m/%Y')
                data['Month'] = data['Date'].dt.to_period('M').astype(str)

                monthly_operations = data.groupby(['Month', 'Airl.Desig'])['ArrDep'].count().unstack(fill_value=0)
                monthly_passengers = data.groupby(['Month', 'Airl.Desig'])['Seats'].sum().unstack(fill_value=0)

                # Substituir códigos de companhias
                airline_mapping = {'AD': 'AZUL', 'G3': 'GOL', 'JJ': 'LATAM'}
                monthly_operations.rename(columns=airline_mapping, inplace=True)
                monthly_passengers.rename(columns=airline_mapping, inplace=True)

                # Gráfico de operações e passageiros lado a lado
                st.subheader("Gráficos por Companhia Aérea")
                fig, axes = plt.subplots(1, 2, figsize=(16, 6))

                # Adicionar espaço no topo para evitar sobreposição dos rótulos
                axes[0].set_ylim(0, monthly_operations.values.max() * 1.1)
                monthly_operations.plot(kind='bar', ax=axes[0], color=['blue', 'orange', 'red'], legend=False)
                axes[0].set_title("Operações Mensais por Companhia Aérea")
                axes[0].set_xlabel("Mês")
                axes[0].set_ylabel("Número de Operações")
                axes[0].tick_params(axis='x', labelrotation=45)
                for container in axes[0].containers:
                    labels = [f"{int(val.get_height()):,}".replace(",", ".") for val in container]
                    axes[0].bar_label(container, labels=labels, label_type='edge', fontsize=8, rotation=90, padding=3)

                axes[1].set_ylim(0, monthly_passengers.values.max() * 1.1)
                monthly_passengers.plot(kind='bar', ax=axes[1], color=['blue', 'orange', 'red'], legend=False)
                axes[1].set_title("Passageiros Mensais por Companhia Aérea")
                axes[1].set_xlabel("Mês")
                axes[1].set_ylabel("Número de Passageiros")
                axes[1].tick_params(axis='x', labelrotation=45)
                for container in axes[1].containers:
                    labels = [f"{int(val.get_height()):,}".replace(",", ".") for val in container]
                    axes[1].bar_label(container, labels=labels, label_type='edge', fontsize=8, rotation=90, padding=3)

                # Ajustar legenda
                handles, labels = axes[1].get_legend_handles_labels()
                fig.legend(handles, labels, loc='upper center', ncol=3, title="Companhia Aérea", fontsize=10)
                st.pyplot(fig)

                # Estatísticas gerais por companhia aérea
                st.subheader("Estatísticas Gerais por Companhia Aérea")
                stats_operations = monthly_operations.sum()
                stats_passengers = monthly_passengers.sum()

                st.markdown("""
                <div class="stats-container">
                    <div class="stat">
                        <div class="stat-title">Total de Operações AZUL</div>
                        <div>{}</div>
                    </div>
                    <div class="stat">
                        <div class="stat-title">Total de Operações GOL</div>
                        <div>{}</div>
                    </div>
                    <div class="stat">
                        <div class="stat-title">Total de Operações LATAM</div>
                        <div>{}</div>
                    </div>
                </div>
                <div class="stats-container">
                    <div class="stat">
                        <div class="stat-title">Total de Passageiros AZUL</div>
                        <div>{}</div>
                    </div>
                    <div class="stat">
                        <div class="stat-title">Total de Passageiros GOL</div>
                        <div>{}</div>
                    </div>
                    <div class="stat">
                        <div class="stat-title">Total de Passageiros LATAM</div>
                        <div>{}</div>
                    </div>
                </div>
                <div class="general-stats">
                    <div>Total Geral de Operações: {}</div>
                    <div>Total Geral de Passageiros: {}</div>
                </div>
                """.format(
                    f"{stats_operations['AZUL']:,}".replace(',', '.'),
                    f"{stats_operations['GOL']:,}".replace(',', '.'),
                    f"{stats_operations['LATAM']:,}".replace(',', '.'),
                    f"{stats_passengers['AZUL']:,}".replace(',', '.'),
                    f"{stats_passengers['GOL']:,}".replace(',', '.'),
                    f"{stats_passengers['LATAM']:,}".replace(',', '.'),
                    f"{stats_operations.sum():,}".replace(',', '.'),
                    f"{stats_passengers.sum():,}".replace(',', '.')
                ), unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Erro ao processar o arquivo: {e}")
    else:
        st.warning("Por favor, carregue um arquivo Excel para realizar a análise.")

# Mantém o código original intacto abaixo deste bloco

def find_consecutive_operations(data, operation_type):
    data_filtered = data[data['ArrDep'] == operation_type].copy()
    data_filtered['Time'] = pd.to_datetime(
        data_filtered['Time'].astype(str).str.zfill(4), format='%H%M', errors='coerce'
    ).dt.time
    data_filtered['DateTime'] = pd.to_datetime(data_filtered['Date'], format='%d/%m/%Y') + pd.to_timedelta(data_filtered['Time'].astype(str))
    data_filtered = data_filtered.sort_values(by='DateTime')

    consecutive_flights = []
    total_counts = {}
    
    for i in range(len(data_filtered)):
        group = [data_filtered.iloc[i]]
        total_pax = data_filtered.iloc[i]['Seats']

        for j in range(i + 1, len(data_filtered)):
            if (data_filtered.iloc[j]['DateTime'] - group[0]['DateTime']) <= timedelta(minutes=45):
                group.append(data_filtered.iloc[j])
                total_pax += data_filtered.iloc[j]['Seats']
            else:
                break

        if len(group) >= 3:
            total_counts[len(group)] = total_counts.get(len(group), 0) + 1
            record = {}
            for idx, flight in enumerate(group):
                record[f'{idx+1}th DateTime'] = flight['DateTime'].strftime('%d/%m/%Y %H:%M')
                record[f'{idx+1}th Flight'] = f"{flight['Airl.Desig']} {flight['Fltno']} - {flight['Actyp']}"
            record['PAX'] = total_pax
            consecutive_flights.append(record)

    df = pd.DataFrame(consecutive_flights).fillna('---')
    if not df.empty and 'PAX' in df.columns:
        cols = [col for col in df.columns if col != 'PAX'] + ['PAX']
        df = df[cols]
    return df, total_counts

def find_combined_operations(data):
    data['Time'] = pd.to_datetime(
        data['Time'].astype(str).str.zfill(4), format='%H%M', errors='coerce'
    ).dt.time
    data['DateTime'] = pd.to_datetime(data['Date'], format='%d/%m/%Y') + pd.to_timedelta(data['Time'].astype(str))
    data = data.sort_values(by='DateTime')

    combined_operations = []
    total_counts = {}

    for i in range(len(data)):
        group = [data.iloc[i]]
        total_pax = data.iloc[i]['Seats']
        arrivals, departures = 0, 0

        for j in range(i + 1, len(data)):
            if (data.iloc[j]['DateTime'] - group[0]['DateTime']) <= timedelta(minutes=45):
                group.append(data.iloc[j])
                total_pax += data.iloc[j]['Seats']
            else:
                break

        if len(group) >= 4:
            arrivals = sum(1 for x in group if x['ArrDep'] == 'A')
            departures = sum(1 for x in group if x['ArrDep'] == 'D')

            if arrivals > 0 and departures > 0:
                combination_type = f"{arrivals} Pousos e {departures} Decolagens"
                total_counts[combination_type] = total_counts.get(combination_type, 0) + 1
                record = {}
                for idx, flight in enumerate(group):
                    arr_dep_symbol = "(A)" if flight['ArrDep'] == 'A' else "(D)"
                    record[f'{idx+1}th DateTime'] = flight['DateTime'].strftime('%d/%m/%Y %H:%M')
                    record[f'{idx+1}th Flight'] = f"{flight['Airl.Desig']} {flight['Fltno']} {arr_dep_symbol} - {flight['Actyp']}"
                record['Combination Type'] = combination_type
                record['PAX'] = total_pax
                combined_operations.append(record)

    # Reorganizando colunas: Combination Type e PAX no final
    df = pd.DataFrame(combined_operations).fillna('---')
    if not df.empty:
        cols = [col for col in df.columns if col not in ['Combination Type', 'PAX']]
        df = df[cols + ['Combination Type', 'PAX']]
    return df, total_counts

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Dados')
    return output.getvalue()

# Processamento do arquivo
if uploaded_file is not None:
    try:
        data = pd.read_excel(uploaded_file)

        # Mostrar total de operações com código 9, 99, 999 ou 9999
        codes_of_interest = [9, 99, 999, 9999]
        results = []  # Lista para armazenar os resultados encontrados

        for code in codes_of_interest:
            count = data[data['Time'] == code].shape[0]
            if count > 0:
                results.append((code, count))  # Adicionar código e quantidade encontrados

        # Exibir os resultados somente se houver pelo menos um código encontrado
        if len(results) > 0:
            st.subheader("Total de Operações com Código 9:")
            for code, count in results:
                st.markdown(f"<div class='highlight-red'>Total de Operações {code}: {count:02}</div>", unsafe_allow_html=True)

        # Pousos consecutivos
        st.subheader("Pousos Consecutivos (A):")
        consecutive_arrivals, total_counts_arrivals = find_consecutive_operations(data, 'A')
        if consecutive_arrivals.empty:
            st.markdown("<div class='highlight-bold'>Esta análise não identificou a ocorrência de Pousos Consecutivos.</div>", unsafe_allow_html=True)
        else:
            for count, total in sorted(total_counts_arrivals.items(), reverse=True):
                st.markdown(f"<div class='highlight-red'>Total de {count:02} Pousos Consecutivos: {total}</div>", unsafe_allow_html=True)
            styled_arrivals = consecutive_arrivals.style.applymap(
                lambda val: 'color: red;' if isinstance(val, int) and val >= 484 else '', subset=['PAX']
            )
            st.dataframe(styled_arrivals, use_container_width=True)
            st.download_button(
                label="Download Pousos Consecutivos",
                data=to_excel(consecutive_arrivals),
                file_name="Pousos_Consecutivos.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        # Decolagens consecutivas
        st.subheader("Decolagens Consecutivas (D):")
        consecutive_departures, total_counts_departures = find_consecutive_operations(data, 'D')
        if consecutive_departures.empty:
            st.markdown("<div class='highlight-bold'>Esta análise não identificou a ocorrência de Decolagens Consecutivas.</div>", unsafe_allow_html=True)
        else:
            for count, total in sorted(total_counts_departures.items(), reverse=True):
                st.markdown(f"<div class='highlight-red'>Total de {count:02} Decolagens Consecutivas: {total}</div>", unsafe_allow_html=True)
            styled_departures = consecutive_departures.style.applymap(
                lambda val: 'color: red;' if isinstance(val, int) and val >= 484 else '', subset=['PAX']
            )
            st.dataframe(styled_departures, use_container_width=True)
            st.download_button(
                label="Download Decolagens Consecutivas",
                data=to_excel(consecutive_departures),
                file_name="Decolagens_Consecutivas.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        # Operacoes combinadas
        st.subheader("Operações Combinadas:")
        combined_operations, total_counts_combined = find_combined_operations(data)
        if combined_operations.empty:
            st.markdown("<div class='highlight-bold'>Esta análise não identificou a ocorrência de Operações Combinadas.</div>", unsafe_allow_html=True)
        else:
            for combination, total in total_counts_combined.items():
                st.markdown(f"<div class='highlight-red'>Total de {combination}: {total}</div>", unsafe_allow_html=True)
            styled_combined = combined_operations.style.applymap(
                lambda val: 'color: red;' if isinstance(val, int) and val > 580 else '', subset=['PAX']
            )
            st.dataframe(styled_combined, use_container_width=True)
            st.download_button(
                label="Download Operações Combinadas",
                data=to_excel(combined_operations),
                file_name="Operacoes_Combinadas.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")

        # NOVA FUNCIONALIDADE: Identificar dias com 4 ou mais posições ocupadas
if uploaded_file is not None:
    try:
        st.subheader("Datas Com 04 ou Mais Posições Ocupadas (Somente Na Data):")

        # Carregar o arquivo e verificar as colunas
        data = pd.read_excel(uploaded_file)

        # Filtrar voos inválidos (com '9999', '999', '99', '9' no campo 'Time')
        data = data[~data['Time'].astype(str).isin(['9', '99', '999', '9999'])]

        # Ajustar 'Time' para formato HH:MM
        data['Time'] = pd.to_datetime(data['Time'].astype(str).str.zfill(4), format='%H%M', errors='coerce').dt.time

        # Garantir que 'Date' esteja no formato correto
        data['Date'] = pd.to_datetime(data['Date'], format='%d/%m/%Y', errors='coerce')

        # Combinar 'Date' e 'Time' para formar 'DateTime'
        data['DateTime'] = data['Date'] + pd.to_timedelta(data['Time'].astype(str))
        data = data.sort_values(by='DateTime')

        # Variáveis para acompanhar posições acumuladas
        rows = []

        for date, group in data.groupby('Date'):
            current_positions = 0  # Reset positions for each day

            # Processar os voos do dia
            for _, row in group.iterrows():
                if row['ArrDep'] == 'A':  # Incrementar posições apenas para 'A'
                    current_positions += 1

                    # Armazenar apenas quando houver 4 ou mais posições ocupadas
                    if current_positions >= 4:
                        rows.append({
                            'Date': row['Date'].strftime('%d/%m/%Y'),
                            'Time': row['Time'].strftime('%H:%M'),
                            'Flight': f"{row['Airl.Desig']} {row['Fltno']}",
                            'Positions': current_positions
                        })
                elif row['ArrDep'] == 'D':  # Decrementar posições apenas para 'D'
                    current_positions -= 1

        # Criar DataFrame final
        result_df = pd.DataFrame(rows)

        # Verificar se há dados
        if result_df.empty:
            st.write("Nenhum dia com 4 ou mais posições ocupadas foi identificado.")
        else:
            # Calcular totais dinâmicos
            total_positions = result_df['Positions'].value_counts().sort_index()

            # Exibir os totais de forma dinâmica
            for positions, count in total_positions.items():
                st.markdown(f"<div style='color: red; font-weight: bold;'>Total de {positions:02d} Posições Ocupadas: {count}</div>", unsafe_allow_html=True)

            # Estilizar o DataFrame
            def highlight_positions(val):
                return 'color: red;' if isinstance(val, int) and val >= 4 else ''

            # Renomear a coluna 'Flight' para 'Last Flight' e resetar o índice
            result_df_display = result_df.rename(columns={'Flight': 'Last Flight'}).reset_index(drop=True)

            # Exibir DataFrame com a coluna 'Last Flight' e 'Date' visíveis
            st.dataframe(
                result_df_display.style.applymap(highlight_positions, subset=['Positions']),
                use_container_width=True
            )

            # Botão de download com a coluna original 'Flight'
            st.download_button(
                label="Download Datas Com 04 ou Mais Posições Ocupadas",
                data=to_excel(result_df),
                file_name="Dias_Com_4_Posicoes.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"Erro ao processar a análise de posições: {e}")

# NOVA FUNCIONALIDADE: Identificar voos pernoites
if uploaded_file is not None:
    try:
        st.subheader("Voos Pernoites:")

        # Carregar o arquivo e verificar as colunas
        data = pd.read_excel(uploaded_file)

        # Ajustar 'Time' para formato HH:MM
        data['Time'] = pd.to_datetime(data['Time'].astype(str).str.zfill(4), format='%H%M', errors='coerce').dt.time
        data = data.dropna(subset=['Time'])  # Remove linhas onde 'Time' é inválido

        # Garantir que 'Date' esteja no formato correto
        data['Date'] = pd.to_datetime(data['Date'], format='%d/%m/%Y', errors='coerce')

        # Inicializar lista para armazenar os resultados de voos pernoite
        pernoite_rows = []

        # Processar os dados agrupados por data
        for date, group in data.groupby('Date'):
            total_A = (group['ArrDep'] == 'A').sum()  # Contar total de chegadas (A)
            total_D = (group['ArrDep'] == 'D').sum()  # Contar total de partidas (D)

            # Determinar se há pernoite
            if total_A > total_D:
                pernoite_rows.append({
                    'Date': date.strftime('%d/%m/%Y'),
                    'Pernoite': 'SIM'
                })

        # Criar DataFrame final para voos pernoite
        pernoite_df = pd.DataFrame(pernoite_rows)

        # Verificar se há dados
        if pernoite_df.empty:
            st.write("Esta análise não identificou a ocorrência de voos pernoites.")
        else:
            # Calcular o total de voos pernoite
            total_pernoite = len(pernoite_df)
            st.markdown(f"<div style='color: red; font-weight: bold;'>Total de Datas Com Pernoites: {total_pernoite}</div>", unsafe_allow_html=True)

            # Exibir os resultados
            st.dataframe(pernoite_df.reset_index(drop=True), use_container_width=True)

            # Botão de download
            st.download_button(
                label="Download Voos Pernoites",
                data=to_excel(pernoite_df),
                file_name="Voos_Pernoites.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"Erro ao processar a análise de voos pernoites: {e}")
        
st.markdown("<hr style='border-top: 2px dashed red; margin: 20px 0;'>", unsafe_allow_html=True)

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
