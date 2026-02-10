import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import io

# Configuración de la página
st.set_page_config(
    page_title="Dashboard Médico - Análisis de Facturación",
    page_icon="🏥",
    layout="wide"
)

# Título de la aplicación
st.title("🏥 Dashboard de Análisis de Facturación Médica")
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
    # Crear copia para no modificar el original
    df_procesado = df.copy()
    
    # Convertir columnas de fecha
    if 'Fecha del Servicio' in df_procesado.columns:
        df_procesado['Fecha del Servicio'] = pd.to_datetime(df_procesado['Fecha del Servicio'], errors='coerce')
    
    if 'Fecha de Liquidación' in df_procesado.columns:
        df_procesado['Fecha de Liquidación'] = pd.to_datetime(df_procesado['Fecha de Liquidación'], errors='coerce')
    
    # Asegurar que las columnas numéricas sean del tipo correcto
    if 'Importe HHMM' in df_procesado.columns:
        df_procesado['Importe HHMM'] = pd.to_numeric(df_procesado['Importe HHMM'], errors='coerce')
    
    if '% Liquidación' in df_procesado.columns:
        df_procesado['% Liquidación'] = pd.to_numeric(df_procesado['% Liquidación'], errors='coerce')
    
    # Crear columna de Importe Total (100%)
    df_procesado['Importe Total'] = df_procesado.apply(
        lambda row: (row['Importe HHMM'] / (row['% Liquidación'] / 100)) 
        if pd.notnull(row['Importe HHMM']) and pd.notnull(row['% Liquidación']) and row['% Liquidación'] > 0 
        else row['Importe HHMM'], 
        axis=1
    )
    
    # Añadir información de especialidad y tipo de médico
    df_procesado['Subespecialidad'] = df_procesado['Profesional'].map(
        lambda x: PROFESIONALES_INFO.get(x, {}).get('especialidad', 'NO ESPECIFICADA')
    )
    
    df_procesado['Tipo Médico'] = df_procesado['Profesional'].map(
        lambda x: PROFESIONALES_INFO.get(x, {}).get('tipo', 'NO ESPECIFICADO')
    )
    
    return df_procesado

def calcular_kpis(df):
    """Calcula KPIs y estadísticas"""
    if df.empty:
        return None
    
    # Calcular promedios por subespecialidad
    promedios = df.groupby('Subespecialidad')['Importe HHMM'].mean().to_dict()
    
    # Función para calcular "A Cobrar"
    def calcular_a_cobrar(row):
        if pd.isnull(row['Importe HHMM']) or pd.isnull(row['Subespecialidad']):
            return 0
        
        promedio_especialidad = promedios.get(row['Subespecialidad'], 0)
        importe_hhmm = row['Importe HHMM']
        tipo_medico = row['Tipo Médico']
        
        if importe_hhmm >= promedio_especialidad:
            # Por encima del promedio
            if tipo_medico == 'CONSULTOR':
                return importe_hhmm * 0.92
            elif tipo_medico == 'ESPECIALISTA':
                return importe_hhmm * 0.90
            else:
                return importe_hhmm * 0.90  # Por defecto
        else:
            # Por debajo del promedio
            if tipo_medico == 'CONSULTOR':
                return importe_hhmm * 0.88
            elif tipo_medico == 'ESPECIALISTA':
                return importe_hhmm * 0.85
            else:
                return importe_hhmm * 0.85  # Por defecto
    
    # Aplicar cálculo
    df['A Cobrar'] = df.apply(calcular_a_cobrar, axis=1)
    
    # Estadísticas generales
    stats = {
        'total_registros': len(df),
        'total_importe_hhmm': df['Importe HHMM'].sum(),
        'total_a_cobrar': df['A Cobrar'].sum(),
        'promedio_importe_hhmm': df['Importe HHMM'].mean(),
        'promedio_a_cobrar': df['A Cobrar'].mean(),
        'num_profesionales': df['Profesional'].nunique(),
        'num_aseguradoras': df['Aseguradora'].nunique() if 'Aseguradora' in df.columns else 0,
        'fecha_min': df['Fecha del Servicio'].min(),
        'fecha_max': df['Fecha del Servicio'].max()
    }
    
    return df, stats, promedios

def crear_dashboard(df, stats):
    """Crea visualizaciones del dashboard"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Total Registros", f"{stats['total_registros']:,}")
    
    with col2:
        st.metric("💰 Importe HHMM Total", f"€{stats['total_importe_hhmm']:,.2f}")
    
    with col3:
        st.metric("💳 A Cobrar Total", f"€{stats['total_a_cobrar']:,.2f}")
    
    with col4:
        st.metric("👨‍⚕️ Profesionales", stats['num_profesionales'])
    
    st.markdown("---")
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de barras por profesional
        profesional_importe = df.groupby('Profesional')['Importe HHMM'].sum().sort_values(ascending=False).head(10)
        fig1 = px.bar(
            x=profesional_importe.values,
            y=profesional_importe.index,
            orientation='h',
            title='Top 10 Profesionales por Importe HHMM',
            labels={'x': 'Importe HHMM (€)', 'y': 'Profesional'}
        )
        fig1.update_layout(height=400)
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        # Gráfico por subespecialidad
        especialidad_importe = df.groupby('Subespecialidad')['Importe HHMM'].sum()
        fig2 = px.pie(
            values=especialidad_importe.values,
            names=especialidad_importe.index,
            title='Distribución por Subespecialidad',
            hole=0.3
        )
        fig2.update_layout(height=400)
        st.plotly_chart(fig2, use_container_width=True)
    
    col3, col4 = st.columns(2)
    
    with col3:
        # Gráfico por tipo de médico
        tipo_importe = df.groupby('Tipo Médico')['Importe HHMM'].sum()
        fig3 = px.bar(
            x=tipo_importe.index,
            y=tipo_importe.values,
            title='Importe HHMM por Tipo de Médico',
            labels={'x': 'Tipo de Médico', 'y': 'Importe HHMM (€)'},
            color=tipo_importe.index
        )
        fig3.update_layout(height=400)
        st.plotly_chart(fig3, use_container_width=True)
    
    with col4:
        # Evolución temporal
        if 'Fecha del Servicio' in df.columns:
            df['Fecha'] = df['Fecha del Servicio'].dt.date
            temporal = df.groupby('Fecha')['Importe HHMM'].sum().reset_index()
            fig4 = px.line(
                temporal,
                x='Fecha',
                y='Importe HHMM',
                title='Evolución Diaria del Importe HHMM'
            )
            fig4.update_layout(height=400)
            st.plotly_chart(fig4, use_container_width=True)

def main():
    # Sidebar para carga de archivo y filtros
    with st.sidebar:
        st.header("📁 Carga de Datos")
        
        uploaded_file = st.file_uploader(
            "Sube tu archivo Excel",
            type=['xlsx', 'xls']
        )
        
        if uploaded_file is not None:
            try:
                df = pd.read_excel(uploaded_file)
                st.success(f"✅ Archivo cargado: {uploaded_file.name}")
                st.info(f"📊 {len(df)} registros cargados")
                
                # Mostrar columnas disponibles
                with st.expander("Ver columnas del archivo"):
                    st.write("Columnas disponibles:", list(df.columns))
                
            except Exception as e:
                st.error(f"Error al cargar el archivo: {e}")
                st.stop()
        else:
            # Usar datos de ejemplo
            st.info("📋 Usando datos de ejemplo")
            # Crear DataFrame de ejemplo basado en la estructura proporcionada
            df = pd.DataFrame([
                {
                    "Acreedor": "ORTHOPAEDIC SPECIALIST ALLIANCE SLU",
                    "Profesional": "FALLONE, JAN",
                    "Especialidad": "Traumatología y cir ortopédica",
                    "Clase aseguradora": "NAC",
                    "Aseguradora": "AXA SALUD, AXA SEGUROS GENERALES SOCIEDAD",
                    "Nº de Episodio": 1013682955,
                    "Nombre paciente": "CAMACHO BARBA, VICENTE",
                    "Fecha del Servicio": "2025-12-30",
                    "Hora del Servicio": "18:15:00",
                    "Tipo de Episodio": "Epis.ambulante",
                    "Tipo de Prestación": "HME",
                    "Tipo de Prestación 2": "CEX",
                    "Cantidad": 1,
                    "Código de Prestación": 1,
                    "Descripción de Prestación": "CONSULTA",
                    "Importe HHMM": 19.6,
                    "% Liquidación": 70,
                    "Nº Autofactura": "26VBEF0000049206",
                    "Nº Factura del Episodio": "BE26TI000000312",
                    "Fecha de Liquidación": "2026-01-30"
                }
            ])
        
        st.markdown("---")
        st.header("🔍 Filtros")
        
        if 'df' in locals():
            df_procesado = procesar_datos(df)
            
            # Filtro por fecha
            if 'Fecha del Servicio' in df_procesado.columns:
                min_date = df_procesado['Fecha del Servicio'].min().date()
                max_date = df_procesado['Fecha del Servicio'].max().date()
                
                fecha_range = st.date_input(
                    "Rango de Fechas",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date
                )
                
                if len(fecha_range) == 2:
                    mask = (df_procesado['Fecha del Servicio'].dt.date >= fecha_range[0]) & \
                           (df_procesado['Fecha del Servicio'].dt.date <= fecha_range[1])
                    df_procesado = df_procesado[mask]
            
            # Filtro por profesional
            if 'Profesional' in df_procesado.columns:
                profesionales = ['Todos'] + sorted(df_procesado['Profesional'].unique().tolist())
                profesional_seleccionado = st.selectbox(
                    "Profesional",
                    profesionales
                )
                
                if profesional_seleccionado != 'Todos':
                    df_procesado = df_procesado[df_procesado['Profesional'] == profesional_seleccionado]
            
            # Filtro por descripción de prestación
            if 'Descripción de Prestación' in df_procesado.columns:
                prestaciones = ['Todas'] + sorted(df_procesado['Descripción de Prestación'].unique().tolist())
                prestacion_seleccionada = st.selectbox(
                    "Descripción de Prestación",
                    prestaciones
                )
                
                if prestacion_seleccionada != 'Todas':
                    df_procesado = df_procesado[df_procesado['Descripción de Prestación'] == prestacion_seleccionada]
            
            # Filtro por aseguradora
            if 'Aseguradora' in df_procesado.columns:
                aseguradoras = ['Todas'] + sorted(df_procesado['Aseguradora'].dropna().unique().tolist())
                aseguradora_seleccionada = st.selectbox(
                    "Aseguradora",
                    aseguradoras
                )
                
                if aseguradora_seleccionada != 'Todas':
                    df_procesado = df_procesado[df_procesado['Aseguradora'] == aseguradora_seleccionada]
            
            st.markdown("---")
            
            # Botón para calcular KPIs
            if st.button("📈 Calcular KPIs", type="primary", use_container_width=True):
                st.session_state['df_filtrado'] = df_procesado
    
    # Área principal
    if 'df_filtrado' in st.session_state:
        df_filtrado = st.session_state['df_filtrado']
        
        if not df_filtrado.empty:
            # Calcular KPIs
            df_con_kpis, stats, promedios = calcular_kpis(df_filtrado)
            
            # Mostrar dashboard
            crear_dashboard(df_con_kpis, stats)
            
            st.markdown("---")
            
            # Mostrar tabla con datos procesados
            with st.expander("📋 Ver Datos Procesados", expanded=False):
                st.dataframe(
                    df_con_kpis,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Importe HHMM": st.column_config.NumberColumn(format="€%.2f"),
                        "Importe Total": st.column_config.NumberColumn(format="€%.2f"),
                        "A Cobrar": st.column_config.NumberColumn(format="€%.2f")
                    }
                )
            
            # Mostrar promedios por especialidad
            with st.expander("📊 Promedios por Subespecialidad", expanded=False):
                promedios_df = pd.DataFrame.from_dict(promedios, orient='index', columns=['Promedio Importe HHMM'])
                promedios_df['Promedio Importe HHMM'] = promedios_df['Promedio Importe HHMM'].round(2)
                st.dataframe(promedios_df, use_container_width=True)
            
            # Botón para descargar resultados
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_con_kpis.to_excel(writer, index=False, sheet_name='Datos_Procesados')
            output.seek(0)
            
            st.download_button(
                label="📥 Descargar Datos Procesados (Excel)",
                data=output,
                file_name="datos_procesados.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        else:
            st.warning("No hay datos que cumplan con los filtros seleccionados.")
    else:
        # Pantalla de inicio
        st.markdown("""
        ## Bienvenido al Dashboard de Análisis de Facturación Médica
        
        ### Instrucciones:
        1. **Carga tu archivo Excel** usando el panel lateral
        2. **Aplica los filtros** que necesites
        3. **Haz clic en 'Calcular KPIs'** para generar el análisis
        
        ### Características:
        - 🏥 **Procesamiento automático** de datos médicos
        - 📈 **Cálculo de KPIs** personalizados
        - 💰 **Cálculo de "A Cobrar"** según reglas específicas
        - 🔍 **Filtros interactivos** por fecha, profesional, prestación y aseguradora
        - 📊 **Visualizaciones dinámicas** con gráficos interactivos
        - 📥 **Exportación** de resultados procesados
        
        ### Columnas que se generan automáticamente:
        - **Importe Total**: Calculado a partir de Importe HHMM y % Liquidación
        - **Subespecialidad**: Según la lista de profesionales proporcionada
        - **Tipo Médico**: CONSULTOR o ESPECIALISTA
        - **A Cobrar**: Calculado según las reglas de negocio
        
        *Si no cargas un archivo, se usarán datos de ejemplo.*
        """)
        
        st.image("https://cdn.pixabay.com/photo/2017/10/04/09/56/laboratory-2815641_1280.jpg", 
                caption="Dashboard de Análisis Médico", use_column_width=True)

if __name__ == "__main__":
    main()
