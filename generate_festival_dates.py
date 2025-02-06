import pandas as pd
import streamlit as st
from datetime import timedelta
from io import BytesIO
import plotly.express as px

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

# Exibir controle de abas apenas quando o arquivo for carregado
if uploaded_file is not None:
    selected_tab = st.selectbox("", ["Operações & Passageiros", "Gráficos por Companhia Aérea"])

    if selected_tab == "Operações & Passageiros":
        st.subheader("Operações e Passageiros")
        st.write("Análise de operações e passageiros carregada.")

    elif selected_tab == "Gráficos por Companhia Aérea":
        try:
            # Carregar os dados
            data = pd.read_excel(uploaded_file)

            # Verificar colunas necessárias
            required_columns = ['Airl.Desig', 'ArrDep', 'Seats', 'Date', 'OrigDest']
            if not all(col in data.columns for col in required_columns):
                st.error("O arquivo não possui as colunas necessárias para a análise.")
            else:
                # Preparar os dados para o gráfico
                data['Date'] = pd.to_datetime(data['Date'], format='%d/%m/%Y')
                data['Month'] = data['Date'].dt.to_period('M').astype(str)

                monthly_operations = data.groupby(['Month', 'Airl.Desig'])['ArrDep'].count().unstack(fill_value=0)
                monthly_passengers = data.groupby(['Month', 'Airl.Desig'])['Seats'].sum().unstack(fill_value=0)

                # Substituir códigos de companhias
                airline_mapping = {'AD': 'AZUL', 'G3': 'GOL', 'JJ': 'LATAM', '7M': 'VOEPASS'}
                monthly_operations.rename(columns=airline_mapping, inplace=True)
                monthly_passengers.rename(columns=airline_mapping, inplace=True)

                # Adicionar coluna de texto formatado para rótulos
                monthly_operations_text = monthly_operations.reset_index().melt(
                    id_vars='Month',
                    var_name='Companhia Aérea',
                    value_name='Número de Operações'
                )
                monthly_operations_text['Número de Operações Formatado'] = monthly_operations_text[
                    'Número de Operações'
                ].apply(lambda x: f"{x:,}".replace(",", "."))

                monthly_passengers_text = monthly_passengers.reset_index().melt(
                    id_vars='Month',
                    var_name='Companhia Aérea',
                    value_name='Número de Passageiros'
                )
                monthly_passengers_text['Número de Passageiros Formatado'] = monthly_passengers_text[
                    'Número de Passageiros'
                ].apply(lambda x: f"{x:,}".replace(",", "."))

                # Gráficos usando Plotly
                st.subheader("Gráficos por Companhia Aérea")

                # Gráfico de operações mensais
                fig_operations = px.bar(
                    monthly_operations_text,
                    x='Month',
                    y='Número de Operações',
                    color='Companhia Aérea',
                    text='Número de Operações Formatado',
                    color_discrete_map={"AZUL": "blue", "GOL": "orange", "LATAM": "red", "VOEPASS": "#FFD700"}
                )
                fig_operations.update_traces(textposition='outside')
                fig_operations.update_layout(
                    xaxis_title="Mês",
                    yaxis_title="Operações Mensais Cias. Aéreas",  # Ajustado conforme solicitado
                    legend_title="Companhia Aérea",
                    barmode='group',
                    xaxis_showgrid=False,  # Remove linhas de grade do eixo X
                    yaxis_showgrid=False   # Remove linhas de grade do eixo Y
                )
                st.plotly_chart(fig_operations, use_container_width=True)

                # Gráfico de passageiros mensais
                fig_passengers = px.bar(
                    monthly_passengers_text,
                    x='Month',
                    y='Número de Passageiros',
                    color='Companhia Aérea',
                    text='Número de Passageiros Formatado',
                    color_discrete_map={"AZUL": "blue", "GOL": "orange", "LATAM": "red", "VOEPASS": "#FFD700"}
                )
                fig_passengers.update_traces(textposition='outside')
                fig_passengers.update_layout(
                    xaxis_title="Mês",
                    yaxis_title="Assentos Ofertados",  # Ajustado conforme solicitado
                    legend_title="Companhia Aérea",
                    barmode='group',
                    xaxis_showgrid=False,  # Remove linhas de grade do eixo X
                    yaxis_showgrid=False   # Remove linhas de grade do eixo Y
                )
                st.plotly_chart(fig_passengers, use_container_width=True)

                # Gráfico de total de operações por Origem e Destino
                operations_by_orig_dest = data.groupby('OrigDest')['ArrDep'].count().reset_index()
                total_operations = operations_by_orig_dest['ArrDep'].sum()
                operations_by_orig_dest['Percentual'] = operations_by_orig_dest['ArrDep'] / total_operations * 100
                operations_by_orig_dest['Texto'] = operations_by_orig_dest.apply(
                    lambda row: f"{row['ArrDep']} ({row['Percentual']:.1f}%)", axis=1
                )

                # Adicionar a coluna formatada com números com pontos
                operations_by_orig_dest['Texto'] = operations_by_orig_dest.apply(
                lambda row: f"{row['ArrDep']:,}".replace(",", ".") + f" ({row['Percentual']:.1f}%)", axis=1
                )

                # Ordenar do maior para o menor
                operations_by_orig_dest = operations_by_orig_dest.sort_values(by='ArrDep', ascending=False)

                fig_orig_dest = px.bar(
                    operations_by_orig_dest,
                    x='OrigDest',
                    y='ArrDep',
                    text='Texto',
                    title='',  # Removendo título do gráfico
                    labels={'OrigDest': 'Origem e Destino', 'ArrDep': 'Operações Origem/Destino'}  # Ajustado
                )

                # Configuração das cores e layout
                fig_orig_dest.update_traces(
                textposition='outside',
                marker_color='#27ae60'  # Cor personalizada para as barras
                )
                fig_orig_dest.update_layout(
                xaxis_title="Origem e Destino",
                yaxis_title="Operações Origem/Destino",  # Ajustado conforme solicitado
                barmode='group',
                xaxis_showgrid=False,  # Remove linhas de grade do eixo X
                yaxis_showgrid=False   # Remove linhas de grade do eixo Y
                )

                st.plotly_chart(fig_orig_dest, use_container_width=True)

                # Garantir que a coluna 'Actyp' seja tratada como texto
                data['Actyp'] = data['Actyp'].astype(str).str.strip()

                # Preparar os dados para o gráfico de modelos de aeronaves
                operations_by_actyp = data.groupby('Actyp')['ArrDep'].count().reset_index()
                total_operations_actyp = operations_by_actyp['ArrDep'].sum()
                operations_by_actyp['Percentual'] = operations_by_actyp['ArrDep'] / total_operations_actyp * 100
                operations_by_actyp['Texto'] = operations_by_actyp.apply(
                lambda row: f"{row['ArrDep']} ({row['Percentual']:.1f}%)", axis=1
                )

                # Adicionar a coluna formatada para exibir números com pontos
                operations_by_actyp['Texto'] = operations_by_actyp.apply(
                lambda row: f"{row['ArrDep']:,}".replace(",", ".") + f" ({row['Percentual']:.1f}%)", axis=1
                )

                # Ordenar os dados por frequência de operações (do maior para o menor)
                operations_by_actyp = operations_by_actyp.sort_values(by='ArrDep', ascending=False)

                # Criar o gráfico com Plotly
                fig_actyp = px.bar(
                operations_by_actyp,
                x='Actyp',
                y='ArrDep',
                text='Texto',
                title='',  # Removendo título do gráfico
                labels={'Actyp': 'Modelo de Aeronave', 'ArrDep': 'Operações por Modelo de Aeronave'}
                )

                # Forçar o eixo x a ser categórico
                fig_actyp.update_layout(
                xaxis=dict(
                type='category',  # Define o tipo do eixo como categórico
                categoryorder='array',  # Ordenar com base nos dados
                categoryarray=operations_by_actyp['Actyp'].tolist()  # Ordem baseada na lista dos modelos
                )
                )

                # Adicionar configurações visuais
                fig_actyp.update_traces(textposition='outside')
                fig_actyp.update_layout(
                xaxis_title="Modelo de Aeronave",
                yaxis_title="Operações por Modelo de Aeronave",
                barmode='group',
                xaxis_showgrid=False,
                yaxis_showgrid=False
                )

                # Exibir o gráfico no Streamlit
                st.plotly_chart(fig_actyp, use_container_width=True)

                # Processar a coluna 'Time' para extrair as horas
                def process_time_column(time):
                    time = str(int(time)).zfill(4)  # Corrigir formato e preencher com zeros
                    hour = int(time[:-2]) if len(time) > 2 else 0
                    return hour

                data['Hour'] = data['Time'].apply(process_time_column)

                # Filtro para tipos de operações (Pousos, Decolagens, Todos)
                operation_filter = st.radio(
                    "Selecione o tipo de operação:",
                    ["Todos", "Pousos", "Decolagens"],
                    horizontal=True
                )

                if operation_filter == "Pousos":
                    filtered_data = data[data['ArrDep'] == 'A']
                elif operation_filter == "Decolagens":
                    filtered_data = data[data['ArrDep'] == 'D']
                else:
                    filtered_data = data

                # Contar operações por intervalo de horas
                operations_by_hour = filtered_data.groupby('Hour').size().reset_index(name='Count')

                # Garantir que todas as horas de 0 a 23 sejam representadas
                all_hours = pd.DataFrame({'Hour': range(24)})
                operations_by_hour = all_hours.merge(operations_by_hour, on='Hour', how='left').fillna(0)

                # Criar o gráfico de barras
                fig_hours = px.bar(
                    operations_by_hour,
                    x='Hour',
                    y='Count',
                    labels={'Hour': 'Hora do Dia', 'Count': 'Quantidade de Operações'},
                )

                # Atualizar o layout do gráfico
                fig_hours.update_layout(
                    xaxis=dict(
                        tickmode='array',  # Definir manualmente os ticks
                        tickvals=list(range(24)),  # Definir os valores do eixo X de 0 a 23
                        ticktext=[f"{hour:02d}" for hour in range(24)],  # Formatar como 00, 01, ..., 23
                        title="Hora"
                    ),
                    yaxis=dict(
                        title="Operações por Hora"
                    ),
                    xaxis_showgrid=False,
                    yaxis_showgrid=False
                )

                # Adicionar rótulos acima das barras e personalizar a cor
                fig_hours.update_traces(
                    text=operations_by_hour['Count'].astype(int),  # Adicionar os valores como texto
                    textposition='outside',  # Posicionar os rótulos acima das barras
                    marker_color='#712ecc'  # Cor personalizada para as barras
                )

                # Exibir o gráfico no Streamlit
                st.plotly_chart(fig_hours, use_container_width=True)

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
    <div class="stat">
        <div class="stat-title">Total de Operações VOEPASS</div>
        <div>{}</div>
    </div>
</div>
<div class="stats-container">
    <div class="stat">
        <div class="stat-title">Total de Assentos AZUL</div>
        <div>{}</div>
    </div>
    <div class="stat">
        <div class="stat-title">Total de Assentos GOL</div>
        <div>{}</div>
    </div>
    <div class="stat">
        <div class="stat-title">Total de Assentos LATAM</div>
        <div>{}</div>
    </div>
    <div class="stat">
        <div class="stat-title">Total de Assentos VOEPASS</div>
        <div>{}</div>
    </div>
</div>
<div class="general-stats">
    <div>Total Geral de Operações: {}</div>
    <div>Total Geral de Assentos Ofertados: {}</div>
</div>
""".format(
    f"{stats_operations.get('AZUL', 0):,}".replace(',', '.'),
    f"{stats_operations.get('GOL', 0):,}".replace(',', '.'),
    f"{stats_operations.get('LATAM', 0):,}".replace(',', '.'),
    f"{stats_operations.get('VOEPASS', 0):,}".replace(',', '.'),  # Usa .get() para evitar erro
    f"{stats_passengers.get('AZUL', 0):,}".replace(',', '.'),
    f"{stats_passengers.get('GOL', 0):,}".replace(',', '.'),
    f"{stats_passengers.get('LATAM', 0):,}".replace(',', '.'),
    f"{stats_passengers.get('VOEPASS', 0):,}".replace(',', '.'),  # Usa .get() para evitar erro
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

# 📌 Criar botões de seleção (radio) para filtrar por companhia aérea
companhia_selecionada_cab = st.radio(
    "Selecione a Companhia Aérea para o gráfico de cabeceira",
    ["Todos"] + list(df_filtered["AERONAVE_OPERADOR"].unique()),
    horizontal=True
)

# 📌 Filtrar os dados conforme a seleção
if companhia_selecionada_cab == "Todos":
    df_cab_filtered = df_filtered
else:
    df_cab_filtered = df_filtered[df_filtered["AERONAVE_OPERADOR"] == companhia_selecionada_cab]

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
        title=f"Distribuição de Operações por Cabeceira - {companhia_selecionada_cab}",
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
