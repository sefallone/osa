import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import io

# Configuración de la página
st.set_page_config(
    page_title="Dashboard Médico - Análisis Individual",
    page_icon="👨‍⚕️",
    layout="wide"
)

# Título de la aplicación
st.title("👨‍⚕️ Dashboard de Análisis Médico Individual")
st.markdown("---")

# Diccionario de profesionales con especialidad y tipo de médico
PROFESIONALES_INFO = {
    "FALLONE, JAN": {"especialidad": "HOMBRO Y CODO", "tipo": "CONSULTOR"},
    "ORTEGA RODRIGUEZ, JUAN PABLO": {"especialidad": "PIE Y TOBILLO", "tipo": "CONSULTOR"},
    "ESTEBAN FELIU, IGNACIO": {"especialidad": "MANO", "tipo": "CONSULTOR"},
    "PARDO I POL, ALBERT": {"especialidad": "MANO", "tipo": "ESPECIALISTA"},
    "ALCANTARA MORENO, EDGAR ALFREDO": {"especialidad": "HOMBRO Y CODO", "tipo": "ESPECIALISTA"},
    "RIUS MORENO, XAVIER": {"especialidad": "HOMBRO Y CODO", "tipo": "CONSULTOR"},
    "AGUILAR GARCIA, MARC": {"especialidad": "RODILLA", "tipo": "CONSULTOR"},
    "MAIO MÉNDEZ, TOMAS EDUARDO": {"especialidad": "RODILLA", "tipo": "ESPECIALISTA"},
    "MONSONET VILLA, PABLO": {"especialidad": "RODILLA", "tipo": "CONSULTOR"},
    "PUIGDELLIVOL GRIFELL, JORDI": {"especialidad": "RODILLA", "tipo": "CONSULTOR"},
    "CASACCIA, MARCELO AGUSTIN": {"especialidad": "RODILLA", "tipo": "CONSULTOR"}
}

def procesar_datos(df):
    """Procesa el DataFrame cargado"""
    df_procesado = df.copy()
    
    # Convertir columnas de fecha
    if 'Fecha del Servicio' in df_procesado.columns:
        df_procesado['Fecha del Servicio'] = pd.to_datetime(df_procesado['Fecha del Servicio'], errors='coerce')
    
    # Asegurar columnas numéricas
    if 'Importe HHMM' in df_procesado.columns:
        df_procesado['Importe HHMM'] = pd.to_numeric(df_procesado['Importe HHMM'], errors='coerce')
    
    if '% Liquidación' in df_procesado.columns:
        df_procesado['% Liquidación'] = pd.to_numeric(df_procesado['% Liquidación'], errors='coerce')
    
    # Crear columna de Importe Total (100%)
    if 'Importe HHMM' in df_procesado.columns and '% Liquidación' in df_procesado.columns:
        df_procesado['Importe Total'] = df_procesado.apply(
            lambda row: (row['Importe HHMM'] / (row['% Liquidación'] / 100)) 
            if pd.notnull(row['Importe HHMM']) and pd.notnull(row['% Liquidación']) and row['% Liquidación'] > 0 
            else row['Importe HHMM'], 
            axis=1
        )
    
    # Añadir información de especialidad y tipo de médico
    if 'Profesional' in df_procesado.columns:
        df_procesado['Subespecialidad'] = df_procesado['Profesional'].map(
            lambda x: PROFESIONALES_INFO.get(str(x).strip(), {}).get('especialidad', 'NO ESPECIFICADA')
        )
        
        df_procesado['Tipo Médico'] = df_procesado['Profesional'].map(
            lambda x: PROFESIONALES_INFO.get(str(x).strip(), {}).get('tipo', 'NO ESPECIFICADO')
        )
    
    return df_procesado

def calcular_promedio_subespecialidad(df, subespecialidad):
    """Calcula el promedio de facturación para una subespecialidad específica"""
    if subespecialidad not in df['Subespecialidad'].values:
        return 0, 0, 0
    
    # Filtrar por subespecialidad
    df_especialidad = df[df['Subespecialidad'] == subespecialidad]
    
    if df_especialidad.empty:
        return 0, 0, 0
    
    # Suma total del Importe HHMM para esa subespecialidad
    suma_total = df_especialidad['Importe HHMM'].sum()
    
    # Número de médicos únicos que facturaron en esa subespecialidad
    num_medicos = df_especialidad['Profesional'].nunique()
    
    # Calcular promedio
    promedio = suma_total / num_medicos if num_medicos > 0 else 0
    
    return promedio, suma_total, num_medicos

def calcular_a_cobrar_individual(df_medico, promedio_subespecialidad):
    """Calcula los KPIs para un médico individual"""
    if df_medico.empty:
        return None
    
    # Estadísticas básicas
    total_registros = len(df_medico)
    importe_total = df_medico['Importe Total'].sum() if 'Importe Total' in df_medico.columns else 0
    importe_hhmm_total = df_medico['Importe HHMM'].sum() if 'Importe HHMM' in df_medico.columns else 0
    
    # Obtener tipo de médico
    tipo_medico = df_medico['Tipo Médico'].iloc[0] if 'Tipo Médico' in df_medico.columns else 'NO ESPECIFICADO'
    
    # Calcular % a cobrar y total a cobrar
    por_encima_promedio = importe_hhmm_total >= promedio_subespecialidad
    
    if tipo_medico == 'CONSULTOR':
        porcentaje_cobrar = 0.92 if por_encima_promedio else 0.88
    elif tipo_medico == 'ESPECIALISTA':
        porcentaje_cobrar = 0.90 if por_encima_promedio else 0.85
    else:
        porcentaje_cobrar = 0.90  # Por defecto
    
    total_a_cobrar = importe_hhmm_total * porcentaje_cobrar
    
    # CALCULAR NUEVOS KPIs
    # % OSA = 100% - % a Cobrar
    porcentaje_osa = 100 - (porcentaje_cobrar * 100)
    
    # A Cobrar OSA = Importe HHMM Total - Total a Cobrar
    a_cobrar_osa = importe_hhmm_total - total_a_cobrar
    
    return {
        'total_registros': total_registros,
        'importe_total': importe_total,
        'importe_hhmm_total': importe_hhmm_total,
        'promedio_subespecialidad': promedio_subespecialidad,
        'porcentaje_cobrar': porcentaje_cobrar * 100,  # En porcentaje
        'total_a_cobrar': total_a_cobrar,
        'porcentaje_osa': porcentaje_osa,  # NUEVO KPI
        'a_cobrar_osa': a_cobrar_osa,      # NUEVO KPI
        'tipo_medico': tipo_medico,
        'por_encima_promedio': por_encima_promedio
    }

def crear_dashboard_medico(df_medico, kpis, promedio_info):
    """Crea el dashboard específico para un médico"""
    
    # Header del médico
    nombre_medico = df_medico['Profesional'].iloc[0] if 'Profesional' in df_medico.columns else 'Médico'
    subespecialidad = df_medico['Subespecialidad'].iloc[0] if 'Subespecialidad' in df_medico.columns else 'No especificada'
    
    st.header(f"👨‍⚕️ {nombre_medico}")
    st.subheader(f"Subespecialidad: {subespecialidad}")
    
    # KPIs en 4 filas de 2 columnas (8 KPIs total)
    # Fila 1: Registros e Importes
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "💰 Facturado x Vithas",
            f"€{kpis['importe_total']:,.2f}",
            help="Importe total calculado al 100%"
        )
            
    with col2:
        st.metric(
            "💵 Cobrado x OSA",
            f"€{kpis['importe_hhmm_total']:,.2f}",
            help="Descontados % Vithas"
        )
          
    with co3:
        # Mostrar si está por encima o por debajo del promedio
        if kpis['por_encima_promedio']:
            delta_text = "↑ Por encima"
            delta_color = "normal"
        else:
            delta_text = "↓ Por debajo"
            delta_color = "inverse"
        
        st.metric(
            "📈 Promedio Subespecialidad",
            f"€{kpis['promedio_subespecialidad']:,.2f}",
            delta=delta_text,
            delta_color=delta_color,
            help=f"Promedio de {subespecialidad}: €{promedio_info['suma_total']:,.2f} / {promedio_info['num_medicos']} médicos"
        )

    with col4:
        st.metric(
            "📊 Total Registros",
            f"{kpis['total_registros']:,}",
            help="Número total de servicios prestados"
        )
        

    col5, col6 = st.columns(2)
    
    with col5:
        st.metric(
            "📋 % a Cobrar (Médico)",
            f"{kpis['porcentaje_cobrar']:.1f}%",
            help=f"{kpis['tipo_medico']} {'por encima' if kpis['por_encima_promedio'] else 'por debajo'} del promedio"
        )
    
    with col6:
        # NUEVO KPI: % OSA
        st.metric(
            "🏥 % OSA",
            f"{kpis['porcentaje_osa']:.1f}%",
            help="Porcentaje para OSA = 100% - % a Cobrar"
        )
    
    # Fila 4: Totales a cobrar
    col7, col8 = st.columns(2)
    
    with col7:
        st.metric(
            "💳 Total a Cobrar (Médico)",
            f"€{kpis['total_a_cobrar']:,.2f}",
            help=f"Calculado: €{kpis['importe_hhmm_total']:,.2f} × {kpis['porcentaje_cobrar']:.1f}%"
        )
    
    with col8:
        # NUEVO KPI: A Cobrar OSA
        st.metric(
            "💰 OSA se queda con:",
            f"€{kpis['a_cobrar_osa']:,.2f}",
            help=f"Calculado: €{kpis['importe_hhmm_total']:,.2f} - €{kpis['total_a_cobrar']:,.2f}"
        )
    
    st.markdown("---")
    
    # Resumen visual de distribución
    st.subheader("📊 Distribución del Importe HHMM")
    
    # Crear gráfico de barras para mostrar la distribución
    distribucion_data = {
        'Concepto': ['Médico', 'OSA'],
        'Monto': [kpis['total_a_cobrar'], kpis['a_cobrar_osa']],
        'Porcentaje': [kpis['porcentaje_cobrar'], kpis['porcentaje_osa']]
    }
    
    distribucion_df = pd.DataFrame(distribucion_data)
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        # Gráfico de barras para montos
        fig_montos = px.bar(
            distribucion_df,
            x='Concepto',
            y='Monto',
            title='Distribución por Monto (€)',
            color='Concepto',
            text_auto='.2f',
            color_discrete_map={'Médico': '#4CAF50', 'OSA': '#2196F3'}
        )
        fig_montos.update_layout(
            height=300,
            showlegend=False,
            yaxis_title='Monto (€)'
        )
        fig_montos.update_traces(texttemplate='€%{value:,.2f}', textposition='outside')
        st.plotly_chart(fig_montos, use_container_width=True)
    
    with col_chart2:
        # Gráfico de pastel para porcentajes
        fig_porcentajes = px.pie(
            distribucion_df,
            values='Porcentaje',
            names='Concepto',
            title='Distribución por Porcentaje',
            hole=0.4,
            color='Concepto',
            color_discrete_map={'Médico': '#4CAF50', 'OSA': '#2196F3'}
        )
        fig_porcentajes.update_layout(height=300, showlegend=True)
        fig_porcentajes.update_traces(textinfo='percent+label')
        st.plotly_chart(fig_porcentajes, use_container_width=True)
    
    # Información detallada del cálculo
    with st.expander("ℹ️ Detalles del cálculo completo", expanded=False):
        st.markdown(f"""
        ### 📝 **Cálculos Detallados para {nombre_medico}**
        
        **1. Promedio de la Subespecialidad ({subespecialidad}):**
        ```
        Suma total de facturación en {subespecialidad} por OSA: €{promedio_info['suma_total']:,.2f}
        Número de médicos que facturaron: {promedio_info['num_medicos']}
        Promedio = €{promedio_info['suma_total']:,.2f} ÷ {promedio_info['num_medicos']} = €{kpis['promedio_subespecialidad']:,.2f}
        ```
        
        **2. Posición del Médico:**
        - **{nombre_medico}** facturó: **€{kpis['importe_hhmm_total']:,.2f}**
        - Promedio de la subespecialidad: **€{kpis['promedio_subespecialidad']:,.2f}**
        - **Resultado:** {'POR ENCIMA' if kpis['por_encima_promedio'] else 'POR DEBAJO'} del promedio
        - **Tipo de médico:** {kpis['tipo_medico']}
        
        **3. Cálculo de Porcentajes:**
        - **% a Cobrar (Médico):** {kpis['porcentaje_cobrar']:.1f}%
          *(Basado en reglas: {kpis['tipo_medico']} {'por encima' if kpis['por_encima_promedio'] else 'por debajo'} del promedio)*
        - **% OSA:** 100% - {kpis['porcentaje_cobrar']:.1f}% = **{kpis['porcentaje_osa']:.1f}%**
        
        **4. Cálculo de Montos:**
        - **Importe Cobrado OSA:** €{kpis['importe_hhmm_total']:,.2f}
        - **Total a Cobrar (Médico):** €{kpis['importe_hhmm_total']:,.2f} × {kpis['porcentaje_cobrar']:.1f}% = **€{kpis['total_a_cobrar']:,.2f}**
        - **OSA se queda con:** €{kpis['importe_hhmm_total']:,.2f} - €{kpis['total_a_cobrar']:,.2f} = **€{kpis['a_cobrar_osa']:,.2f}**
        
           
    st.markdown("---")
    
    # Análisis por Tipo de Prestación
    st.subheader("📋 Análisis por Tipo de Prestación")
    
    if 'Descripción de Prestación' in df_medico.columns:
        # Métricas por tipo de prestación
        prestacion_analisis = df_medico.groupby('Descripción de Prestación').agg({
            'Importe HHMM': ['count', 'sum']
        }).reset_index()
        
        # Aplanar columnas multi-index
        prestacion_analisis.columns = ['Descripción de Prestación', 'Cantidad', 'Monto Total']
        
        # Calcular distribución porcentual para el médico
        prestacion_analisis['% Médico'] = (prestacion_analisis['Monto Total'] / kpis['importe_hhmm_total']) * 100
        prestacion_analisis['Médico Recibe'] = prestacion_analisis['Monto Total'] * (kpis['porcentaje_cobrar'] / 100)
        prestacion_analisis['OSA Recibe'] = prestacion_analisis['Monto Total'] * (kpis['porcentaje_osa'] / 100)
        
        # Crear dos columnas para las métricas
        col_metrics1, col_metrics2 = st.columns(2)
        
        with col_metrics1:
            st.markdown("**🏥 Unidades por Tipo de Prestación**")
            for _, row in prestacion_analisis.iterrows():
                st.metric(
                    label=row['Descripción de Prestación'],
                    value=f"{row['Cantidad']:,} unidades",
                    delta=None
                )
        
        with col_metrics2:
            st.markdown("**💰 Monto Cobrado por OSA y Tipo de Prestación**")
            for _, row in prestacion_analisis.iterrows():
                st.metric(
                    label=row['Descripción de Prestación'],
                    value=f"€{row['Monto Total']:,.2f}",
                    delta=None
                )
        
        # Gráficos de distribución por prestación
        col_chart3, col_chart4 = st.columns(2)
        
        with col_chart3:
            # Gráfico de cantidad
            fig_cantidad = px.pie(
                prestacion_analisis,
                values='Cantidad',
                names='Descripción de Prestación',
                title='Distribución de Unidades por Prestación',
                hole=0.4,
                color_discrete_sequence=px.colors.sequential.Viridis
            )
            fig_cantidad.update_layout(height=400)
            st.plotly_chart(fig_cantidad, use_container_width=True)
        
        with col_chart4:
            # Gráfico de monto con distribución Médico/OSA
            fig_distribucion = go.Figure(data=[
                go.Bar(name='Médico', x=prestacion_analisis['Descripción de Prestación'], 
                      y=prestacion_analisis['Médico Recibe'], marker_color='#4CAF50'),
                go.Bar(name='OSA', x=prestacion_analisis['Descripción de Prestación'], 
                      y=prestacion_analisis['OSA Recibe'], marker_color='#2196F3')
            ])
            
            fig_distribucion.update_layout(
                title='Distribución Médico vs OSA por Prestación',
                barmode='stack',
                height=400,
                xaxis_title='Tipo de Prestación',
                yaxis_title='Monto (€)',
                legend_title='Destino'
            )
            st.plotly_chart(fig_distribucion, use_container_width=True)
        
        # Tabla detallada con distribución
        st.markdown("**📊 Tabla Resumen por Tipo de Prestación**")
        prestacion_analisis['Monto Promedio'] = prestacion_analisis['Monto Total'] / prestacion_analisis['Cantidad']
        
        st.dataframe(
            prestacion_analisis,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Descripción de Prestación": "Tipo de Prestación",
                "Cantidad": st.column_config.NumberColumn(
                    "Unidades",
                    format="%d",
                    help="Número de servicios prestados"
                ),
                "Monto Total": st.column_config.NumberColumn(
                    "Monto Total OSA (€)",
                    format="€%.2f",
                    help="Suma del Importe HHMM"
                ),
                "Monto Promedio": st.column_config.NumberColumn(
                    "Promedio por Unidad (€)",
                    format="€%.2f",
                    help="Monto Total / Unidades"
                ),
                "Médico Recibe": st.column_config.NumberColumn(
                    "Médico Recibe (€)",
                    format="€%.2f",
                    help="Monto que recibe el médico"
                ),
                "OSA Recibe": st.column_config.NumberColumn(
                    "OSA Retiene (€)",
                    format="€%.2f",
                    help="Monto que recibe OSA"
                )
            }
        )
    
    st.markdown("---")
    
    # Tabla con todos los registros del médico
    with st.expander("📋 Ver todos los registros del médico", expanded=False):
        st.dataframe(
            df_medico,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Fecha del Servicio": st.column_config.DateColumn("Fecha"),
                "Descripción de Prestación": "Prestación",
                "Importe HHMM": st.column_config.NumberColumn(format="€%.2f"),
                "Importe Total": st.column_config.NumberColumn(format="€%.2f"),
                "% Liquidación": st.column_config.NumberColumn(format="%.0f%%")
            }
        )
    
    # Botón para descargar reporte del médico
    if st.button("📥 Descargar Reporte del Médico (Excel)", use_container_width=True, type="primary"):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Hoja 1: Datos del médico
            df_medico.to_excel(writer, index=False, sheet_name='Datos_Médico')
            
            # Hoja 2: Resumen por prestación
            if 'Descripción de Prestación' in df_medico.columns:
                prestacion_resumen = df_medico.groupby('Descripción de Prestación').agg({
                    'Importe HHMM': ['count', 'sum', 'mean'],
                    'Importe Total': 'sum'
                }).reset_index()
                prestacion_resumen.columns = ['Prestación', 'Unidades', 'Monto HHMM Total', 'Monto HHMM Promedio', 'Monto Total']
                prestacion_resumen['% Médico'] = (prestacion_resumen['Monto HHMM Total'] / kpis['importe_hhmm_total']) * 100
                prestacion_resumen['Médico Recibe'] = prestacion_resumen['Monto HHMM Total'] * (kpis['porcentaje_cobrar'] / 100)
                prestacion_resumen['OSA Recibe'] = prestacion_resumen['Monto HHMM Total'] * (kpis['porcentaje_osa'] / 100)
                prestacion_resumen.to_excel(writer, index=False, sheet_name='Resumen_Prestaciones')
            
            # Hoja 3: KPIs
            kpis_df = pd.DataFrame([{
                'Médico': nombre_medico,
                'Subespecialidad': subespecialidad,
                'Tipo Médico': kpis['tipo_medico'],
                'Total Registros': kpis['total_registros'],
                'Importe Total (100%)': kpis['importe_total'],
                'Importe HHMM Total': kpis['importe_hhmm_total'],
                'Promedio Subespecialidad': kpis['promedio_subespecialidad'],
                'Posición vs Promedio': 'Por encima' if kpis['por_encima_promedio'] else 'Por debajo',
                '% a Cobrar (Médico)': kpis['porcentaje_cobrar'],
                '% OSA': kpis['porcentaje_osa'],
                'Total a Cobrar (Médico)': kpis['total_a_cobrar'],
                'A Cobrar OSA': kpis['a_cobrar_osa']
            }])
            kpis_df.to_excel(writer, index=False, sheet_name='KPIs')
            
            # Hoja 4: Distribución general
            distribucion_df = pd.DataFrame({
                'Concepto': ['Total', 'Médico', 'OSA'],
                'Monto (€)': [kpis['importe_hhmm_total'], kpis['total_a_cobrar'], kpis['a_cobrar_osa']],
                'Porcentaje': [100, kpis['porcentaje_cobrar'], kpis['porcentaje_osa']],
                'Descripción': [
                    'Importe HHMM Total',
                    f'Médico recibe ({kpis["porcentaje_cobrar"]:.1f}%)',
                    f'OSA recibe ({kpis["porcentaje_osa"]:.1f}%)'
                ]
            })
            distribucion_df.to_excel(writer, index=False, sheet_name='Distribución')
        
        output.seek(0)
        
        st.download_button(
            label=f"⬇️ Descargar Reporte de {nombre_medico}",
            data=output,
            file_name=f"reporte_{nombre_medico.replace(', ', '_').replace(' ', '_')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

# [El resto del código permanece igual desde aquí...]
# Solo necesito copiar la función main() completa

def main():
    # Sidebar simplificado
    with st.sidebar:
        st.header("📁 Carga de Datos")
        
        uploaded_file = st.file_uploader(
            "Sube tu archivo Excel",
            type=['xlsx', 'xls']
        )
        
        df = None
        
        if uploaded_file is not None:
            try:
                df = pd.read_excel(uploaded_file)
                st.success(f"✅ Archivo cargado")
                st.info(f"📊 {len(df)} registros cargados")
            except Exception as e:
                st.error(f"Error al cargar el archivo: {e}")
                st.stop()
        else:
            # Usar datos de ejemplo del archivo proporcionado
            st.info("📋 Usando datos de ejemplo")
            
            # Crear datos de ejemplo basados en la estructura proporcionada
            sample_data = []
            
            # Datos para FALLONE, JAN
            for i in range(10):
                sample_data.append({
                    "Acreedor": "ORTHOPAEDIC SPECIALIST ALLIANCE SLU",
                    "Profesional": "FALLONE, JAN",
                    "Especialidad": "Traumatología y cir ortopédica",
                    "Clase aseguradora": "NAC",
                    "Aseguradora": "AXA SALUD",
                    "Nº de Episodio": 1013682955 + i,
                    "Nombre paciente": f"PACIENTE {i+1}",
                    "Fecha del Servicio": f"2025-12-{20 + i}",
                    "Hora del Servicio": "09:00:00",
                    "Tipo de Episodio": "Epis.ambulante",
                    "Tipo de Prestación": "HME",
                    "Tipo de Prestación 2": "CEX",
                    "Cantidad": 1,
                    "Código de Prestación": 1 if i % 2 == 0 else 2,
                    "Descripción de Prestación": "CONSULTA" if i % 2 == 0 else "REVISION",
                    "Importe HHMM": 19.6 + i,
                    "% Liquidación": 70,
                    "Nº Autofactura": f"26VBEF000004920{i}",
                    "Nº Factura del Episodio": f"BE26TI0000003{i}",
                    "Fecha de Liquidación": "2026-01-30"
                })
            
            # Datos para ORTEGA RODRIGUEZ, JUAN PABLO
            for i in range(8):
                sample_data.append({
                    "Acreedor": "ORTHOPAEDIC SPECIALIST ALLIANCE SLU",
                    "Profesional": "ORTEGA RODRIGUEZ, JUAN PABLO",
                    "Especialidad": "Traumatología y cir ortopédica",
                    "Clase aseguradora": "NAC",
                    "Aseguradora": "CIGNA SALUD",
                    "Nº de Episodio": 1013676822 + i,
                    "Nombre paciente": f"PACIENTE {i+11}",
                    "Fecha del Servicio": f"2025-12-{15 + i}",
                    "Hora del Servicio": "09:00:00",
                    "Tipo de Episodio": "Epis.ambulante",
                    "Tipo de Prestación": "HME",
                    "Tipo de Prestación 2": "CEX",
                    "Cantidad": 1,
                    "Código de Prestación": 1 if i % 3 == 0 else 2,
                    "Descripción de Prestación": "CONSULTA" if i % 3 == 0 else "REVISION",
                    "Importe HHMM": 21.0 + i,
                    "% Liquidación": 70,
                    "Nº Autofactura": f"26VBEF000004921{i}",
                    "Nº Factura del Episodio": f"BE25TI0000001{i}",
                    "Fecha de Liquidación": "2026-01-30"
                })
            
            # Datos para ESTEBAN FELIU, IGNACIO
            for i in range(6):
                sample_data.append({
                    "Acreedor": "ORTHOPAEDIC SPECIALIST ALLIANCE SLU",
                    "Profesional": "ESTEBAN FELIU, IGNACIO",
                    "Especialidad": "Traumatología y cir ortopédica",
                    "Clase aseguradora": "NAC",
                    "Aseguradora": "AXA SALUD",
                    "Nº de Episodio": 1013666452 + i,
                    "Nombre paciente": f"PACIENTE {i+21}",
                    "Fecha del Servicio": f"2025-12-{10 + i}",
                    "Hora del Servicio": "16:34:51",
                    "Tipo de Episodio": "Epis.ambulante",
                    "Tipo de Prestación": "DPI" if i % 2 == 0 else "HME",
                    "Tipo de Prestación 2": "ECO" if i % 2 == 0 else "CEX",
                    "Cantidad": 1,
                    "Código de Prestación": 1434 if i % 2 == 0 else 1,
                    "Descripción de Prestación": "ECOGRAFIA MUSCULAR O TENDINOSA" if i % 2 == 0 else "CONSULTA",
                    "Importe HHMM": 12.0 + i,
                    "% Liquidación": 40 if i % 2 == 0 else 70,
                    "Nº Autofactura": f"26VBEF000004922{i}",
                    "Nº Factura del Episodio": f"BE26TI0000004{i}",
                    "Fecha de Liquidación": "2026-01-30"
                })
            
            df = pd.DataFrame(sample_data)
        
        st.markdown("---")
        st.header("🔍 Filtros")
        
        if df is not None and not df.empty:
            df_procesado = procesar_datos(df)
            
            # Filtro por fecha
            if 'Fecha del Servicio' in df_procesado.columns:
                try:
                    min_date = df_procesado['Fecha del Servicio'].min().date()
                    max_date = df_procesado['Fecha del Servicio'].max().date()
                    
                    fecha_range = st.date_input(
                        "📅 Rango de Fechas",
                        value=(min_date, max_date),
                        min_value=min_date,
                        max_value=max_date
                    )
                    
                    if len(fecha_range) == 2:
                        mask = (df_procesado['Fecha del Servicio'].dt.date >= fecha_range[0]) & \
                               (df_procesado['Fecha del Servicio'].dt.date <= fecha_range[1])
                        df_procesado = df_procesado[mask]
                except:
                    pass
            
            # Filtro por médico
            if 'Profesional' in df_procesado.columns:
                try:
                    medicos_disponibles = sorted(df_procesado['Profesional'].dropna().unique().tolist())
                    
                    if medicos_disponibles:
                        medico_seleccionado = st.selectbox(
                            "👨‍⚕️ Seleccionar Médico",
                            medicos_disponibles,
                            help="Seleccione un médico para ver su análisis detallado"
                        )
                        
                        # Filtrar por médico seleccionado
                        df_medico = df_procesado[df_procesado['Profesional'] == medico_seleccionado]
                        
                        if not df_medico.empty:
                            # Obtener subespecialidad del médico
                            subespecialidad = df_medico['Subespecialidad'].iloc[0]
                            
                            # Calcular promedio de la subespecialidad
                            promedio_subespecialidad, suma_total, num_medicos = calcular_promedio_subespecialidad(df_procesado, subespecialidad)
                            
                            # Calcular KPIs individuales
                            kpis_medico = calcular_a_cobrar_individual(df_medico, promedio_subespecialidad)
                            
                            if kpis_medico:
                                # Guardar en session state
                                st.session_state['df_medico'] = df_medico
                                st.session_state['kpis_medico'] = kpis_medico
                                st.session_state['promedio_info'] = {
                                    'suma_total': suma_total,
                                    'num_medicos': num_medicos,
                                    'promedio': promedio_subespecialidad
                                }
                                st.session_state['medico_seleccionado'] = medico_seleccionado
                                st.session_state['subespecialidad'] = subespecialidad
                    else:
                        st.warning("No hay médicos disponibles en el rango de fechas seleccionado")
                except Exception as e:
                    st.error(f"Error al procesar médicos: {e}")
    
    # Área principal - Dashboard del médico
    if 'df_medico' in st.session_state and 'kpis_medico' in st.session_state:
        df_medico = st.session_state['df_medico']
        kpis_medico = st.session_state['kpis_medico']
        promedio_info = st.session_state['promedio_info']
        
        if not df_medico.empty and kpis_medico:
            # Crear dashboard del médico
            crear_dashboard_medico(df_medico, kpis_medico, promedio_info)
    else:
        # Pantalla de inicio
        st.markdown("""
        ## 👨‍⚕️ Bienvenido al Dashboard de Análisis Médico Individual
        
        ### 📋 Instrucciones:
        1. **Carga tu archivo Excel** usando el panel lateral
        2. **Selecciona el rango de fechas** que deseas analizar
        3. **Selecciona un médico** de la lista
        4. **Visualiza el análisis completo** con todos los KPIs
        
        ### 📊 **KPIs que se generan por médico (8 KPIs total):**
        
        #### **Fila 1 - Registros e Importes:**
        - **Total Registros**: Número de servicios prestados
        - **Importe Total**: Suma del importe al 100%
        
        #### **Fila 2 - Facturación y Comparación:**
        - **Importe HHMM Total**: Suma del Importe HHMM
        - **Promedio Subespecialidad**: Comparativa con otros médicos
        
        #### **Fila 3 - Porcentajes:**
        - **% a Cobrar (Médico)**: Porcentaje que recibe el médico
        - **% OSA**: Porcentaje que recibe OSA (100% - % Médico)
        
        #### **Fila 4 - Montos a Cobrar:**
        - **Total a Cobrar (Médico)**: Monto que recibe el médico
        - **A Cobrar OSA**: Monto que recibe OSA
        
        ### 📋 **Nuevos KPIs Agregados:**
        
        **1. % OSA:**
        ```
        % OSA = 100% - % a Cobrar (Médico)
        Ejemplo: Si médico recibe 92%, OSA recibe 8%
        ```
        
        **2. A Cobrar OSA:**
        ```
        A Cobrar OSA = Importe HHMM Total - Total a Cobrar (Médico)
        Ejemplo: 1,000 total - 920 médico = 80 OSA
        ```
        
        ### 📋 **Análisis por Tipo de Prestación:**
        - **Unidades por tipo de prestación** (cantidad de servicios)
        - **Monto facturado por tipo de prestación**
        - **Distribución Médico vs OSA** por cada prestación
        - **Gráficos de distribución** interactivos
        
        ### 📥 **Funcionalidades adicionales:**
        - **Descargar reporte completo** en Excel (4 hojas)
        - **Ver todos los registros** del médico
        - **Detalles del cálculo** completo
        
        *Si no cargas un archivo, se usarán datos de ejemplo con 3 médicos diferentes.*
        """)
        
        # Mostrar ejemplo de datos disponibles
        with st.expander("📝 Ejemplo de cálculo con nuevos KPIs", expanded=False):
            st.markdown("""
            **Ejemplo para "FALLONE, JAN" (CONSULTOR por encima del promedio):**
            
            **Datos:**
            - Importe HHMM Total: 2,000.00
            - Promedio subespecialidad: 1,800.00
            - Tipo: CONSULTOR (por encima → 92%)
            
            **Cálculos:**
            1. **% a Cobrar (Médico):** 92%
            2. **% OSA:** 100% - 92% = **8%**
            3. **Total a Cobrar (Médico):** 2,000 × 92% = **1,840**
            4. **A Cobrar OSA:** 2,000 - 1,840 = **160**
            
            **Verificación:**
            - 1,840 + 160 = 2,000 ✓
            - 92% + 8% = 100% ✓
            
            **Distribución final:**
            - **Médico recibe:** 1,840 (92%)
            - **OSA recibe:** 160 (8%)
            """)

if __name__ == "__main__":
    main()
