import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date
import plotly.express as px
import plotly.graph_objects as go
import io
import os
import json
from pathlib import Path

# -------------------------------------------------------------------
# CONFIGURACIÓN DE COLORES CORPORATIVOS
# -------------------------------------------------------------------
COLORES = {
    "primary": "#153009",    # Verde oscuro - Color principal
    "secondary": "#cbb26a",  # Dorado - Color secundario
    "background": "#f8f9fa",
    "text_dark": "#1e2e1e",
    "text_light": "#ffffff",
    "success": "#28a745",
    "warning": "#ffc107",
    "danger": "#dc3545",
    "info": "#17a2b8"
}

# Configuración de la página
st.set_page_config(
    page_title="OSA Medical Analytics",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado con los colores corporativos
st.markdown(f"""
<style>
    /* Colores principales */
    :root {{
        --primary-color: {COLORES['primary']};
        --secondary-color: {COLORES['secondary']};
        --background-color: {COLORES['background']};
    }}
    
    /* Títulos con color primario */
    h1, h2, h3 {{
        color: {COLORES['primary']} !important;
    }}
    
    /* Métricas personalizadas */
    .stMetric {{
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 5px solid {COLORES['secondary']};
    }}
    
    .stMetric label {{
        color: {COLORES['primary']} !important;
        font-weight: 600;
    }}
    
    /* Botones */
    .stButton > button {{
        background-color: {COLORES['primary']};
        color: white;
        border: none;
        border-radius: 5px;
        padding: 10px 24px;
        font-weight: 600;
    }}
    
    .stButton > button:hover {{
        background-color: {COLORES['secondary']};
        color: {COLORES['primary']};
    }}
    
    /* Sidebar */
    .css-1d391kg {{
        background-color: {COLORES['primary']};
    }}
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        background-color: white;
        border-radius: 4px 4px 0px 0px;
        padding: 10px 20px;
        color: {COLORES['primary']};
    }}
    
    .stTabs [aria-selected="true"] {{
        background-color: {COLORES['secondary']} !important;
        color: {COLORES['primary']} !important;
    }}
    
    /* Cards personalizadas */
    .custom-card {{
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        border-top: 3px solid {COLORES['secondary']};
    }}
    
    .metric-highlight {{
        font-size: 24px;
        font-weight: bold;
        color: {COLORES['primary']};
    }}
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------------
# PROFESIONALES_INFO - Diccionario de médicos
# -------------------------------------------------------------------
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

# -------------------------------------------------------------------
# CARGA DE USUARIOS DESDE STREAMLIT SECRETS
# -------------------------------------------------------------------
def cargar_usuarios():
    """
    Carga los usuarios y credenciales desde Streamlit Secrets.
    En local usa .streamlit/secrets.toml si existe.
    """
    
    try:
        # Intentar cargar desde st.secrets (Streamlit Cloud)
        admin_pass = st.secrets["usuarios"]["admin_password"]
        medico_default = st.secrets["usuarios"]["medico_password"]
        
        # Credenciales específicas de médicos
        if "credenciales_medicos" in st.secrets:
            credenciales_medicos = dict(st.secrets["credenciales_medicos"])
        else:
            credenciales_medicos = {}
            
        st.success("✅ Configuración de usuarios cargada desde Streamlit Secrets")
        
    except Exception as e:
        # Si no hay secrets, intentar cargar desde archivo local
        try:
            if os.path.exists('.streamlit/secrets.toml'):
                import toml
                secrets_local = toml.load('.streamlit/secrets.toml')
                admin_pass = secrets_local["usuarios"]["admin_password"]
                medico_default = secrets_local["usuarios"]["medico_password"]
                credenciales_medicos = secrets_local.get("credenciales_medicos", {})
                st.info("📁 Usando configuración local desde .streamlit/secrets.toml")
            else:
                # SOLO PARA DESARROLLO - NUNCA EN PRODUCCIÓN
                admin_pass = "admin123"
                medico_default = "medico123"
                credenciales_medicos = {}
                st.warning("⚠️ MODO DESARROLLO: Usando credenciales por defecto. Crea .streamlit/secrets.toml para producción.")
        except:
            # Último recurso - solo para pruebas
            admin_pass = "admin123"
            medico_default = "medico123"
            credenciales_medicos = {}
            st.warning("⚠️ MODO DESARROLLO: Usando credenciales por defecto")
    
    # Construir diccionario de usuarios
    usuarios = {
        "admin": {
            "password": admin_pass,
            "nombre": "Administrador",
            "rol": "admin",
            "email": "admin@osa.com"
        }
    }
    
    # Agregar médicos con sus credenciales específicas o la por defecto
    medicos = {
        "fallone.jan": {
            "password": credenciales_medicos.get("fallone_jan", medico_default),
            "nombre": "Dr. Jan Fallone",
            "rol": "medico",
            "profesional": "FALLONE, JAN",
            "email": "j.fallone@osa.com"
        },
        "ortega.juan": {
            "password": credenciales_medicos.get("ortega_juan", medico_default),
            "nombre": "Dr. Juan Pablo Ortega",
            "rol": "medico",
            "profesional": "ORTEGA RODRIGUEZ, JUAN PABLO",
            "email": "jp.ortega@osa.com"
        },
        "esteban.ignacio": {
            "password": credenciales_medicos.get("esteban_ignacio", medico_default),
            "nombre": "Dr. Ignacio Esteban",
            "rol": "medico",
            "profesional": "ESTEBAN FELIU, IGNACIO",
            "email": "i.esteban@osa.com"
        },
        "pardo.albert": {
            "password": credenciales_medicos.get("pardo_albert", medico_default),
            "nombre": "Dr. Albert Pardo",
            "rol": "medico",
            "profesional": "PARDO I POL, ALBERT",
            "email": "a.pardo@osa.com"
        },
        "alcantara.edgar": {
            "password": credenciales_medicos.get("alcantara_edgar", medico_default),
            "nombre": "Dr. Edgar Alcantara",
            "rol": "medico",
            "profesional": "ALCANTARA MORENO, EDGAR ALFREDO",
            "email": "e.alcantara@osa.com"
        },
        "rius.xavier": {
            "password": credenciales_medicos.get("rius_xavier", medico_default),
            "nombre": "Dr. Xavier Rius",
            "rol": "medico",
            "profesional": "RIUS MORENO, XAVIER",
            "email": "x.rius@osa.com"
        },
        "aguilar.marc": {
            "password": credenciales_medicos.get("aguilar_marc", medico_default),
            "nombre": "Dr. Marc Aguilar",
            "rol": "medico",
            "profesional": "AGUILAR GARCIA, MARC",
            "email": "m.aguilar@osa.com"
        },
        "maio.tomas": {
            "password": credenciales_medicos.get("maio_tomas", medico_default),
            "nombre": "Dr. Tomas Maio",
            "rol": "medico",
            "profesional": "MAIO MÉNDEZ, TOMAS EDUARDO",
            "email": "t.maio@osa.com"
        },
        "monsonet.pablo": {
            "password": credenciales_medicos.get("monsonet_pablo", medico_default),
            "nombre": "Dr. Pablo Monsonet",
            "rol": "medico",
            "profesional": "MONSONET VILLA, PABLO",
            "email": "p.monsonet@osa.com"
        },
        "puigdellivol.jordi": {
            "password": credenciales_medicos.get("puigdellivol_jordi", medico_default),
            "nombre": "Dr. Jordi Puigdellivol",
            "rol": "medico",
            "profesional": "PUIGDELLIVOL GRIFELL, JORDI",
            "email": "j.puigdellivol@osa.com"
        },
        "casaccia.marcelo": {
            "password": credenciales_medicos.get("casaccia_marcelo", medico_default),
            "nombre": "Dr. Marcelo Casaccia",
            "rol": "medico",
            "profesional": "CASACCIA, MARCELO AGUSTIN",
            "email": "m.casaccia@osa.com"
        }
    }
    
    usuarios.update(medicos)
    return usuarios

# -------------------------------------------------------------------
# AUTENTICACIÓN
# -------------------------------------------------------------------
def check_password():
    """Sistema de autenticación con Streamlit Secrets"""
    
    # Cargar usuarios desde secrets
    USUARIOS = cargar_usuarios()
    
    def login_form():
        with st.form("Credentials"):
            st.markdown(f"""
            <div style='text-align: center; padding: 20px;'>
                <h2 style='color: {COLORES['primary']};'>🏥 OSA Medical Analytics</h2>
                <p style='color: {COLORES['primary']};'>Sistema de Análisis Médico</p>
            </div>
            """, unsafe_allow_html=True)
            
            username = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            submitted = st.form_submit_button("Iniciar Sesión", use_container_width=True)
            
            if submitted:
                if username in USUARIOS and password == USUARIOS[username]["password"]:
                    st.session_state["authentication_status"] = True
                    st.session_state["username"] = username
                    st.session_state["user_info"] = USUARIOS[username]
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos")
    
    if "authentication_status" not in st.session_state:
        st.session_state["authentication_status"] = False
    
    if not st.session_state["authentication_status"]:
        login_form()
        return False
    else:
        return True

def logout():
    """Cerrar sesión"""
    if st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True):
        for key in ["authentication_status", "username", "user_info"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

# -------------------------------------------------------------------
# GESTIÓN DE DATOS PERSISTENTES
# -------------------------------------------------------------------
class DataManager:
    """Gestiona el almacenamiento persistente de datos"""
    
    @staticmethod
    def get_data_path():
        """Obtiene la ruta para guardar datos"""
        # En Streamlit Cloud, usamos el directorio persistente
        if os.path.exists('/mount/src'):
            # En producción (Streamlit Cloud)
            data_dir = '/mount/src/medical_dashboard/data'
        else:
            # En local
            data_dir = './data'
        
        Path(data_dir).mkdir(parents=True, exist_ok=True)
        return data_dir
    
    @staticmethod
    def save_dataframe(df, filename='medical_data.parquet'):
        """Guarda el DataFrame de manera persistente"""
        try:
            path = os.path.join(DataManager.get_data_path(), filename)
            df.to_parquet(path, index=False)
            return True
        except Exception as e:
            st.error(f"Error guardando datos: {e}")
            return False
    
    @staticmethod
    def load_dataframe(filename='medical_data.parquet'):
        """Carga el DataFrame guardado"""
        try:
            path = os.path.join(DataManager.get_data_path(), filename)
            if os.path.exists(path):
                return pd.read_parquet(path)
            return None
        except Exception as e:
            st.error(f"Error cargando datos: {e}")
            return None
    
    @staticmethod
    def get_upload_metadata():
        """Obtiene metadatos de la última carga"""
        try:
            path = os.path.join(DataManager.get_data_path(), 'upload_metadata.json')
            if os.path.exists(path):
                with open(path, 'r') as f:
                    return json.load(f)
            return None
        except:
            return None
    
    @staticmethod
    def save_upload_metadata(metadata):
        """Guarda metadatos de la carga"""
        try:
            path = os.path.join(DataManager.get_data_path(), 'upload_metadata.json')
            with open(path, 'w') as f:
                json.dump(metadata, f)
            return True
        except:
            return False

# -------------------------------------------------------------------
# FUNCIONES DE PROCESAMIENTO
# -------------------------------------------------------------------
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
    
    # Añadir mes y año para filtros
    df_procesado['Mes'] = df_procesado['Fecha del Servicio'].dt.month
    df_procesado['Año'] = df_procesado['Fecha del Servicio'].dt.year
    df_procesado['Mes-Año'] = df_procesado['Fecha del Servicio'].dt.strftime('%Y-%m')
    
    return df_procesado

def calcular_promedio_subespecialidad(df, subespecialidad):
    """Calcula el promedio de facturación para una subespecialidad específica"""
    if 'Subespecialidad' not in df.columns or subespecialidad not in df['Subespecialidad'].values:
        return 0, 0, 0
    
    df_especialidad = df[df['Subespecialidad'] == subespecialidad]
    
    if df_especialidad.empty:
        return 0, 0, 0
    
    suma_total = df_especialidad['Importe HHMM'].sum()
    num_medicos = df_especialidad['Profesional'].nunique()
    promedio = suma_total / num_medicos if num_medicos > 0 else 0
    
    return promedio, suma_total, num_medicos

def calcular_a_cobrar_individual(df_medico, promedio_subespecialidad):
    """Calcula los KPIs para un médico individual"""
    if df_medico.empty:
        return None
    
    total_registros = len(df_medico)
    importe_total = df_medico['Importe Total'].sum() if 'Importe Total' in df_medico.columns else 0
    importe_hhmm_total = df_medico['Importe HHMM'].sum() if 'Importe HHMM' in df_medico.columns else 0
    
    tipo_medico = df_medico['Tipo Médico'].iloc[0] if 'Tipo Médico' in df_medico.columns else 'NO ESPECIFICADO'
    
    por_encima_promedio = importe_hhmm_total >= promedio_subespecialidad
    
    if tipo_medico == 'CONSULTOR':
        porcentaje_cobrar = 0.92 if por_encima_promedio else 0.88
    elif tipo_medico == 'ESPECIALISTA':
        porcentaje_cobrar = 0.90 if por_encima_promedio else 0.85
    else:
        porcentaje_cobrar = 0.90
    
    total_a_cobrar = importe_hhmm_total * porcentaje_cobrar
    porcentaje_osa = 100 - (porcentaje_cobrar * 100)
    a_cobrar_osa = importe_hhmm_total - total_a_cobrar
    
    return {
        'total_registros': total_registros,
        'importe_total': importe_total,
        'importe_hhmm_total': importe_hhmm_total,
        'promedio_subespecialidad': promedio_subespecialidad,
        'porcentaje_cobrar': porcentaje_cobrar * 100,
        'total_a_cobrar': total_a_cobrar,
        'porcentaje_osa': porcentaje_osa,
        'a_cobrar_osa': a_cobrar_osa,
        'tipo_medico': tipo_medico,
        'por_encima_promedio': por_encima_promedio
    }

def calcular_dashboard_general(df):
    """Calcula métricas generales para el dashboard del admin"""
    if df is None or df.empty:
        return None
    
    total_medicos = df['Profesional'].nunique()
    total_registros = len(df)
    importe_hhmm_total = df['Importe HHMM'].sum()
    importe_total_vithas = df['Importe Total'].sum()
    
    # Distribución por subespecialidad
    distribucion_subesp = df.groupby('Subespecialidad').agg({
        'Importe HHMM': ['sum', 'count', 'nunique']
    }).reset_index()
    distribucion_subesp.columns = ['Subespecialidad', 'Monto_Total', 'Registros', 'Num_Medicos']
    
    # Top 5 médicos
    top_medicos = df.groupby('Profesional').agg({
        'Importe HHMM': 'sum',
        'Importe Total': 'sum',
        'Fecha del Servicio': 'count'
    }).reset_index()
    top_medicos.columns = ['Profesional', 'Importe_HHMM', 'Importe_Total', 'Registros']
    top_medicos = top_medicos.sort_values('Importe_HHMM', ascending=False).head(5)
    
    # KPIs calculados
    total_pagar_medicos = 0
    total_osa_retiene = 0
    
    for medico in df['Profesional'].unique():
        df_medico = df[df['Profesional'] == medico]
        subesp = df_medico['Subespecialidad'].iloc[0]
        promedio, _, _ = calcular_promedio_subespecialidad(df, subesp)
        kpis = calcular_a_cobrar_individual(df_medico, promedio)
        if kpis:
            total_pagar_medicos += kpis['total_a_cobrar']
            total_osa_retiene += kpis['a_cobrar_osa']
    
    return {
        'total_medicos': total_medicos,
        'total_registros': total_registros,
        'importe_hhmm_total': importe_hhmm_total,
        'importe_total_vithas': importe_total_vithas,
        'total_pagar_medicos': total_pagar_medicos,
        'total_osa_retiene': total_osa_retiene,
        'distribucion_subesp': distribucion_subesp,
        'top_medicos': top_medicos
    }

# -------------------------------------------------------------------
# FUNCIÓN PARA TABLA DETALLADA DE ADMIN (TODOS LOS MÉDICOS)
# -------------------------------------------------------------------
def tabla_detalle_admin(df):
    """Genera la tabla detallada para administradores con todos los médicos"""
    
    st.subheader("📋 Detalle de Servicios - Todos los Médicos")
    
    # Crear DataFrame con las columnas solicitadas en el orden correcto
    columnas_deseadas = {
        'Fecha del Servicio': 'Fecha del servicio',
        'Profesional': 'Profesional',
        'Aseguradora': 'Aseguradora',
        'Descripción de Prestación': 'Descripción de Prestación',
        'Importe Total': 'Monto Cobrado por Vithas (€)',
        '% Liquidación': '% Liquidación',
        'Importe HHMM': 'Importe Cobrado OSA (€)'
    }
    
    # Verificar qué columnas existen en el DataFrame
    columnas_existentes = [col for col in columnas_deseadas.keys() if col in df.columns]
    
    if columnas_existentes:
        # Crear DataFrame con las columnas seleccionadas
        df_detalle = df[columnas_existentes].copy()
        
        # Renombrar columnas
        df_detalle = df_detalle.rename(columns={k: v for k, v in columnas_deseadas.items() if k in df_detalle.columns})
        
        # Asegurar el orden correcto de columnas
        orden_columnas = [
            'Fecha del servicio',
            'Profesional', 
            'Aseguradora',
            'Descripción de Prestación',
            'Monto Cobrado por Vithas (€)',
            '% Liquidación',
            'Importe Cobrado OSA (€)'
        ]
        
        # Solo mantener columnas que existen
        orden_columnas = [col for col in orden_columnas if col in df_detalle.columns]
        df_detalle = df_detalle[orden_columnas]
        
        # Formatear fechas
        if 'Fecha del servicio' in df_detalle.columns:
            df_detalle['Fecha del servicio'] = pd.to_datetime(df_detalle['Fecha del servicio']).dt.strftime('%d/%m/%Y')
        
        # Filtros adicionales para admin
        col_f1, col_f2 = st.columns(2)
        
        with col_f1:
            medicos = ['TODOS'] + sorted(df_detalle['Profesional'].unique().tolist())
            medico_filtro = st.selectbox("👨‍⚕️ Filtrar por Médico", medicos, key="admin_filtro_medico")
        
        with col_f2:
            aseguradoras = ['TODAS'] + sorted(df_detalle['Aseguradora'].unique().tolist())
            aseguradora_filtro = st.selectbox("🏥 Filtrar por Aseguradora", aseguradoras, key="admin_filtro_aseguradora")
        
        # Aplicar filtros
        df_detalle_filtrado = df_detalle.copy()
        
        if medico_filtro != 'TODOS':
            df_detalle_filtrado = df_detalle_filtrado[df_detalle_filtrado['Profesional'] == medico_filtro]
        
        if aseguradora_filtro != 'TODAS':
            df_detalle_filtrado = df_detalle_filtrado[df_detalle_filtrado['Aseguradora'] == aseguradora_filtro]
        
        # Métricas del filtro
        col_m1, col_m2, col_m3 = st.columns(3)
        
        with col_m1:
            st.metric("Registros", f"{len(df_detalle_filtrado):,}")
        
        with col_m2:
            total_vithas = df_detalle_filtrado['Monto Cobrado por Vithas (€)'].sum() if 'Monto Cobrado por Vithas (€)' in df_detalle_filtrado.columns else 0
            st.metric("Total Vithas", f"€{total_vithas:,.2f}")
        
        with col_m3:
            total_osa = df_detalle_filtrado['Importe Cobrado OSA (€)'].sum() if 'Importe Cobrado OSA (€)' in df_detalle_filtrado.columns else 0
            st.metric("Total OSA", f"€{total_osa:,.2f}")
        
        # Mostrar la tabla
        st.dataframe(
            df_detalle_filtrado,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Fecha del servicio": "Fecha",
                "Profesional": "Médico",
                "Aseguradora": "Aseguradora",
                "Descripción de Prestación": "Prestación",
                "Monto Cobrado por Vithas (€)": st.column_config.NumberColumn(
                    "Monto Vithas (€)",
                    format="€%.2f",
                    help="Importe total al 100%"
                ),
                "% Liquidación": st.column_config.NumberColumn(
                    "% Liquidación",
                    format="%.0f%%",
                    help="Porcentaje que liquida Vithas"
                ),
                "Importe Cobrado OSA (€)": st.column_config.NumberColumn(
                    "Importe OSA (€)",
                    format="€%.2f",
                    help="Importe que cobra OSA (descontado % Vithas)"
                )
            }
        )
        
        # Botón de descarga para admin
        if st.button("📥 Descargar Detalle Completo (Excel)", use_container_width=True, type="primary"):
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Hoja 1: Detalle completo
                df_detalle_filtrado.to_excel(writer, index=False, sheet_name='Detalle_Servicios')
                
                # Hoja 2: Resumen por médico
                resumen_medico = df_detalle_filtrado.groupby('Profesional').agg({
                    'Monto Cobrado por Vithas (€)': 'sum',
                    'Importe Cobrado OSA (€)': 'sum',
                    'Fecha del servicio': 'count'
                }).reset_index()
                resumen_medico.columns = ['Médico', 'Total Vithas', 'Total OSA', 'Registros']
                resumen_medico.to_excel(writer, index=False, sheet_name='Resumen_Medicos')
                
                # Hoja 3: Resumen por aseguradora
                resumen_aseguradora = df_detalle_filtrado.groupby('Aseguradora').agg({
                    'Monto Cobrado por Vithas (€)': 'sum',
                    'Importe Cobrado OSA (€)': 'sum',
                    'Fecha del servicio': 'count'
                }).reset_index()
                resumen_aseguradora.columns = ['Aseguradora', 'Total Vithas', 'Total OSA', 'Registros']
                resumen_aseguradora.to_excel(writer, index=False, sheet_name='Resumen_Aseguradoras')
            
            output.seek(0)
            
            st.download_button(
                label=f"⬇️ Confirmar Descarga",
                data=output,
                file_name=f"detalle_completo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.warning("No se encontraron las columnas necesarias para mostrar el detalle de servicios.")

# -------------------------------------------------------------------
# DASHBOARD ADMINISTRADOR
# -------------------------------------------------------------------
def dashboard_admin(df):
    """Dashboard completo para administradores"""
    
    st.markdown(f"""
    <div class='custom-card'>
        <h2 style='color: {COLORES['primary']}; margin-bottom: 0;'>📊 Dashboard Ejecutivo OSA</h2>
        <p style='color: {COLORES['secondary']};'>Análisis global de rendimiento médico</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Filtros globales
    col_f1, col_f2, col_f3 = st.columns([2,2,2])
    
    with col_f1:
        if 'Fecha del Servicio' in df.columns:
            min_date = df['Fecha del Servicio'].min().date()
            max_date = df['Fecha del Servicio'].max().date()
            fecha_range = st.date_input(
                "📅 Rango de Fechas",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
                key="admin_fecha_range"
            )
    
    with col_f2:
        subespecialidades = ['TODAS'] + sorted(df['Subespecialidad'].unique().tolist())
        subesp_selected = st.selectbox("🏥 Subespecialidad", subespecialidades, key="admin_subesp")
    
    with col_f3:
        tipos_medico = ['TODOS'] + sorted(df['Tipo Médico'].unique().tolist())
        tipo_selected = st.selectbox("👨‍⚕️ Tipo de Médico", tipos_medico, key="admin_tipo")
    
    # Aplicar filtros
    df_filtered = df.copy()
    
    if 'fecha_range' in locals() and len(fecha_range) == 2:
        df_filtered = df_filtered[
            (df_filtered['Fecha del Servicio'].dt.date >= fecha_range[0]) &
            (df_filtered['Fecha del Servicio'].dt.date <= fecha_range[1])
        ]
    
    if subesp_selected != 'TODAS':
        df_filtered = df_filtered[df_filtered['Subespecialidad'] == subesp_selected]
    
    if tipo_selected != 'TODOS':
        df_filtered = df_filtered[df_filtered['Tipo Médico'] == tipo_selected]
    
    # Calcular métricas generales
    metricas = calcular_dashboard_general(df_filtered)
    
    if metricas:
        # KPIs principales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class='stMetric'>
                <label>👥 Médicos Activos</label>
                <div class='metric-highlight'>{metricas['total_medicos']:,}</div>
                <small>Periodo seleccionado</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class='stMetric'>
                <label>💰 Facturado Vithas</label>
                <div class='metric-highlight'>€{metricas['importe_total_vithas']:,.2f}</div>
                <small>Importe al 100%</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class='stMetric'>
                <label>💵 Cobrado OSA</label>
                <div class='metric-highlight'>€{metricas['importe_hhmm_total']:,.2f}</div>
                <small>Importe HHMM</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class='stMetric'>
                <label>📋 Total Servicios</label>
                <div class='metric-highlight'>{metricas['total_registros']:,}</div>
                <small>Registros procesados</small>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Segunda fila KPIs
        col5, col6, col7, col8 = st.columns(4)
        
        with col5:
            st.markdown(f"""
            <div class='stMetric'>
                <label>💳 Pago a Médicos</label>
                <div class='metric-highlight'>€{metricas['total_pagar_medicos']:,.2f}</div>
                <small>Total a liquidar</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col6:
            st.markdown(f"""
            <div class='stMetric'>
                <label>🏥 OSA Retiene</label>
                <div class='metric-highlight'>€{metricas['total_osa_retiene']:,.2f}</div>
                <small>Margen OSA</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col7:
            margen = (metricas['total_osa_retiene'] / metricas['importe_hhmm_total'] * 100) if metricas['importe_hhmm_total'] > 0 else 0
            st.markdown(f"""
            <div class='stMetric'>
                <label>📊 Margen OSA</label>
                <div class='metric-highlight'>{margen:.1f}%</div>
                <small>Sobre HHMM</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col8:
            promedio_medico = metricas['importe_hhmm_total'] / metricas['total_medicos'] if metricas['total_medicos'] > 0 else 0
            st.markdown(f"""
            <div class='stMetric'>
                <label>📈 Promedio/Médico</label>
                <div class='metric-highlight'>€{promedio_medico:,.2f}</div>
                <small>Facturación media</small>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Gráficos y análisis
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            # Distribución por subespecialidad
            fig_subesp = px.bar(
                metricas['distribucion_subesp'],
                x='Subespecialidad',
                y='Monto_Total',
                title='💰 Facturación por Subespecialidad',
                color='Subespecialidad',
                color_discrete_sequence=[COLORES['secondary'], COLORES['primary']],
                text_auto='.2s'
            )
            fig_subesp.update_layout(
                height=400,
                title_x=0.5,
                showlegend=False,
                plot_bgcolor='white'
            )
            fig_subesp.update_traces(
                texttemplate='€%{text:,.0f}',
                textposition='outside',
                marker_line_color=COLORES['primary'],
                marker_line_width=1.5,
                opacity=0.8
            )
            st.plotly_chart(fig_subesp, use_container_width=True)
        
        with col_g2:
            # Top 5 médicos
            fig_top = px.bar(
                metricas['top_medicos'],
                x='Importe_HHMM',
                y='Profesional',
                orientation='h',
                title='🏆 Top 5 Médicos por Facturación',
                color='Importe_HHMM',
                color_continuous_scale=[COLORES['secondary'], COLORES['primary']],
                text_auto='.2s'
            )
            fig_top.update_layout(
                height=400,
                title_x=0.5,
                plot_bgcolor='white'
            )
            fig_top.update_traces(
                texttemplate='€%{text:,.0f}',
                textposition='outside'
            )
            st.plotly_chart(fig_top, use_container_width=True)
        
        st.markdown("---")
        
        # Tabla de médicos con KPIs individuales
        st.subheader("📋 Análisis Individual por Médico")
        
        medicos_data = []
        for medico in df_filtered['Profesional'].unique():
            df_med = df_filtered[df_filtered['Profesional'] == medico]
            subesp = df_med['Subespecialidad'].iloc[0]
            tipo = df_med['Tipo Médico'].iloc[0]
            promedio, _, _ = calcular_promedio_subespecialidad(df_filtered, subesp)
            kpis = calcular_a_cobrar_individual(df_med, promedio)
            
            if kpis:
                medicos_data.append({
                    'Profesional': medico,
                    'Subespecialidad': subesp,
                    'Tipo': tipo,
                    'Registros': kpis['total_registros'],
                    'Facturado HHMM': kpis['importe_hhmm_total'],
                    'Promedio Subesp': kpis['promedio_subespecialidad'],
                    '% Cobrar': f"{kpis['porcentaje_cobrar']:.1f}%",
                    'A Cobrar': kpis['total_a_cobrar'],
                    'OSA Retiene': kpis['a_cobrar_osa'],
                    '% OSA': f"{kpis['porcentaje_osa']:.1f}%"
                })
        
        df_medicos = pd.DataFrame(medicos_data)
        
        st.dataframe(
            df_medicos,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Profesional": "Médico",
                "Subespecialidad": "Subespecialidad",
                "Tipo": "Tipo",
                "Registros": st.column_config.NumberColumn("Registros", format="%d"),
                "Facturado HHMM": st.column_config.NumberColumn("Facturado HHMM (€)", format="€%.2f"),
                "Promedio Subesp": st.column_config.NumberColumn("Promedio Subesp (€)", format="€%.2f"),
                "% Cobrar": "% Médico",
                "A Cobrar": st.column_config.NumberColumn("A Cobrar (€)", format="€%.2f"),
                "OSA Retiene": st.column_config.NumberColumn("OSA Retiene (€)", format="€%.2f"),
                "% OSA": "% OSA"
            }
        )
        
        st.markdown("---")
        
        # Tabla detallada para admin (todos los médicos)
        tabla_detalle_admin(df_filtered)

# -------------------------------------------------------------------
# DASHBOARD MÉDICO - COMPLETAMENTE ACTUALIZADO
# -------------------------------------------------------------------
def dashboard_medico(df, profesional_nombre):
    """Dashboard específico para médicos"""
    
    # Filtrar datos del médico
    df_medico = df[df['Profesional'] == profesional_nombre].copy()
    
    if df_medico.empty:
        st.warning("No hay datos disponibles para este médico en el período actual.")
        return
    
    # Obtener subespecialidad y calcular promedios
    subespecialidad = df_medico['Subespecialidad'].iloc[0]
    promedio_subespecialidad, suma_total, num_medicos = calcular_promedio_subespecialidad(df, subespecialidad)
    
    # Calcular KPIs
    kpis = calcular_a_cobrar_individual(df_medico, promedio_subespecialidad)
    
    if not kpis:
        st.error("Error calculando KPIs")
        return
    
    # Información de metadatos de carga
    metadata = DataManager.get_upload_metadata()
    
    # Header personalizado
    st.markdown(f"""
    <div class='custom-card' style='background: linear-gradient(135deg, {COLORES['primary']} 0%, {COLORES['primary']}ee 100%);'>
        <h2 style='color: white !important; margin-bottom: 5px;'>👨‍⚕️ {profesional_nombre}</h2>
        <p style='color: {COLORES['secondary']} !important; font-size: 18px; margin-bottom: 0;'>
            {subespecialidad} • {kpis['tipo_medico']}
        </p>
        <p style='color: rgba(255,255,255,0.8); font-size: 14px; margin-top: 10px;'>
            📅 Última actualización: {metadata.get('fecha', 'No disponible') if metadata else 'No disponible'}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # KPIs principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class='stMetric'>
            <label style='color: {COLORES['primary']};'>💰 Facturado x Vithas</label>
            <div style='font-size: 28px; font-weight: bold; color: {COLORES['primary']};'>
                €{kpis['importe_total']:,.2f}
            </div>
            <small>Importe total al 100%</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class='stMetric'>
            <label style='color: {COLORES['primary']};'>💵 Cobrado x OSA</label>
            <div style='font-size: 28px; font-weight: bold; color: {COLORES['primary']};'>
                €{kpis['importe_hhmm_total']:,.2f}
            </div>
            <small>Descontado % Vithas</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        delta_color = "normal" if kpis['por_encima_promedio'] else "inverse"
        delta_text = "↑ Por encima" if kpis['por_encima_promedio'] else "↓ Por debajo"
        
        st.markdown(f"""
        <div class='stMetric'>
            <label style='color: {COLORES['primary']};'>📈 Promedio {subespecialidad}</label>
            <div style='font-size: 28px; font-weight: bold; color: {COLORES['primary']};'>
                €{kpis['promedio_subespecialidad']:,.2f}
            </div>
            <small style='color: {"#28a745" if kpis["por_encima_promedio"] else "#dc3545"};'>{delta_text}</small>
            <br>
            <small>vs tu facturación: €{kpis['importe_hhmm_total']:,.2f}</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class='stMetric'>
            <label style='color: {COLORES['primary']};'>📊 Total Servicios</label>
            <div style='font-size: 28px; font-weight: bold; color: {COLORES['primary']};'>
                {kpis['total_registros']:,}
            </div>
            <small>Registros en el período</small>
        </div>
        """, unsafe_allow_html=True)
    
    # Segunda fila
    col5, col6, col7, col8 = st.columns(4)
    
    with col5:
        st.markdown(f"""
        <div class='stMetric'>
            <label style='color: {COLORES['primary']};'>📋 % a Cobrar (Médico)</label>
            <div style='font-size: 28px; font-weight: bold; color: {COLORES['primary']};'>
                {kpis['porcentaje_cobrar']:.1f}%
            </div>
            <small>{kpis['tipo_medico']} {'por encima' if kpis['por_encima_promedio'] else 'por debajo'}</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col6:
        st.markdown(f"""
        <div class='stMetric'>
            <label style='color: {COLORES['primary']};'>🏥 % OSA</label>
            <div style='font-size: 28px; font-weight: bold; color: {COLORES['primary']};'>
                {kpis['porcentaje_osa']:.1f}%
            </div>
            <small>100% - {kpis['porcentaje_cobrar']:.1f}%</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col7:
        st.markdown(f"""
        <div class='stMetric'>
            <label style='color: {COLORES['primary']};'>💳 Total a Cobrar</label>
            <div style='font-size: 28px; font-weight: bold; color: {COLORES['primary']};'>
                €{kpis['total_a_cobrar']:,.2f}
            </div>
            <small>Tu liquidación</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col8:
        st.markdown(f"""
        <div class='stMetric'>
            <label style='color: {COLORES['primary']};'>💰 OSA Retiene</label>
            <div style='font-size: 28px; font-weight: bold; color: {COLORES['primary']};'>
                €{kpis['a_cobrar_osa']:,.2f}
            </div>
            <small>Margen OSA</small>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Gráficos de distribución
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        # Gráfico de distribución Médico vs OSA
        distribucion_data = pd.DataFrame({
            'Concepto': ['Médico', 'OSA'],
            'Monto': [kpis['total_a_cobrar'], kpis['a_cobrar_osa']],
            'Porcentaje': [kpis['porcentaje_cobrar'], kpis['porcentaje_osa']]
        })
        
        fig_dist = px.pie(
            distribucion_data,
            values='Monto',
            names='Concepto',
            title='Distribución de Ingresos',
            color='Concepto',
            color_discrete_map={'Médico': COLORES['primary'], 'OSA': COLORES['secondary']},
            hole=0.4
        )
        fig_dist.update_layout(
            height=400,
            title_x=0.5,
            font=dict(size=14)
        )
        fig_dist.update_traces(
            textinfo='percent+label',
            textfont_size=14,
            marker=dict(line=dict(color='#000000', width=2))
        )
        st.plotly_chart(fig_dist, use_container_width=True)
    
    with col_g2:
        # Gráfico de evolución temporal
        df_medico_mensual = df_medico.groupby('Mes-Año').agg({
            'Importe HHMM': 'sum',
            'Importe Total': 'sum'
        }).reset_index()
        
        if len(df_medico_mensual) > 0:
            fig_evol = px.line(
                df_medico_mensual,
                x='Mes-Año',
                y='Importe HHMM',
                title='Evolución Mensual de Facturación',
                markers=True,
                color_discrete_sequence=[COLORES['primary']]
            )
            fig_evol.update_layout(
                height=400,
                title_x=0.5,
                plot_bgcolor='white',
                xaxis_title='Mes',
                yaxis_title='Importe HHMM (€)'
            )
            fig_evol.update_traces(
                line=dict(width=3),
                marker=dict(size=8, color=COLORES['secondary'])
            )
            st.plotly_chart(fig_evol, use_container_width=True)
    
    st.markdown("---")
    
    # -------------------------------------------------------------------
    # ANÁLISIS POR TIPO DE PRESTACIÓN - ACTUALIZADO
    # -------------------------------------------------------------------
    st.subheader("📋 Análisis por Tipo de Prestación")
    
    if 'Descripción de Prestación' in df_medico.columns:
        prestacion_analisis = df_medico.groupby('Descripción de Prestación').agg({
            'Importe HHMM': ['count', 'sum']
        }).reset_index()
        prestacion_analisis.columns = ['Descripción de Prestación', 'Cantidad', 'Monto Total']
        
        # Calcular porcentaje y distribución
        prestacion_analisis['% del Total'] = (prestacion_analisis['Monto Total'] / kpis['importe_hhmm_total']) * 100
        prestacion_analisis['Médico Recibe'] = prestacion_analisis['Monto Total'] * (kpis['porcentaje_cobrar'] / 100)
        prestacion_analisis['OSA Recibe'] = prestacion_analisis['Monto Total'] * (kpis['porcentaje_osa'] / 100)
        prestacion_analisis['Monto Promedio'] = prestacion_analisis['Monto Total'] / prestacion_analisis['Cantidad']
        
        # RENOMBRAR COLUMNAS SEGÚN LO SOLICITADO
        prestacion_analisis = prestacion_analisis.rename(columns={
            'Monto Total': 'Monto Cobrado por OSA (€)',
            'Monto Promedio': 'Monto Promedio (€)'
        })
        
        st.dataframe(
            prestacion_analisis,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Descripción de Prestación": "Tipo de Prestación",
                "Cantidad": st.column_config.NumberColumn("Unidades", format="%d"),
                "Monto Cobrado por OSA (€)": st.column_config.NumberColumn("Monto Cobrado por OSA (€)", format="€%.2f"),
                "Monto Promedio (€)": st.column_config.NumberColumn("Monto Promedio (€)", format="€%.2f"),
                "% del Total": st.column_config.NumberColumn("% del Total", format="%.1f%%"),
                "Médico Recibe": st.column_config.NumberColumn("Médico Recibe (€)", format="€%.2f"),
                "OSA Recibe": st.column_config.NumberColumn("OSA Retiene (€)", format="€%.2f")
            }
        )
    
    st.markdown("---")
    
    # -------------------------------------------------------------------
    # TABLA ORIGINAL FILTRADA - NUEVA SECCIÓN
    # -------------------------------------------------------------------
    st.subheader("📋 Detalle de Servicios")
    
    # Crear DataFrame con las columnas solicitadas en el orden correcto
    columnas_deseadas = {
        'Fecha del Servicio': 'Fecha del servicio',
        'Profesional': 'Profesional',
        'Aseguradora': 'Aseguradora',
        'Descripción de Prestación': 'Descripción de Prestación',
        'Importe Total': 'Monto Cobrado por Vithas (€)',
        '% Liquidación': '% Liquidación',
        'Importe HHMM': 'Importe Cobrado OSA (€)'
    }
    
    # Verificar qué columnas existen en el DataFrame
    columnas_existentes = [col for col in columnas_deseadas.keys() if col in df_medico.columns]
    
    if columnas_existentes:
        # Crear DataFrame con las columnas seleccionadas
        df_detalle = df_medico[columnas_existentes].copy()
        
        # Renombrar columnas
        df_detalle = df_detalle.rename(columns={k: v for k, v in columnas_deseadas.items() if k in df_detalle.columns})
        
        # Asegurar el orden correcto de columnas
        orden_columnas = [
            'Fecha del servicio',
            'Profesional', 
            'Aseguradora',
            'Descripción de Prestación',
            'Monto Cobrado por Vithas (€)',
            '% Liquidación',
            'Importe Cobrado OSA (€)'
        ]
        
        # Solo mantener columnas que existen
        orden_columnas = [col for col in orden_columnas if col in df_detalle.columns]
        df_detalle = df_detalle[orden_columnas]
        
        # Formatear fechas
        if 'Fecha del servicio' in df_detalle.columns:
            df_detalle['Fecha del servicio'] = pd.to_datetime(df_detalle['Fecha del servicio']).dt.strftime('%d/%m/%Y')
        
        # Mostrar la tabla
        st.dataframe(
            df_detalle,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Fecha del servicio": "Fecha",
                "Profesional": "Médico",
                "Aseguradora": "Aseguradora",
                "Descripción de Prestación": "Prestación",
                "Monto Cobrado por Vithas (€)": st.column_config.NumberColumn(
                    "Monto Vithas (€)",
                    format="€%.2f",
                    help="Importe total al 100%"
                ),
                "% Liquidación": st.column_config.NumberColumn(
                    "% Liquidación",
                    format="%.0f%%",
                    help="Porcentaje que liquida Vithas"
                ),
                "Importe Cobrado OSA (€)": st.column_config.NumberColumn(
                    "Importe OSA (€)",
                    format="€%.2f",
                    help="Importe que cobra OSA (descontado % Vithas)"
                )
            }
        )
        
        # Botón de descarga para la tabla detallada
        if st.button("📥 Descargar Detalle de Servicios (Excel)", use_container_width=True):
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_detalle.to_excel(writer, index=False, sheet_name='Detalle_Servicios')
                
                # Agregar hoja de resumen de KPIs
                kpis_resumen = pd.DataFrame([{
                    'Médico': profesional_nombre,
                    'Subespecialidad': subespecialidad,
                    'Tipo': kpis['tipo_medico'],
                    'Total Facturado Vithas': kpis['importe_total'],
                    'Total Cobrado OSA': kpis['importe_hhmm_total'],
                    '% Cobrar': kpis['porcentaje_cobrar'],
                    '% OSA': kpis['porcentaje_osa'],
                    'A Cobrar Médico': kpis['total_a_cobrar'],
                    'OSA Retiene': kpis['a_cobrar_osa']
                }])
                kpis_resumen.to_excel(writer, index=False, sheet_name='Resumen_KPIs')
            
            output.seek(0)
            
            st.download_button(
                label=f"⬇️ Confirmar Descarga",
                data=output,
                file_name=f"detalle_{profesional_nombre.replace(', ', '_').replace(' ', '_')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.warning("No se encontraron las columnas necesarias para mostrar el detalle de servicios.")

# -------------------------------------------------------------------
# PANEL DE ADMINISTRADOR
# -------------------------------------------------------------------
def panel_admin(df_actual):
    """Panel exclusivo para administradores"""
    
    st.markdown(f"""
    <div class='custom-card'>
        <h2 style='color: {COLORES['primary']};'>🔧 Panel de Administración</h2>
        <p style='color: {COLORES['secondary']};'>Gestión de datos y configuración</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📤 Carga de Datos", "📊 Dashboard General", "ℹ️ Información"])
    
    with tab1:
        st.subheader("Cargar Nuevo Archivo de Datos")
        st.markdown(f"<p style='color: {COLORES['primary']};'>Formato permitido: Excel (.xlsx, .xls)</p>", unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "Selecciona el archivo Excel con los datos médicos",
            type=['xlsx', 'xls'],
            key="admin_upload"
        )
        
        if uploaded_file is not None:
            try:
                df_nuevo = pd.read_excel(uploaded_file)
                df_procesado = procesar_datos(df_nuevo)
                
                # Mostrar preview
                st.success(f"✅ Archivo cargado exitosamente: {uploaded_file.name}")
                st.info(f"📊 Registros: {len(df_procesado):,} | 👥 Médicos: {df_procesado['Profesional'].nunique():,}")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Vista previa de los datos:**")
                    st.dataframe(df_procesado.head(10), use_container_width=True)
                
                with col2:
                    st.markdown("**Resumen de médicos detectados:**")
                    medicos_resumen = df_procesado.groupby('Profesional').agg({
                        'Importe HHMM': 'sum',
                        'Fecha del Servicio': 'count'
                    }).reset_index()
                    medicos_resumen.columns = ['Médico', 'Total Facturado', 'Registros']
                    medicos_resumen = medicos_resumen.sort_values('Total Facturado', ascending=False)
                    st.dataframe(medicos_resumen, use_container_width=True, hide_index=True)
                
                # Confirmar guardado
                if st.button("💾 Guardar Datos Permanentemente", use_container_width=True, type="primary"):
                    if DataManager.save_dataframe(df_procesado):
                        metadata = {
                            'fecha': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'archivo': uploaded_file.name,
                            'registros': len(df_procesado),
                            'medicos': df_procesado['Profesional'].nunique(),
                            'usuario': st.session_state['username']
                        }
                        DataManager.save_upload_metadata(metadata)
                        
                        st.session_state['df_global'] = df_procesado
                        st.success("✅ Datos guardados correctamente. Ya están disponibles para todos los médicos.")
                        st.rerun()
            
            except Exception as e:
                st.error(f"❌ Error al procesar el archivo: {e}")
        
        # Mostrar estado actual
        if df_actual is not None:
            st.markdown("---")
            st.markdown("**📋 Estado actual de los datos:**")
            col_s1, col_s2, col_s3 = st.columns(3)
            
            with col_s1:
                st.metric("Registros almacenados", f"{len(df_actual):,}")
            
            with col_s2:
                st.metric("Médicos", f"{df_actual['Profesional'].nunique():,}")
            
            with col_s3:
                metadata = DataManager.get_upload_metadata()
                if metadata:
                    st.metric("Última actualización", metadata.get('fecha', 'No disponible'))
    
    with tab2:
        if df_actual is not None and not df_actual.empty:
            dashboard_admin(df_actual)
        else:
            st.warning("⚠️ No hay datos cargados. Por favor, carga un archivo en la pestaña 'Carga de Datos'.")
    
    with tab3:
        st.subheader("Información del Sistema")
        st.markdown(f"""
        **Versión:** 2.0.0  
        **Última actualización:** Febrero 2026  
        **Colores corporativos:** {COLORES['primary']} / {COLORES['secondary']}
        
        **Médicos configurados en el sistema:**
        """)
        
        # Mostrar lista de médicos disponibles
        medicos_sistema = []
        for profesional in PROFESIONALES_INFO.keys():
            info = PROFESIONALES_INFO[profesional]
            medicos_sistema.append({
                'Profesional': profesional,
                'Especialidad': info['especialidad'],
                'Tipo': info['tipo']
            })
        
        df_medicos_sistema = pd.DataFrame(medicos_sistema)
        st.dataframe(df_medicos_sistema, use_container_width=True, hide_index=True)

# -------------------------------------------------------------------
# FUNCIÓN PRINCIPAL
# -------------------------------------------------------------------
def main():
    """Función principal de la aplicación"""
    
    # Verificar autenticación
    if not check_password():
        return
    
    # Obtener información del usuario
    user_info = st.session_state['user_info']
    username = st.session_state['username']
    rol = user_info['rol']
    
    # Sidebar con información del usuario
    with st.sidebar:
        st.markdown(f"""
        <div style='text-align: center; padding: 20px;'>
            <h3 style='color: {COLORES['secondary']};'>🏥 OSA</h3>
            <p style='color: white;'>Bienvenido,</p>
            <p style='color: {COLORES['secondary']}; font-weight: bold;'>{user_info['nombre']}</p>
            <p style='color: rgba(255,255,255,0.7);'>{'👑 Administrador' if rol == 'admin' else '👨‍⚕️ Médico'}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Cargar datos persistentes
        df_global = DataManager.load_dataframe()
        
        if df_global is not None:
            st.success(f"✅ Datos cargados: {len(df_global):,} registros")
            
            metadata = DataManager.get_upload_metadata()
            if metadata:
                st.info(f"📅 Última actualización: {metadata.get('fecha', 'No disponible')}")
        else:
            if rol == 'admin':
                st.warning("⚠️ No hay datos cargados. Ve al panel de administración para cargar datos.")
            else:
                st.warning("⏳ Esperando que el administrador cargue los datos...")
        
        st.markdown("---")
        logout()
    
    # Área principal según el rol
    if rol == 'admin':
        st.markdown(f"""
        <h1 style='color: {COLORES['primary']};'>🏥 OSA Medical Analytics</h1>
        <p style='color: {COLORES['secondary']}; font-size: 18px;'>Panel de Administración</p>
        """, unsafe_allow_html=True)
        
        panel_admin(df_global)
    
    elif rol == 'medico':
        profesional = user_info['profesional']
        
        if df_global is None or df_global.empty:
            st.markdown(f"""
            <div style='text-align: center; padding: 50px;'>
                <h2 style='color: {COLORES['primary']};'>👨‍⚕️ {user_info['nombre']}</h2>
                <p style='color: {COLORES['secondary']}; font-size: 18px;'>Esperando datos del administrador...</p>
                <p>El administrador cargará los datos próximamente. Por favor, intenta más tarde.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            dashboard_medico(df_global, profesional)

if __name__ == "__main__":
    main()
