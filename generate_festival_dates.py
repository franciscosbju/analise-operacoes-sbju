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
    data_filtered['Time'] = pd.to_datetime(data_filtered['Time'].astype(str).str.zfill(4), format='%H%M').dt.time
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

# Função para gerar arquivo Excel
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Dados')
    processed_data = output.getvalue()
    return processed_data

# Upload do arquivo
uploaded_file = st.file_uploader("Carregue o arquivo (apenas Excel)", type=["xls", "xlsx"])

if uploaded_file is not None:
    try:
        # Ler o arquivo Excel
        data = pd.read_excel(uploaded_file)
        
        # Filtrar e formatar colunas necessárias
        data = data[['ArrDep', 'Airl.Desig', 'Fltno', 'Time', 'Date', 'Seats']].copy()
        
        # Processar pousos (A)
        st.subheader("Pousos Consecutivos (A):")
        consecutive_arrivals = find_consecutive_operations(data, 'A')
        st.dataframe(consecutive_arrivals.style.set_table_styles(
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
        st.dataframe(consecutive_departures.style.set_table_styles(
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
    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")
