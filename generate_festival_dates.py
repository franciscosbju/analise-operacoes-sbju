import pandas as pd
import streamlit as st
from datetime import timedelta
from io import BytesIO

# Configuração inicial da página
st.set_page_config(
    page_title="Análise de Operações e Passageiros",
    layout="wide"  # Define largura total
)

# Adicionar título na parte superior (alinhado à esquerda)
st.markdown("""
    <style>
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
        .upload-section {
            padding: 20px;
            border: 1px solid #cccccc;
            border-radius: 10px;
            background-color: #f9f9f9;
        }
        .highlight {
            color: red;
            text-decoration: underline;
        }
        .dataframe tbody tr th { display: none; }
        .dataframe { width: 100% !important; }
    </style>
    <div class="title">Análise de Operações e Passageiros - SBJU</div>
    <div class="subtitle">Operações simultâneas em intervalo de 45 minutos</div>
    <hr style="border: 1px solid #cccccc;">
""", unsafe_allow_html=True)

# Carregamento do arquivo
st.markdown(
    '<div class="upload-section"><b>Escolha um arquivo Excel para análise:</b></div>',
    unsafe_allow_html=True
)
uploaded_file = st.file_uploader("Carregue o arquivo (apenas Excel)", type=["xls", "xlsx"])

# Função para processar os dados
def find_consecutive_operations(data, operation_type):
    data_filtered = data[data['ArrDep'] == operation_type].copy()
    data_filtered['Time'] = pd.to_datetime(
        data_filtered['Time'].astype(str).str.zfill(4), format='%H%M', errors='coerce'
    ).dt.time
    data_filtered['DateTime'] = pd.to_datetime(data_filtered['Date'], format='%d/%m/%Y') + pd.to_timedelta(data_filtered['Time'].astype(str))
    data_filtered = data_filtered.sort_values(by='DateTime')

    consecutive_flights = []
    for i in range(len(data_filtered) - 2):
        first = data_filtered.iloc[i]
        second = data_filtered.iloc[i + 1]
        third = data_filtered.iloc[i + 2]

        if (second['DateTime'] - first['DateTime'] <= timedelta(minutes=45)) and \
           (third['DateTime'] - first['DateTime'] <= timedelta(minutes=45)):
            consecutive_flights.append({
                'First DateTime': first['DateTime'].strftime('%d/%m/%Y %H:%M'),
                'First Flight': f"{first['Airl.Desig']} {first['Fltno']}",
                'Second DateTime': second['DateTime'].strftime('%d/%m/%Y %H:%M'),
                'Second Flight': f"{second['Airl.Desig']} {second['Fltno']}",
                'Third DateTime': third['DateTime'].strftime('%d/%m/%Y %H:%M'),
                'Third Flight': f"{third['Airl.Desig']} {third['Fltno']}",
                'PAX': first['Seats'] + second['Seats'] + third['Seats']
            })

    return pd.DataFrame(consecutive_flights)

# Função para identificar operações combinadas (quádruplas)
def find_combined_operations(data):
    data['Time'] = pd.to_datetime(
        data['Time'].astype(str).str.zfill(4), format='%H%M', errors='coerce'
    ).dt.time
    data['DateTime'] = pd.to_datetime(data['Date'], format='%d/%m/%Y') + pd.to_timedelta(data['Time'].astype(str))
    data = data.sort_values(by='DateTime')

    combined_operations = []
    for i in range(len(data) - 3):
        first = data.iloc[i]
        second = data.iloc[i + 1]
        third = data.iloc[i + 2]
        fourth = data.iloc[i + 3]

        if (second['DateTime'] - first['DateTime'] <= timedelta(minutes=45)) and \
           (third['DateTime'] - first['DateTime'] <= timedelta(minutes=45)) and \
           (fourth['DateTime'] - first['DateTime'] <= timedelta(minutes=45)):

            pax_sum = first['Seats'] + second['Seats'] + third['Seats'] + fourth['Seats']
            operations_sequence = [first['ArrDep'], second['ArrDep'], third['ArrDep'], fourth['ArrDep']]

            if operations_sequence.count('A') == 2 and operations_sequence.count('D') == 2:
                combination_type = "Dois Pousos e Duas Decolagens"
            elif operations_sequence.count('A') == 3 and operations_sequence.count('D') == 1:
                combination_type = "Três Pousos e Uma Decolagem"
            elif operations_sequence.count('D') == 3 and operations_sequence.count('A') == 1:
                combination_type = "Três Decolagens e Um Pouso"
            else:
                continue

            combined_operations.append({
                'First DateTime': first['DateTime'].strftime('%d/%m/%Y %H:%M'),
                'First Flight': f"{first['Airl.Desig']} {first['Fltno']}",
                'Second DateTime': second['DateTime'].strftime('%d/%m/%Y %H:%M'),
                'Second Flight': f"{second['Airl.Desig']} {second['Fltno']}",
                'Third DateTime': third['DateTime'].strftime('%d/%m/%Y %H:%M'),
                'Third Flight': f"{third['Airl.Desig']} {third['Fltno']}",
                'Fourth DateTime': fourth['DateTime'].strftime('%d/%m/%Y %H:%M'),
                'Fourth Flight': f"{fourth['Airl.Desig']} {fourth['Fltno']}",
                'Combination Type': combination_type,
                'PAX': pax_sum
            })

    return pd.DataFrame(combined_operations)

# Função para gerar arquivo Excel
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Dados')
    processed_data = output.getvalue()
    return processed_data

# Função para estilizar as linhas
def highlight_pax(value, threshold):
    if isinstance(value, int) and value >= threshold:
        return 'color: red;'
    return ''

if uploaded_file is not None:
    try:
        data = pd.read_excel(uploaded_file)
        invalid_codes = ['9', '99', '999', '9999']
        counts = {code: len(data[data['Time'] == int(code)]) for code in invalid_codes if int(code) in data['Time'].unique()}
        for code, count in counts.items():
            st.markdown(
                f"<h4 style='color: red;'>Total de Operações Código {code}: {count}</h4>",
                unsafe_allow_html=True
            )

        data = data[['ArrDep', 'Airl.Desig', 'Fltno', 'Time', 'Date', 'Seats']].copy()

        st.subheader("Pousos Consecutivos (A):")
        consecutive_arrivals = find_consecutive_operations(data, 'A')
        if consecutive_arrivals.empty:
            st.write("Esta análise não identificou a ocorrência de Três Pousos Consecutivos.")
        else:
            total_above_484 = len(consecutive_arrivals[consecutive_arrivals['PAX'] >= 484])
            st.markdown(f"**Total de Operações Consecutivas (Três Pousos): {len(consecutive_arrivals)}**")
            st.markdown(f"<span class='highlight'>Total de Operações Superior a 484 PAX: {total_above_484}</span>", unsafe_allow_html=True)
            styled_arrivals = consecutive_arrivals.style.applymap(lambda x: highlight_pax(x, 484), subset=['PAX'])
            st.dataframe(styled_arrivals, use_container_width=True)
            st.download_button(
                label="Download Arquivo (Pousos) em Excel",
                data=to_excel(consecutive_arrivals),
                file_name="Pousos_Consecutivos.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        st.subheader("Decolagens Consecutivas (D):")
        consecutive_departures = find_consecutive_operations(data, 'D')
        if consecutive_departures.empty:
            st.write("Esta análise não identificou a ocorrência Três Decolagens Consecutivas.")
        else:
            total_above_484 = len(consecutive_departures[consecutive_departures['PAX'] >= 484])
            st.markdown(f"**Total de Operações Consecutivas (Três Decolagens): {len(consecutive_departures)}**")
            st.markdown(f"<span class='highlight'>Total de Operações Superior a 484 PAX: {total_above_484}</span>", unsafe_allow_html=True)
            styled_departures = consecutive_departures.style.applymap(lambda x: highlight_pax(x, 484), subset=['PAX'])
            st.dataframe(styled_departures, use_container_width=True)
            st.download_button(
                label="Download Arquivo (Decolagens) em Excel",
                data=to_excel(consecutive_departures),
                file_name="Decolagens_Consecutivas.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        st.subheader("Operações Combinadas (Quádruplas):")
        combined_operations = find_combined_operations(data)
        if combined_operations.empty:
            st.write("Esta análise não identificou a ocorrência de operações quádruplas.")
        else:
            total_above_580_dd = len(combined_operations[(combined_operations['PAX'] >= 580) & (combined_operations['Combination Type'] == "Dois Pousos e Duas Decolagens")])
            total_above_580_tdp = len(combined_operations[(combined_operations['PAX'] >= 580) & (combined_operations['Combination Type'] == "Três Decolagens e Um Pouso")])
            total_above_580_tpd = len(combined_operations[(combined_operations['PAX'] >= 580) & (combined_operations['Combination Type'] == "Três Pousos e Uma Decolagem")])

            st.markdown(f"**Total de Operações Combinadas: {len(combined_operations)}**")
            st.markdown(f"<span class='highlight'>Total de Operações Superior a 580 PAX (Dois Pousos e Duas Decolagens): {total_above_580_dd}</span>", unsafe_allow_html=True)
            st.markdown(f"<span class='highlight'>Total de Operações Superior a 580 PAX (Três Decolagens e Um Pouso): {total_above_580_tdp}</span>", unsafe_allow_html=True)
            st.markdown(f"<span class='highlight'>Total de Operações Superior a 580 PAX (Três Pousos e Uma Decolagem): {total_above_580_tpd}</span>", unsafe_allow_html=True)

            styled_combined = combined_operations.style.applymap(lambda x: highlight_pax(x, 580), subset=['PAX'])
            st.dataframe(styled_combined, use_container_width=True)
            st.download_button(
                label="Download Arquivo (Operações Combinadas) em Excel",
                data=to_excel(combined_operations),
                file_name="Operacoes_Combinadas.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")

# NOVA FUNCIONALIDADE: Identificar dias com 4 ou mais posições ocupadas
if uploaded_file is not None:
    try:
        st.subheader("Datas Com 04 ou Mais Posições Ocupadas:")

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
            st.markdown(f"<div style='color: red; font-weight: bold;'>Total de Voos Pernoites: {total_pernoite}</div>", unsafe_allow_html=True)

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
