import pandas as pd
import streamlit as st
from datetime import timedelta
from io import BytesIO

# Ajustar o tamanho do título
st.markdown("<h2 style='text-align: center;'>Análise de Operações SBJU (ARR + DEP)</h2>", unsafe_allow_html=True)

# Função para processar os dados
def find_consecutive_operations(data, operation_type):
    # Filtrar por tipo de operação (A ou D)
    data_filtered = data[data['ArrDep'] == operation_type].copy()

    # Ajustar o formato do horário
    data_filtered['Time'] = pd.to_datetime(
        data_filtered['Time'].astype(str).str.zfill(4), format='%H%M', errors='coerce'
    ).dt.time
    data_filtered['DateTime'] = pd.to_datetime(data_filtered['Date'], format='%d/%m/%Y') + pd.to_timedelta(data_filtered['Time'].astype(str))
    data_filtered = data_filtered.sort_values(by='DateTime')

    # Encontrar operações consecutivas em intervalo de 45 minutos
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

            # Identificar combinações específicas
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
    if isinstance(value, int) and value > threshold:
        return 'color: red;'
    return ''

# CSS personalizado
st.markdown(
    """
    <style>
    .dataframe tbody tr th { display: none; }
    .dataframe { width: 100% !important; }
    </style>
    """,
    unsafe_allow_html=True
)

# Upload do arquivo
uploaded_file = st.file_uploader("Carregue o arquivo (apenas Excel)", type=["xls", "xlsx"])

if uploaded_file is not None:
    try:
        # Ler o arquivo Excel
        data = pd.read_excel(uploaded_file)

        # Contar valores inválidos na coluna Time
        invalid_codes = ['9', '99', '999', '9999']
        counts = {code: len(data[data['Time'] == int(code)]) for code in invalid_codes if int(code) in data['Time'].unique()}
        for code, count in counts.items():
            st.markdown(
                f"<h4 style='color: red;'>Total de Operações Código {code}: {count}</h4>",
                unsafe_allow_html=True
            )

        # Filtrar e formatar colunas necessárias
        data = data[['ArrDep', 'Airl.Desig', 'Fltno', 'Time', 'Date', 'Seats']].copy()

        # Processar pousos (A)
        st.subheader("Pousos Consecutivos (A):")
        consecutive_arrivals = find_consecutive_operations(data, 'A')
        if consecutive_arrivals.empty:
            st.write("Não Identificado Movimentações de Três Pousos Consecutivos.")
        else:
            styled_arrivals = consecutive_arrivals.style.applymap(lambda x: highlight_pax(x, 484), subset=['PAX'])
            st.dataframe(styled_arrivals.set_table_styles(
                [{'selector': 'th', 'props': [('text-align', 'center')]},
                 {'selector': 'td', 'props': [('text-align', 'center')]}]
            ), use_container_width=True)
            st.write(f"**Total de Operações Consecutivas (Três Pousos): {len(consecutive_arrivals)}**")

            # Botão para download do Excel (Pousos)
            st.download_button(
                label="Download Arquivo (Pousos) em Excel",
                data=to_excel(consecutive_arrivals),
                file_name="Pousos_Consecutivos.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        # Processar decolagens (D)
        st.subheader("Decolagens Consecutivas (D):")
        consecutive_departures = find_consecutive_operations(data, 'D')
        if consecutive_departures.empty:
            st.write("Não Identificado Movimentações de Três Decolagens Consecutivas.")
        else:
            styled_departures = consecutive_departures.style.applymap(lambda x: highlight_pax(x, 484), subset=['PAX'])
            st.dataframe(styled_departures.set_table_styles(
                [{'selector': 'th', 'props': [('text-align', 'center')]},
                 {'selector': 'td', 'props': [('text-align', 'center')]}]
            ), use_container_width=True)
            st.write(f"**Total de Operações Consecutivas (Três Decolagens): {len(consecutive_departures)}**")

            # Botão para download do Excel (Decolagens)
            st.download_button(
                label="Download Arquivo (Decolagens) em Excel",
                data=to_excel(consecutive_departures),
                file_name="Decolagens_Consecutivas.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        # Processar operações combinadas (quádruplas)
        st.subheader("Operações Combinadas (Quádruplas):")
        combined_operations = find_combined_operations(data)
        if combined_operations.empty:
            st.write("Esta análise não identificou a ocorrência de operações quádruplas.")
        else:
            styled_combined = combined_operations.style.applymap(lambda x: highlight_pax(x, 580), subset=['PAX'])
            st.dataframe(styled_combined.set_table_styles(
                [{'selector': 'th', 'props': [('text-align', 'center')]},
                 {'selector': 'td', 'props': [('text-align', 'center')]}]
            ), use_container_width=True)
            st.write(f"**Total de Operações Combinadas: {len(combined_operations)}**")

            # Botão para download do Excel (Operações Combinadas)
            st.download_button(
                label="Download Arquivo (Operações Combinadas) em Excel",
                data=to_excel(combined_operations),
                file_name="Operacoes_Combinadas.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")
