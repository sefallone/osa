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
        return None, None, None, None
    
    # 1. Calcular promedio por subespecialidad (suma total / número de médicos únicos)
    promedios_especialidad = {}
    promedios_detalle = {}  # Para almacenar detalles del cálculo
    
    for especialidad in df['Subespecialidad'].unique():
        # Filtrar por subespecialidad
        df_especialidad = df[df['Subespecialidad'] == especialidad]
        
        if not df_especialidad.empty:
            # Suma total del Importe HHMM para esa subespecialidad
            suma_total = df_especialidad['Importe HHMM'].sum()
            
            # Número de médicos únicos en esa subespecialidad
            num_medicos = df_especialidad['Profesional'].nunique()
            
            # Calcular promedio
            promedio = suma_total / num_medicos if num_medicos > 0 else 0
            
            promedios_especialidad[especialidad] = promedio
            promedios_detalle[especialidad] = {
                'suma_total': suma_total,
                'num_medicos': num_medicos,
                'promedio': promedio
            }
    
    # 2. Calcular "A Cobrar" para cada fila
    def calcular_a_cobrar(row):
        if pd.isnull(row['Importe HHMM']) or pd.isnull(row['Subespecialidad']):
            return 0
        
        especialidad = row['Subespecialidad']
        promedio_especialidad = promedios_especialidad.get(especialidad, 0)
        importe_hhmm = row['Importe HHMM']
        tipo_medico = row['Tipo Médico']
        
        # Determinar si está por encima o por debajo del promedio
        por_encima_promedio = importe_hhmm >= promedio_especialidad
        
        if tipo_medico == 'CONSULTOR':
            if por_encima_promedio:
                return importe_hhmm * 0.92
            else:
                return importe_hhmm * 0.88
        elif tipo_medico == 'ESPECIALISTA':
            if por_encima_promedio:
                return importe_hhmm * 0.90
            else:
                return importe_hhmm * 0.85
        else:
            # Por defecto si no está clasificado
            return importe_hhmm * 0.90
    
    # Aplicar cálculo
    df['A Cobrar'] = df.apply(calcular_a_cobrar, axis=1)
    
    # 3. Calcular "Promedio Facturado por la Unidad" para cada subespecialidad
    # Esto es el mismo cálculo que ya hicimos: suma total / número de médicos
    df['Promedio Facturado por Unidad'] = df.apply(
        lambda row: promedios_especialidad.get(row['Subespecialidad'], 0), 
        axis=1
    )
    
    # 4. Estadísticas generales
    stats = {
        'total_registros': len(df),
        'total_importe_hhmm': df['Importe HHMM'].sum(),
        'total_a_cobrar': df['A Cobrar'].sum(),
        'promedio_importe_hhmm': df['Importe HHMM'].mean(),
        'promedio_a_cobrar': df['A Cobrar'].mean(),
        'num_profesionales': df['Profesional'].nunique(),
        'num_aseguradoras': df['Aseguradora'].nunique() if 'Aseguradora' in df.columns else 0,
        'num_subespecialidades': df['Subespecialidad'].nunique(),
        'fecha_min': df['Fecha del Servicio'].min(),
        'fecha_max': df['Fecha del Servicio'].max()
    }
    
    return df, stats, promedios_especialidad, promedios_detalle

def crear_dashboard(df, stats, promedios_detalle):
    """Crea visualizaciones del dashboard"""
    # Primera fila de KPIs
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Total Registros", f"{stats['total_registros']:,}")
    
    with col2:
        st.metric("💰 Importe HHMM Total", f"€{stats['total_importe_hhmm']:,.2f}")
    
    with col3:
        st.metric("💳 A Cobrar Total", f"€{stats['total_a_cobrar']:,.2f}")
    
    with col4:
        st.metric("👨‍⚕️ Profesionales", stats['num_profesionales'])
    
    # Segunda fila de KPIs específicos
    col5, col6, col7, col8 = st.columns(4)
    
    with col5:
        st.metric("🏥 Subespecialidades", stats['num_subespecialidades'])
    
    with col6:
        st.metric("📈 Prom. Importe HHMM", f"€{stats['promedio_importe_hhmm']:,.2f}")
    
    with col7:
        st.metric("📊 Prom. A Cobrar", f"€{stats['promedio_a_cobrar']:,.2f}")
    
    with col8:
        st.metric("🏢 Aseguradoras", stats['num_aseguradoras'])
    
    st.markdown("---")
    
    # Mostrar promedios por subespecialidad en una tabla
    st.subheader("📊 Promedio Facturado por Unidad (por Subespecialidad)")
    
    if promedios_detalle:
        # Crear DataFrame de promedios
        promedios_df = pd.DataFrame.from_dict(promedios_detalle, orient='index')
        promedios_df = promedios_df.reset_index()
        promedios_df.columns = ['Subespecialidad', 'Detalles']
        
        # Expandir la columna de detalles
        promedios_expanded = pd.json_normalize(promedios_df['Detalles'])
        promedios_df = pd.concat([promedios_df[['Subespecialidad']], promedios_expanded], axis=1)
        
        # Formatear columnas
        promedios_df['suma_total'] = promedios_df['suma_total'].round(2)
        promedios_df['promedio'] = promedios_df['promedio'].round(2)
        
        # Mostrar tabla
        st.dataframe(
            promedios_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Subespecialidad": "Subespecialidad",
                "suma_total": st.column_config.NumberColumn(
                    "Suma Total (€)",
                    help="Suma total del Importe HHMM para la subespecialidad",
                    format="€%.2f"
                ),
                "num_medicos": st.column_config.NumberColumn(
                    "N° Médicos",
                    help="Número de médicos únicos en la subespecialidad"
                ),
                "promedio": st.column_config.NumberColumn(
                    "Promedio por Unidad (€)",
                    help="Suma Total / N° Médicos",
                    format="€%.2f"
                )
            }
        )
    else:
        st.info("No hay datos suficientes para calcular promedios por subespecialidad.")
    
    st.markdown("---")
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de barras por profesional
        if 'Profesional' in df.columns and 'A Cobrar' in df.columns:
            profesional_acobrar = df.groupby('Profesional')['A Cobrar'].sum().sort_values(ascending=False).head(10)
            fig1 = px.bar(
                x=profesional_acobrar.values,
                y=profesional_acobrar.index,
                orientation='h',
                title='Top 10 Profesionales por "A Cobrar"',
                labels={'x': 'A Cobrar (€)', 'y': 'Profesional'},
                color=profesional_acobrar.values,
                color_continuous_scale='Viridis'
            )
            fig1.update_layout(height=400)
            st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        # Gráfico por subespecialidad - Comparación Importe HHMM vs A Cobrar
        if 'Subespecialidad' in df.columns:
            especialidad_comparacion = df.groupby('Subespecialidad').agg({
                'Importe HHMM': 'sum',
                'A Cobrar': 'sum'
            }).reset_index()
            
            # Crear gráfico de barras agrupadas
            fig2 = go.Figure(data=[
                go.Bar(name='Importe HHMM', x=especialidad_comparacion['Subespecialidad'], 
                      y=especialidad_comparacion['Importe HHMM'], marker_color='#1E88E5'),
                go.Bar(name='A Cobrar', x=especialidad_comparacion['Subespecialidad'], 
                      y=especialidad_comparacion['A Cobrar'], marker_color='#FF9800')
            ])
            
            fig2.update_layout(
                title='Comparación: Importe HHMM vs A Cobrar por Subespecialidad',
                barmode='group',
                height=400,
                xaxis_title='Subespecialidad',
                yaxis_title='Importe (€)',
                legend_title='Tipo de Importe'
            )
            st.plotly_chart(fig2, use_container_width=True)
    
    col3, col4 = st.columns(2)
    
    with col3:
        # Gráfico de distribución por tipo de médico
        if 'Tipo Médico' in df.columns and 'A Cobrar' in df.columns:
            tipo_distribucion = df.groupby('Tipo Médico')['A Cobrar'].sum()
            fig3 = px.pie(
                values=tipo_distribucion.values,
                names=tipo_distribucion.index,
                title='Distribución de "A Cobrar" por Tipo de Médico',
                hole=0.4,
                color=tipo_distribucion.index,
                color_discrete_map={'CONSULTOR': '#4CAF50', 'ESPECIALISTA': '#FF5722'}
            )
            fig3.update_layout(height=400)
            st.plotly_chart(fig3, use_container_width=True)
    
    with col4:
        # Evolución temporal del "A Cobrar"
        if 'Fecha del Servicio' in df.columns and 'A Cobrar' in df.columns:
            df['Fecha'] = df['Fecha del Servicio'].dt.date
            temporal = df.groupby('Fecha')['A Cobrar'].sum().reset_index()
            fig4 = px.line(
                temporal,
                x='Fecha',
                y='A Cobrar',
                title='Evolución Diaria de "A Cobrar"',
                markers=True
            )
            fig4.update_layout(
                height=400,
                xaxis_title='Fecha',
                yaxis_title='A Cobrar (€)'
            )
            fig4.update_traces(line=dict(color='#9C27B0', width=3))
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
            # Usar datos de ejemplo del archivo proporcionado
            st.info("📋 Usando datos de ejemplo")
            try:
                # Leer datos del ejemplo proporcionado
                df = pd.read_excel('prueba_sys.xlsx')
            except:
                # Crear DataFrame de ejemplo si no existe el archivo
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
            df_con_kpis, stats, promedios_especialidad, promedios_detalle = calcular_kpis(df_filtrado)
            
            if df_con_kpis is not None:
                # Mostrar dashboard
                crear_dashboard(df_con_kpis, stats, promedios_detalle)
                
                st.markdown("---")
                
                # Mostrar tabla con datos procesados
                with st.expander("📋 Ver Datos Procesados Completos", expanded=False):
                    st.dataframe(
                        df_con_kpis,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Importe HHMM": st.column_config.NumberColumn(format="€%.2f"),
                            "Importe Total": st.column_config.NumberColumn(format="€%.2f"),
                            "A Cobrar": st.column_config.NumberColumn(format="€%.2f"),
                            "Promedio Facturado por Unidad": st.column_config.NumberColumn(format="€%.2f")
                        }
                    )
                
                # Botón para descargar resultados
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_con_kpis.to_excel(writer, index=False, sheet_name='Datos_Procesados')
                    
                    # También guardar los promedios en otra hoja
                    if promedios_detalle:
                        promedios_df = pd.DataFrame.from_dict(promedios_detalle, orient='index')
                        promedios_df = promedios_df.reset_index()
                        promedios_df.columns = ['Subespecialidad', 'Detalles']
                        promedios_expanded = pd.json_normalize(promedios_df['Detalles'])
                        promedios_completo = pd.concat([promedios_df[['Subespecialidad']], promedios_expanded], axis=1)
                        promedios_completo.to_excel(writer, index=False, sheet_name='Promedios_Subespecialidad')
                
                output.seek(0)
                
                st.download_button(
                    label="📥 Descargar Datos Procesados (Excel)",
                    data=output,
                    file_name="datos_procesados_con_promedios.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            else:
                st.warning("No se pudieron calcular los KPIs. Verifique los datos.")
        else:
            st.warning("No hay datos que cumplan con los filtros seleccionados.")
    else:
        # Pantalla de inicio
        st.markdown("""
        ## 🏥 Bienvenido al Dashboard de Análisis de Facturación Médica
        
        ### 📋 Instrucciones:
        1. **Carga tu archivo Excel** usando el panel lateral
        2. **Aplica los filtros** que necesites (fechas, profesional, prestación, aseguradora)
        3. **Haz clic en 'Calcular KPIs'** para generar el análisis completo
        
        ### ⚙️ **Cálculos Automáticos:**
        
        #### 1. **Promedio por Subespecialidad:**
        ```
        Promedio = (Suma Total del Importe HHMM por Subespecialidad) / (Número de Médicos Únicos)
        ```
        
        #### 2. **"A Cobrar" - Cálculo por Tipo de Médico:**
        - **CONSULTOR por encima del promedio**: 92% del Importe HHMM
        - **CONSULTOR por debajo del promedio**: 88% del Importe HHMM
        - **ESPECIALISTA por encima del promedio**: 90% del Importe HHMM
        - **ESPECIALISTA por debajo del promedio**: 85% del Importe HHMM
        
        #### 3. **Promedio Facturado por la Unidad:**
        - Muestra el promedio calculado para cada subespecialidad
        - Este valor se repite para cada registro según su subespecialidad
        
        ### 📊 **KPIs Generados:**
        - **Importe Total** (100% calculado)
        - **Subespecialidad** y **Tipo de Médico**
        - **A Cobrar** (según reglas específicas)
        - **Promedio Facturado por Unidad**
        - **Métricas generales** y gráficos interactivos
        
        ### 📈 **Visualizaciones Incluidas:**
        - Top 10 profesionales por "A Cobrar"
        - Comparación Importe HHMM vs A Cobrar por subespecialidad
        - Distribución por tipo de médico
        - Evolución temporal
        - Tabla detallada de promedios
        
        *Si no cargas un archivo, se usarán datos de ejemplo.*
        """)
        
        # Mostrar ejemplo de cálculo
        with st.expander("📝 Ejemplo de Cálculo", expanded=False):
            st.markdown("""
            **Ejemplo: Subespecialidad "MANO"**
            
            - Médico 1: Importe HHMM = €1,200
            - Médico 2: Importe HHMM = €1,800
            - **Total subespecialidad** = €3,000
            - **Número de médicos** = 2
            - **Promedio por unidad** = €3,000 / 2 = **€1,500**
            
            **Cálculo "A Cobrar" para Médico 1 (€1,200):**
            - Está por debajo del promedio (€1,200 < €1,500)
            - Si es CONSULTOR: €1,200 × 88% = **€1,056**
            - Si es ESPECIALISTA: €1,200 × 85% = **€1,020**
            """)

if __name__ == "__main__":
    main()
