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
        return 0
    
    # Filtrar por subespecialidad
    df_especialidad = df[df['Subespecialidad'] == subespecialidad]
    
    if df_especialidad.empty:
        return 0
    
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
    
    return {
        'total_registros': total_registros,
        'importe_total': importe_total,
        'importe_hhmm_total': importe_hhmm_total,
        'promedio_subespecialidad': promedio_subespecialidad,
        'porcentaje_cobrar': porcentaje_cobrar * 100,  # En porcentaje
        'total_a_cobrar': total_a_cobrar,
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
    
    # KPIs en 3 filas de 2 columnas
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            "📊 Total Registros",
            f"{kpis['total_registros']:,}",
            help="Número total de servicios prestados"
        )
    
    with col2:
        st.metric(
            "💰 Importe Total",
            f"€{kpis['importe_total']:,.2f}",
            help="Importe total calculado al 100%"
        )
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.metric(
            "💵 Importe HHMM Total",
            f"€{kpis['importe_hhmm_total']:,.2f}",
            help="Suma del Importe HHMM"
        )
    
    with col4:
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
    
    col5, col6 = st.columns(2)
    
    with col5:
        st.metric(
            "📋 % a Cobrar",
            f"{kpis['porcentaje_cobrar']:.1f}%",
            help=f"{kpis['tipo_medico']} {'por encima' if kpis['por_encima_promedio'] else 'por debajo'} del promedio"
        )
    
    with col6:
        st.metric(
            "💳 Total a Cobrar",
            f"€{kpis['total_a_cobrar']:,.2f}",
            help=f"Calculado: €{kpis['importe_hhmm_total']:,.2f} × {kpis['porcentaje_cobrar']:.1f}%"
        )
    
    st.markdown("---")
    
    # Información detallada del promedio
    with st.expander("ℹ️ Detalles del cálculo del promedio", expanded=False):
        st.markdown(f"""
        **Cálculo del promedio para {subespecialidad}:**
        
        ```
        Suma total de facturación en {subespecialidad}: €{promedio_info['suma_total']:,.2f}
        Número de médicos que facturaron: {promedio_info['num_medicos']}
        Promedio = €{promedio_info['suma_total']:,.2f} ÷ {promedio_info['num_medicos']} = €{kpis['promedio_subespecialidad']:,.2f}
        ```
        
        **{nombre_medico} facturó: €{kpis['importe_hhmm_total']:,.2f}**
        
        **Resultado:** {'POR ENCIMA' if kpis['por_encima_promedio'] else 'POR DEBAJO'} del promedio
        **Tipo de médico:** {kpis['tipo_medico']}
        **Porcentaje aplicado:** {kpis['porcentaje_cobrar']:.1f}%
        """)
    
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
            st.markdown("**💰 Monto Facturado por Tipo de Prestación**")
            for _, row in prestacion_analisis.iterrows():
                st.metric(
                    label=row['Descripción de Prestación'],
                    value=f"€{row['Monto Total']:,.2f}",
                    delta=None
                )
        
        # Gráfico de pastel para distribución por prestación
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
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
        
        with col_chart2:
            # Gráfico de monto
            fig_monto = px.pie(
                prestacion_analisis,
                values='Monto Total',
                names='Descripción de Prestación',
                title='Distribución de Monto por Prestación',
                hole=0.4,
                color_discrete_sequence=px.colors.sequential.Plasma
            )
            fig_monto.update_layout(height=400)
            st.plotly_chart(fig_monto, use_container_width=True)
        
        # Tabla detallada
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
                    "Monto Total (€)",
                    format="€%.2f",
                    help="Suma del Importe HHMM"
                ),
                "Monto Promedio": st.column_config.NumberColumn(
                    "Promedio por Unidad (€)",
                    format="€%.2f",
                    help="Monto Total / Unidades"
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
                '% a Cobrar': kpis['porcentaje_cobrar'],
                'Total a Cobrar': kpis['total_a_cobrar']
            }])
            kpis_df.to_excel(writer, index=False, sheet_name='KPIs')
        
        output.seek(0)
        
        st.download_button(
            label=f"⬇️ Descargar Reporte de {nombre_medico}",
            data=output,
            file_name=f"reporte_{nombre_medico.replace(', ', '_').replace(' ', '_')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

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
        
        ### 📊 **KPIs que se generan por médico:**
        
        #### **Métricas Básicas:**
        - **Total Registros**: Número de servicios prestados
        - **Importe Total**: Suma del importe al 100%
        - **Importe HHMM Total**: Suma del Importe HHMM
        
        #### **Análisis Comparativo:**
        - **Promedio de la Subespecialidad**: 
          ```
          (Suma total de facturación de la subespecialidad) / (Número de médicos que facturaron)
          ```
        
        #### **Cálculo de "A Cobrar":**
        - **% a Cobrar**: Determina el porcentaje según:
          - **CONSULTOR por encima del promedio**: 92%
          - **CONSULTOR por debajo del promedio**: 88%
          - **ESPECIALISTA por encima del promedio**: 90%
          - **ESPECIALISTA por debajo del promedio**: 85%
        
        - **Total a Cobrar**: `Importe HHMM Total × % a Cobrar`
        
        ### 📋 **Análisis por Tipo de Prestación:**
        - **Unidades por tipo de prestación** (cantidad de servicios)
        - **Monto facturado por tipo de prestación**
        - **Gráficos de distribución**
        - **Tabla resumen detallada**
        
        ### 📥 **Funcionalidades adicionales:**
        - **Descargar reporte completo** en Excel
        - **Ver todos los registros** del médico
        - **Detalles del cálculo** del promedio
        
        *Si no cargas un archivo, se usarán datos de ejemplo con 3 médicos diferentes.*
        """)
        
        # Mostrar ejemplo de datos disponibles
        with st.expander("📝 Ejemplo de datos disponibles", expanded=False):
            st.markdown("""
            **Ejemplo de cálculo para "HOMBRO Y CODO":**
            
            - **Médico 1 (FALLONE, JAN)**: Facturó €2,000
            - **Médico 2 (ALCANTARA)**: Facturó €1,500
            - **Médico 3 (RIUS)**: Facturó €2,500
            
            **Cálculo del promedio:**
            ```
            Suma total = €2,000 + €1,500 + €2,500 = €6,000
            Número de médicos = 3
            Promedio = €6,000 ÷ 3 = €2,000
            ```
            
            **Cálculo de "A Cobrar" para FALLONE, JAN (€2,000):**
            - Facturó €2,000, igual al promedio (€2,000)
            - Es CONSULTOR → Se considera "por encima" → 92%
            - **A Cobrar** = €2,000 × 92% = **€1,840**
            """)

if __name__ == "__main__":
    main()
