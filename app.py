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
    
    /* Badges para resultados del match */
    .badge-success {{
        background-color: #28a745;
        color: white;
        padding: 5px 10px;
        border-radius: 20px;
        font-size: 14px;
        font-weight: bold;
    }}
    
    .badge-warning {{
        background-color: #ffc107;
        color: black;
        padding: 5px 10px;
        border-radius: 20px;
        font-size: 14px;
        font-weight: bold;
    }}
    
    .badge-danger {{
        background-color: #dc3545;
        color: white;
        padding: 5px 10px;
        border-radius: 20px;
        font-size: 14px;
        font-weight: bold;
    }}
    
    /* Header con logo */
    .header-container {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 10px 0;
        margin-bottom: 20px;
        border-bottom: 2px solid {COLORES['secondary']};
    }}
    
    .logo-container {{
        display: flex;
        align-items: center;
        gap: 15px;
    }}
    
    .company-name {{
        font-size: 24px;
        font-weight: bold;
        color: {COLORES['primary']};
        text-align: right;
    }}
    
    .title-container {{
        margin-top: 10px;
        margin-bottom: 20px;
    }}
    
    .main-title {{
        font-size: 32px;
        font-weight: bold;
        color: {COLORES['primary']};
        margin-bottom: 5px;
    }}
    
    .subtitle {{
        font-size: 18px;
        color: {COLORES['secondary']};
    }}
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------------
# PROFESIONALES_INFO - Diccionario de médicos ACTUALIZADO
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
    "CASACCIA, MARCELO AGUSTIN": {"especialidad": "RODILLA", "tipo": "CONSULTOR"},
    # Nuevos médicos
    "GALLARDO CALERO, IRENE": {"especialidad": "MANO", "tipo": "CONSULTOR"},
    "FERNANDEZ DE RETANA, PABLO": {"especialidad": "PIE Y TOBILLO", "tipo": "CONSULTOR"},
    "LECHA NADAL, NIL": {"especialidad": "PIE Y TOBILLO", "tipo": "ESPECIALISTA"},
    "JORDAN GASCON, MARC": {"especialidad": "CADERA", "tipo": "ESPECIALISTA"},
    "BENITO CASTILLO, DAVID": {"especialidad": "CADERA", "tipo": "CONSULTOR"},
    "PASSACANTANDO, FRANCO": {"especialidad": "ORTOPEDIA INFANTIL", "tipo": "CONSULTOR"},
    "COROMINAS FRANCES, LAURA": {"especialidad": "ORTOPEDIA INFANTIL", "tipo": "CONSULTOR"}
}

# -------------------------------------------------------------------
# CARGA DE USUARIOS DESDE STREAMLIT SECRETS (SIN MENSAJE DE ÉXITO)
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
            
        # Eliminado el mensaje de éxito
            
    except Exception as e:
        # Si no hay secrets, intentar cargar desde archivo local
        try:
            if os.path.exists('.streamlit/secrets.toml'):
                import toml
                secrets_local = toml.load('.streamlit/secrets.toml')
                admin_pass = secrets_local["usuarios"]["admin_password"]
                medico_default = secrets_local["usuarios"]["medico_password"]
                credenciales_medicos = secrets_local.get("credenciales_medicos", {})
                # Eliminado el mensaje de info
            else:
                # SOLO PARA DESARROLLO - NUNCA EN PRODUCCIÓN
                admin_pass = "admin123"
                medico_default = "medico123"
                credenciales_medicos = {}
                # Eliminado el mensaje de warning
        except:
            # Último recurso - solo para pruebas
            admin_pass = "admin123"
            medico_default = "medico123"
            credenciales_medicos = {}
            # Eliminado el mensaje de warning
    
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
        },
        # Nuevos médicos
        "gallardo.irene": {
            "password": credenciales_medicos.get("gallardo_irene", medico_default),
            "nombre": "Dra. Irene Gallardo",
            "rol": "medico",
            "profesional": "GALLARDO CALERO, IRENE",
            "email": "i.gallardo@osa.com"
        },
        "fernandez.pablo": {
            "password": credenciales_medicos.get("fernandez_pablo", medico_default),
            "nombre": "Dr. Pablo Fernandez",
            "rol": "medico",
            "profesional": "FERNANDEZ DE RETANA, PABLO",
            "email": "p.fernandez@osa.com"
        },
        "lecha.nil": {
            "password": credenciales_medicos.get("lecha_nil", medico_default),
            "nombre": "Dr. Nil Lecha",
            "rol": "medico",
            "profesional": "LECHA NADAL, NIL",
            "email": "n.lecha@osa.com"
        },
        "jordan.marc": {
            "password": credenciales_medicos.get("jordan_marc", medico_default),
            "nombre": "Dr. Marc Jordan",
            "rol": "medico",
            "profesional": "JORDAN GASCON, MARC",
            "email": "m.jordan@osa.com"
        },
        "benito.david": {
            "password": credenciales_medicos.get("benito_david", medico_default),
            "nombre": "Dr. David Benito",
            "rol": "medico",
            "profesional": "BENITO CASTILLO, DAVID",
            "email": "d.benito@osa.com"
        },
        "passacantando.franco": {
            "password": credenciales_medicos.get("passacantando_franco", medico_default),
            "nombre": "Dr. Franco Passacantando",
            "rol": "medico",
            "profesional": "PASSACANTANDO, FRANCO",
            "email": "f.passacantando@osa.com"
        },
        "corominas.laura": {
            "password": credenciales_medicos.get("corominas_laura", medico_default),
            "nombre": "Dra. Laura Corominas",
            "rol": "medico",
            "profesional": "COROMINAS FRANCES, LAURA",
            "email": "l.corominas@osa.com"
        }
    }
    
    usuarios.update(medicos)
    return usuarios

# -------------------------------------------------------------------
# FUNCIÓN PARA MOSTRAR HEADER CON LOGO
# -------------------------------------------------------------------
def mostrar_header():
    """Muestra el header con logo y nombre de la empresa"""
    
    # Intentar cargar el logo
    logo_path = "logo.png"
    logo_exists = os.path.exists(logo_path)
    
    col_logo, col_title, col_name = st.columns([1, 2, 2])
    
    with col_logo:
        if logo_exists:
            st.image(logo_path, width=80)
        else:
            # Placeholder si no existe el logo
            st.markdown(f"""
            <div style="width:80px; height:80px; background-color:{COLORES['primary']}; border-radius:10px; display:flex; align-items:center; justify-content:center;">
                <span style="color:white; font-size:24px;">🏥</span>
            </div>
            """, unsafe_allow_html=True)
    
    with col_title:
        st.markdown(f"""
        <div style="margin-top:15px;">
            <span style="font-size:20px; font-weight:bold; color:{COLORES['primary']};">OSA Análisis Financiero</span>
        </div>
        """, unsafe_allow_html=True)
    
    with col_name:
        st.markdown(f"""
        <div style="text-align:right; margin-top:15px;">
            <span style="font-size:24px; font-weight:bold; color:{COLORES['primary']};">Orthopaedic Specialist Alliance</span>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")

# -------------------------------------------------------------------
# AUTENTICACIÓN
# -------------------------------------------------------------------
def check_password():
    """Sistema de autenticación con Streamlit Secrets"""
    
    # Cargar usuarios desde secrets
    USUARIOS = cargar_usuarios()
    
    def login_form():
        with st.form("Credentials"):
            # Mostrar header en login
            mostrar_header()
            
            st.markdown(f"""
            <div style='text-align: center; padding: 20px;'>
                <h2 style='color: {COLORES['primary']}'>Sistema de Análisis Médico</h2>
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
# FUNCIÓN PARA TABLA DETALLADA DE ADMIN
# -------------------------------------------------------------------
def tabla_detalle_admin(df):
    """Genera la tabla detallada para administradores con todos los médicos"""
    
    st.subheader("📋 Detalle de Servicios - Todos los Médicos")
    
    # -----------------------------------------------------------------
    # PASO 1: DETECTAR COLUMNAS REALES DEL DATAFRAME
    # -----------------------------------------------------------------
    columnas_df = df.columns.tolist()
    
    # Mapeo de nombres de columna que podrían significar "Aseguradora"
    posibles_nombres_aseguradora = [
        'Aseguradora', 'aseguradora', 'ASEGURADORA',
        'Aseguradora ', ' ASEGURADORA',
        'Nombre Aseguradora', 'Compañía', 'CIA', 'Cia',
        'Aseguradora Nombre', 'Aseguradora Name',
        'Insurance', 'INSURANCE', 'insurance',
        'Insurance Company', 'COMPANY', 'Company'
    ]
    
    # Buscar qué columna del DataFrame coincide con alguna de las posibles
    columna_aseguradora_real = None
    for posible in posibles_nombres_aseguradora:
        if posible in columnas_df:
            columna_aseguradora_real = posible
            break
    
    # -----------------------------------------------------------------
    # PASO 2: DEFINIR COLUMNAS DESEADAS CON LOS NOMBRES REALES
    # -----------------------------------------------------------------
    mapeo_columnas = {
        'Fecha del Servicio': 'Fecha del servicio',
        'Profesional': 'Profesional',
        'Descripción de Prestación': 'Descripción de Prestación',
        'Importe Total': 'Monto Cobrado por Vithas (€)',
        '% Liquidación': '% Liquidación',
        'Importe HHMM': 'Importe Cobrado OSA (€)'
    }
    
    # Agregar la columna de aseguradora SOLO si existe
    if columna_aseguradora_real:
        mapeo_columnas[columna_aseguradora_real] = 'Aseguradora'
    
    # -----------------------------------------------------------------
    # PASO 3: VERIFICAR QUÉ COLUMNAS EXISTEN REALMENTE
    # -----------------------------------------------------------------
    columnas_existentes = [col for col in mapeo_columnas.keys() if col in df.columns]
    
    if not columnas_existentes:
        st.warning("⚠️ No se encontraron las columnas necesarias para mostrar el detalle de servicios.")
        with st.expander("🔍 Ver columnas disponibles en el archivo"):
            st.write(columnas_df)
        return
    
    # -----------------------------------------------------------------
    # PASO 4: CREAR DATAFRAME CON LAS COLUMNAS SELECCIONADAS
    # -----------------------------------------------------------------
    df_detalle = df[columnas_existentes].copy()
    
    # Renombrar columnas
    renombres = {}
    for col_original, col_nueva in mapeo_columnas.items():
        if col_original in df_detalle.columns:
            renombres[col_original] = col_nueva
    
    df_detalle = df_detalle.rename(columns=renombres)
    
    # -----------------------------------------------------------------
    # PASO 5: CONSTRUIR ORDEN DE COLUMNAS DINÁMICAMENTE
    # -----------------------------------------------------------------
    orden_columnas = ['Fecha del servicio', 'Profesional']
    
    # Agregar Aseguradora SOLO si existe
    if 'Aseguradora' in df_detalle.columns:
        orden_columnas.append('Aseguradora')
    
    # Agregar el resto de columnas
    orden_columnas.extend([
        'Descripción de Prestación',
        'Monto Cobrado por Vithas (€)',
        '% Liquidación',
        'Importe Cobrado OSA (€)'
    ])
    
    # Solo mantener columnas que realmente existen
    orden_columnas = [col for col in orden_columnas if col in df_detalle.columns]
    df_detalle = df_detalle[orden_columnas]
    
    # -----------------------------------------------------------------
    # PASO 6: FORMATEAR FECHAS
    # -----------------------------------------------------------------
    if 'Fecha del servicio' in df_detalle.columns:
        df_detalle['Fecha del servicio'] = pd.to_datetime(
            df_detalle['Fecha del servicio'], 
            errors='coerce'
        ).dt.strftime('%d/%m/%Y')
    
    # -----------------------------------------------------------------
    # PASO 7: FILTROS PARA ADMIN
    # -----------------------------------------------------------------
    col_f1, col_f2 = st.columns(2)
    
    with col_f1:
        medicos = ['TODOS'] + sorted(df_detalle['Profesional'].unique().tolist())
        medico_filtro = st.selectbox("👨‍⚕️ Filtrar por Médico", medicos, key="admin_filtro_medico")
    
    with col_f2:
        # Solo mostrar filtro de aseguradora si existe la columna
        if 'Aseguradora' in df_detalle.columns:
            aseguradoras = ['TODAS'] + sorted(df_detalle['Aseguradora'].dropna().unique().tolist())
            aseguradora_filtro = st.selectbox("🏥 Filtrar por Aseguradora", aseguradoras, key="admin_filtro_aseguradora")
        else:
            aseguradora_filtro = 'TODAS'
            st.info("ℹ️ Columna 'Aseguradora' no encontrada en el archivo")
    
    # -----------------------------------------------------------------
    # PASO 8: APLICAR FILTROS
    # -----------------------------------------------------------------
    df_detalle_filtrado = df_detalle.copy()
    
    if medico_filtro != 'TODOS':
        df_detalle_filtrado = df_detalle_filtrado[df_detalle_filtrado['Profesional'] == medico_filtro]
    
    if 'Aseguradora' in df_detalle.columns and aseguradora_filtro != 'TODAS':
        df_detalle_filtrado = df_detalle_filtrado[df_detalle_filtrado['Aseguradora'] == aseguradora_filtro]
    
    # -----------------------------------------------------------------
    # PASO 9: MÉTRICAS DEL FILTRO
    # -----------------------------------------------------------------
    col_m1, col_m2, col_m3 = st.columns(3)
    
    with col_m1:
        st.metric("📌 Registros", f"{len(df_detalle_filtrado):,}")
    
    with col_m2:
        total_vithas = df_detalle_filtrado['Monto Cobrado por Vithas (€)'].sum() if 'Monto Cobrado por Vithas (€)' in df_detalle_filtrado.columns else 0
        st.metric("💰 Total Vithas", f"€{total_vithas:,.2f}")
    
    with col_m3:
        total_osa = df_detalle_filtrado['Importe Cobrado OSA (€)'].sum() if 'Importe Cobrado OSA (€)' in df_detalle_filtrado.columns else 0
        st.metric("💵 Total OSA", f"€{total_osa:,.2f}")
    
    # -----------------------------------------------------------------
    # PASO 10: CONFIGURACIÓN DE COLUMNAS PARA LA TABLA
    # -----------------------------------------------------------------
    column_config = {
        "Fecha del servicio": st.column_config.TextColumn("Fecha"),
        "Profesional": st.column_config.TextColumn("Médico"),
        "Descripción de Prestación": st.column_config.TextColumn("Prestación"),
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
    
    # Agregar Aseguradora a la configuración SOLO si existe
    if 'Aseguradora' in df_detalle_filtrado.columns:
        column_config["Aseguradora"] = st.column_config.TextColumn("Aseguradora")
    
    # -----------------------------------------------------------------
    # PASO 11: MOSTRAR TABLA
    # -----------------------------------------------------------------
    st.dataframe(
        df_detalle_filtrado,
        use_container_width=True,
        hide_index=True,
        column_config=column_config
    )
    
    # -----------------------------------------------------------------
    # PASO 12: BOTÓN DE DESCARGA
    # -----------------------------------------------------------------
    if st.button("📥 Descargar Detalle Completo (Excel)", use_container_width=True, type="primary"):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Hoja 1: Detalle completo
            df_detalle_filtrado.to_excel(writer, index=False, sheet_name='Detalle_Servicios')
            
            # Hoja 2: Resumen por médico
            if 'Profesional' in df_detalle_filtrado.columns:
                resumen_medico = df_detalle_filtrado.groupby('Profesional').agg({
                    'Monto Cobrado por Vithas (€)': 'sum',
                    'Importe Cobrado OSA (€)': 'sum',
                    'Fecha del servicio': 'count'
                }).reset_index()
                resumen_medico.columns = ['Médico', 'Total Vithas', 'Total OSA', 'Registros']
                resumen_medico.to_excel(writer, index=False, sheet_name='Resumen_Medicos')
            
            # Hoja 3: Resumen por aseguradora (solo si existe)
            if 'Aseguradora' in df_detalle_filtrado.columns:
                resumen_aseguradora = df_detalle_filtrado.groupby('Aseguradora').agg({
                    'Monto Cobrado por Vithas (€)': 'sum',
                    'Importe Cobrado OSA (€)': 'sum',
                    'Fecha del servicio': 'count'
                }).reset_index()
                resumen_aseguradora.columns = ['Aseguradora', 'Total Vithas', 'Total OSA', 'Registros']
                resumen_aseguradora.to_excel(writer, index=False, sheet_name='Resumen_Aseguradoras')
        
        output.seek(0)
        
        st.download_button(
            label=f"⬇️ Confirmar Descarga Excel",
            data=output,
            file_name=f"detalle_osa_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

# -------------------------------------------------------------------
# PROYECCIÓN GERENCIA - ACTUALIZADA
# -------------------------------------------------------------------
def proyeccion_gerencia(df):
    """Calcula proyecciones financieras para gerencia"""
    
    st.markdown(f"""
    <div class='custom-card'>
        <h2 style='color: {COLORES['primary']}; margin-bottom: 0;'>📈 Proyección Gerencia</h2>
        <p style='color: {COLORES['secondary']};'>Análisis de punto de equilibrio y márgenes OSA</p>
    </div>
    """, unsafe_allow_html=True)
    
    # -----------------------------------------------------------------
    # GASTOS FIJOS MENSUALES - ACTUALIZADOS
    # -----------------------------------------------------------------
    st.subheader("🏢 Gastos Fijos Mensuales OSA")
    
    col_g1, col_g2, col_g3, col_g4 = st.columns(4)
    
    with col_g1:
        st.markdown(f"""
        <div class='stMetric'>
            <label>👥 SF</label>
            <div style='font-size: 24px; font-weight: bold; color: {COLORES['primary']};'>
                €3,290
            </div>
            <small>Costo mensual empresa</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col_g2:
        st.markdown(f"""
        <div class='stMetric'>
            <label>👤 IR</label>
            <div style='font-size: 24px; font-weight: bold; color: {COLORES['primary']};'>
                €2,835
            </div>
            <small>Costo mensual empresa</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col_g3:
        st.markdown(f"""
        <div class='stMetric'>
            <label>👨‍⚕️ Jefe Servicio</label>
            <div style='font-size: 24px; font-weight: bold; color: {COLORES['primary']};'>
                €3,000
            </div>
            <small>Honorarios mensuales</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col_g4:
        st.markdown(f"""
        <div class='stMetric'>
            <label>🛡️ RC Profesional</label>
            <div style='font-size: 24px; font-weight: bold; color: {COLORES['primary']};'>
                €500
            </div>
            <small>Seguro responsabilidad civil</small>
        </div>
        """, unsafe_allow_html=True)
    
    col_g5, col_g6, col_g7 = st.columns(3)
    
    with col_g5:
        st.markdown(f"""
        <div class='stMetric'>
            <label>🌐 Otros (Web, Google, etc)</label>
            <div style='font-size: 24px; font-weight: bold; color: {COLORES['primary']};'>
                €100
            </div>
            <small>Mantenimiento, publicidad</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col_g6:
        st.markdown(f"""
        <div class='stMetric'>
            <label>⚖️ Despacho legal y laboral</label>
            <div style='font-size: 24px; font-weight: bold; color: {COLORES['primary']};'>
                €400
            </div>
            <small>Asesoría legal y laboral</small>
        </div>
        """, unsafe_allow_html=True)
    
    # Calcular total gastos fijos
    gastos_fijos = {
        'SF': 3290,
        'IR': 2835,
        'Jefe Servicio': 3000,
        'RC Profesional': 500,
        'Otros': 100,
        'Despacho legal': 400
    }
    
    total_gastos_fijos = sum(gastos_fijos.values())
    
    with col_g7:
        st.markdown(f"""
        <div class='stMetric'>
            <label>💰 TOTAL GASTOS FIJOS</label>
            <div style='font-size: 28px; font-weight: bold; color: {COLORES['primary']};'>
                €{total_gastos_fijos:,.2f}
            </div>
            <small>Mensuales</small>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # -----------------------------------------------------------------
    # ANÁLISIS DE MÁRGENES ACTUALES (CON DATOS REALES)
    # -----------------------------------------------------------------
    st.subheader("📊 Análisis de Márgenes Reales (Datos Cargados)")
    
    if df is not None and not df.empty:
        # Calcular métricas globales
        total_hhmm = df['Importe HHMM'].sum()
        total_medicos = df['Profesional'].nunique()
        
        # Clasificar médicos por tipo
        medicos_consultor = df[df['Tipo Médico'] == 'CONSULTOR']['Profesional'].nunique()
        medicos_especialista = df[df['Tipo Médico'] == 'ESPECIALISTA']['Profesional'].nunique()
        
        # Calcular margen real promedio
        total_pagar_medicos = 0
        total_osa_retiene = 0
        
        for medico in df['Profesional'].unique():
            df_med = df[df['Profesional'] == medico]
            subesp = df_med['Subespecialidad'].iloc[0]
            promedio, _, _ = calcular_promedio_subespecialidad(df, subesp)
            kpis = calcular_a_cobrar_individual(df_med, promedio)
            if kpis:
                total_pagar_medicos += kpis['total_a_cobrar']
                total_osa_retiene += kpis['a_cobrar_osa']
        
        margen_real_promedio = (total_osa_retiene / total_hhmm * 100) if total_hhmm > 0 else 0
        
        col_r1, col_r2, col_r3, col_r4 = st.columns(4)
        
        with col_r1:
            st.metric(
                "💰 Facturación OSA (HHMM)",
                f"€{total_hhmm:,.2f}",
                help="Total importe HHMM del período"
            )
        
        with col_r2:
            st.metric(
                "💳 Pago a Médicos",
                f"€{total_pagar_medicos:,.2f}",
                help="Total a liquidar a médicos"
            )
        
        with col_r3:
            st.metric(
                "🏥 OSA Retiene",
                f"€{total_osa_retiene:,.2f}",
                delta=f"{margen_real_promedio:.1f}% margen",
                delta_color="normal",
                help="Margen bruto OSA"
            )
        
        with col_r4:
            st.metric(
                "👥 Composición Médicos",
                f"{medicos_consultor + medicos_especialista}",
                delta=f"{medicos_consultor} Consultores / {medicos_especialista} Especialistas",
                delta_color="off",
                help="Distribución por tipo"
            )
        
        # Calcular cobertura de gastos con datos reales
        meses_periodo = df['Mes-Año'].nunique()
        osa_mensual_promedio = total_osa_retiene / meses_periodo if meses_periodo > 0 else 0
        
        col_c1, col_c2, col_c3 = st.columns(3)
        
        with col_c1:
            st.metric(
                "📅 Período analizado",
                f"{meses_periodo} meses",
                help="Meses con datos en el archivo"
            )
        
        with col_c2:
            st.metric(
                "📊 OSA Mensual Promedio",
                f"€{osa_mensual_promedio:,.2f}",
                help="Margen OSA promedio por mes"
            )
        
        with col_c3:
            cobertura_gastos = (osa_mensual_promedio / total_gastos_fijos) * 100 if total_gastos_fijos > 0 else 0
            st.metric(
                "✅ Cobertura Gastos Fijos",
                f"{cobertura_gastos:.1f}%",
                delta="Superávit" if cobertura_gastos >= 100 else "Déficit",
                delta_color="normal" if cobertura_gastos >= 100 else "inverse",
                help=f"OSA mensual vs Gastos: €{osa_mensual_promedio:,.2f} / €{total_gastos_fijos:,.2f}"
            )
        
        # NUEVO KPI: Diferencia a pagar por Socios
        diferencia_socios = total_gastos_fijos - osa_mensual_promedio
        
        st.markdown("---")
        st.subheader("💰 Distribución a Socios")
        
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        
        with col_s1:
            st.markdown(f"""
            <div class='stMetric' style='background-color: #fff3e0;'>
                <label style='color: {COLORES['primary']};'>💶 Diferencia a pagar por Socios</label>
                <div style='font-size: 28px; font-weight: bold; color: {COLORES['primary']};'>
                    €{max(diferencia_socios, 0):,.2f}
                </div>
                <small>Total Gastos - OSA Retiene</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col_s2:
            aporte_fallone = max(diferencia_socios, 0) * 0.70
            st.markdown(f"""
            <div class='stMetric'>
                <label>👤 Fallone (70%)</label>
                <div style='font-size: 24px; font-weight: bold; color: {COLORES['primary']};'>
                    €{aporte_fallone:,.2f}
                </div>
                <small>Aporte mensual</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col_s3:
            aporte_puigdellivol = max(diferencia_socios, 0) * 0.225
            st.markdown(f"""
            <div class='stMetric'>
                <label>👤 Puigdellivol (22.5%)</label>
                <div style='font-size: 24px; font-weight: bold; color: {COLORES['primary']};'>
                    €{aporte_puigdellivol:,.2f}
                </div>
                <small>Aporte mensual</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col_s4:
            aporte_ortega = max(diferencia_socios, 0) * 0.075
            st.markdown(f"""
            <div class='stMetric'>
                <label>👤 Ortega (7.5%)</label>
                <div style='font-size: 24px; font-weight: bold; color: {COLORES['primary']};'>
                    €{aporte_ortega:,.2f}
                </div>
                <small>Aporte mensual</small>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("⚠️ No hay datos cargados. Usando escenarios simulados para proyección.")
        medicos_consultor = 0
        medicos_especialista = 0
        margen_real_promedio = 0
        osa_mensual_promedio = 0
    
    st.markdown("---")
    
    # -----------------------------------------------------------------
    # PROYECCIÓN DE ESCENARIOS
    # -----------------------------------------------------------------
    st.subheader("🎯 Proyección de Escenarios - Facturación Necesaria")
    
    st.markdown(f"""
    <div style='background-color: {COLORES['background']}; padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
        <h4 style='color: {COLORES['primary']};'>📌 Punto de Equilibrio</h4>
        <p>OSA necesita generar <strong>€{total_gastos_fijos:,.2f} mensuales</strong> en margen (lo que retiene) para cubrir gastos fijos.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Selectores de escenario
    col_s1, col_s2, col_s3 = st.columns(3)
    
    with col_s1:
        st.markdown("**👨‍⚕️ Composición de Médicos**")
        escenario_consultores = st.number_input(
            "Nº Consultores",
            min_value=0,
            max_value=50,
            value=max(medicos_consultor, 5),
            step=1,
            key="escenario_consultores"
        )
        
        escenario_especialistas = st.number_input(
            "Nº Especialistas",
            min_value=0,
            max_value=50,
            value=max(medicos_especialista, 3),
            step=1,
            key="escenario_especialistas"
        )
    
    with col_s2:
        st.markdown("**📊 Distribución por Rendimiento**")
        pct_encima_promedio = st.slider(
            "% Médicos por encima del promedio",
            min_value=0,
            max_value=100,
            value=40,
            step=5,
            help="Porcentaje de médicos que facturan por encima del promedio de su subespecialidad",
            key="pct_encima"
        )
        
        st.markdown(f"""
        <div style='margin-top: 25px;'>
            <small>Distribución:</small><br>
            <strong>{pct_encima_promedio}%</strong> por encima (92%/90%)<br>
            <strong>{100 - pct_encima_promedio}%</strong> por debajo (88%/85%)
        </div>
        """, unsafe_allow_html=True)
    
    with col_s3:
        st.markdown("**💰 Facturación Media por Médico**")
        facturacion_media = st.number_input(
            "Facturación HHMM mensual media (€)",
            min_value=1000,
            max_value=100000,
            value=20000,
            step=1000,
            help="Importe HHMM promedio por médico al mes",
            key="facturacion_media"
        )
    
    st.markdown("---")
    
    # -----------------------------------------------------------------
    # CÁLCULOS DE PROYECCIÓN
    # -----------------------------------------------------------------
    
    # Calcular porcentajes según distribución
    total_medicos_escenario = escenario_consultores + escenario_especialistas
    
    # Distribución de médicos por rendimiento
    medicos_encima = int(total_medicos_escenario * (pct_encima_promedio / 100))
    medicos_debajo = total_medicos_escenario - medicos_encima
    
    # Distribución por tipo y rendimiento
    consultores_encima = int(escenario_consultores * (pct_encima_promedio / 100))
    consultores_debajo = escenario_consultores - consultores_encima
    
    especialistas_encima = int(escenario_especialistas * (pct_encima_promedio / 100))
    especialistas_debajo = escenario_especialistas - especialistas_encima
    
    # Calcular márgenes individuales
    margen_consultor_encima = 8.0
    margen_consultor_debajo = 12.0
    margen_especialista_encima = 10.0
    margen_especialista_debajo = 15.0
    
    # Calcular margen ponderado
    total_margen = (
        consultores_encima * margen_consultor_encima +
        consultores_debajo * margen_consultor_debajo +
        especialistas_encima * margen_especialista_encima +
        especialistas_debajo * margen_especialista_debajo
    )
    
    margen_ponderado = total_margen / total_medicos_escenario if total_medicos_escenario > 0 else 0
    
    # Calcular facturación necesaria
    facturacion_hhmm_necesaria = total_gastos_fijos / (margen_ponderado / 100) if margen_ponderado > 0 else 0
    facturacion_vithas_necesaria = facturacion_hhmm_necesaria / 0.70
    
    # Facturación por médico
    facturacion_hhmm_por_medico = facturacion_hhmm_necesaria / total_medicos_escenario if total_medicos_escenario > 0 else 0
    
    # -----------------------------------------------------------------
    # RESULTADOS DE PROYECCIÓN
    # -----------------------------------------------------------------
    st.subheader("🎯 Resultados de Proyección")
    
    col_res1, col_res2, col_res3 = st.columns(3)
    
    with col_res1:
        st.markdown(f"""
        <div class='stMetric' style='background: linear-gradient(135deg, {COLORES['primary']} 0%, {COLORES['primary']}ee 100%);'>
            <label style='color: white !important;'>📊 MARGEN PONDERADO</label>
            <div style='font-size: 36px; font-weight: bold; color: white;'>
                {margen_ponderado:.1f}%
            </div>
            <small style='color: rgba(255,255,255,0.9);'>Margen OSA según composición</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col_res2:
        st.markdown(f"""
        <div class='stMetric' style='background: linear-gradient(135deg, {COLORES['secondary']} 0%, {COLORES['secondary']}ee 100%);'>
            <label style='color: {COLORES['primary']} !important;'>💰 FACTURACIÓN HHMM NECESARIA</label>
            <div style='font-size: 36px; font-weight: bold; color: {COLORES['primary']};'>
                €{facturacion_hhmm_necesaria:,.0f}
            </div>
            <small style='color: {COLORES['primary']};'>Mensual para cubrir gastos</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col_res3:
        st.markdown(f"""
        <div class='stMetric'>
            <label>💳 FACTURACIÓN VITHAS (100%)</label>
            <div style='font-size: 28px; font-weight: bold; color: {COLORES['primary']};'>
                €{facturacion_vithas_necesaria:,.0f}
            </div>
            <small>Estimado al 70% liquidación</small>
        </div>
        """, unsafe_allow_html=True)
    
    col_res4, col_res5, col_res6 = st.columns(3)
    
    with col_res4:
        st.metric(
            "👥 Total Médicos Necesarios",
            f"{total_medicos_escenario}",
            help=f"{escenario_consultores} Consultores / {escenario_especialistas} Especialistas"
        )
    
    with col_res5:
        st.metric(
            "📈 Facturación HHMM por Médico",
            f"€{facturacion_hhmm_por_medico:,.0f}",
            delta=f"vs €{facturacion_media:,.0f} objetivo",
            delta_color="off"
        )
    
    with col_res6:
        cobertura_objetivo = (facturacion_hhmm_por_medico / facturacion_media) * 100 if facturacion_media > 0 else 0
        st.metric(
            "🎯 % Objetivo por Médico",
            f"{cobertura_objetivo:.1f}%",
            help="Porcentaje de la facturación media objetivo necesaria"
        )
    
    st.markdown("---")
    
    # -----------------------------------------------------------------
    # TABLA DE DISTRIBUCIÓN DETALLADA
    # -----------------------------------------------------------------
    st.subheader("📋 Distribución Detallada del Escenario")
    
    distribucion_data = []
    
    if consultores_encima > 0:
        distribucion_data.append({
            'Tipo': 'Consultor',
            'Rendimiento': 'Por encima',
            'Cantidad': consultores_encima,
            'Margen OSA': f'{margen_consultor_encima}%',
            '% Cobrar': '92%',
            'Aporte por médico (€)': facturacion_media * (margen_consultor_encima / 100),
            'Aporte total (€)': consultores_encima * facturacion_media * (margen_consultor_encima / 100)
        })
    
    if consultores_debajo > 0:
        distribucion_data.append({
            'Tipo': 'Consultor',
            'Rendimiento': 'Por debajo',
            'Cantidad': consultores_debajo,
            'Margen OSA': f'{margen_consultor_debajo}%',
            '% Cobrar': '88%',
            'Aporte por médico (€)': facturacion_media * (margen_consultor_debajo / 100),
            'Aporte total (€)': consultores_debajo * facturacion_media * (margen_consultor_debajo / 100)
        })
    
    if especialistas_encima > 0:
        distribucion_data.append({
            'Tipo': 'Especialista',
            'Rendimiento': 'Por encima',
            'Cantidad': especialistas_encima,
            'Margen OSA': f'{margen_especialista_encima}%',
            '% Cobrar': '90%',
            'Aporte por médico (€)': facturacion_media * (margen_especialista_encima / 100),
            'Aporte total (€)': especialistas_encima * facturacion_media * (margen_especialista_encima / 100)
        })
    
    if especialistas_debajo > 0:
        distribucion_data.append({
            'Tipo': 'Especialista',
            'Rendimiento': 'Por debajo',
            'Cantidad': especialistas_debajo,
            'Margen OSA': f'{margen_especialista_debajo}%',
            '% Cobrar': '85%',
            'Aporte por médico (€)': facturacion_media * (margen_especialista_debajo / 100),
            'Aporte total (€)': especialistas_debajo * facturacion_media * (margen_especialista_debajo / 100)
        })
    
    df_distribucion = pd.DataFrame(distribucion_data)
    
    if not df_distribucion.empty:
        st.dataframe(
            df_distribucion,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Tipo": "Tipo Médico",
                "Rendimiento": "Rendimiento",
                "Cantidad": st.column_config.NumberColumn("Nº Médicos", format="%d"),
                "Margen OSA": "Margen OSA",
                "% Cobrar": "% Médico",
                "Aporte por médico (€)": st.column_config.NumberColumn("Aporte x Médico", format="€%.0f"),
                "Aporte total (€)": st.column_config.NumberColumn("Aporte Total", format="€%.0f")
            }
        )
        
        # Totales
        col_t1, col_t2, col_t3 = st.columns(3)
        
        with col_t1:
            total_aportes = df_distribucion['Aporte total (€)'].sum()
            st.metric(
                "💰 TOTAL APORTE OSA ESTIMADO",
                f"€{total_aportes:,.0f}",
                delta=f"vs €{total_gastos_fijos:,.0f} gastos",
                delta_color="normal" if total_aportes >= total_gastos_fijos else "inverse"
            )
        
        with col_t2:
            st.metric(
                "🎯 DIFERENCIA vs GASTOS",
                f"€{total_aportes - total_gastos_fijos:,.0f}",
                delta="Superávit" if total_aportes >= total_gastos_fijos else "Déficit",
                delta_color="normal" if total_aportes >= total_gastos_fijos else "inverse"
            )
        
        with col_t3:
            st.metric(
                "📊 MARGEN SOBRE GASTOS",
                f"{(total_aportes / total_gastos_fijos - 1) * 100:.1f}%" if total_gastos_fijos > 0 else "0%",
                help="Porcentaje de gastos cubiertos"
            )
    
    st.markdown("---")
    
    # -----------------------------------------------------------------
    # RECOMENDACIONES
    # -----------------------------------------------------------------
    st.subheader("💡 Recomendaciones")
    
    if facturacion_hhmm_por_medico > facturacion_media * 1.2:
        recomendacion = "🔴 **Alta exigencia**: La facturación por médico necesaria es muy superior al objetivo. Se requiere:"
        items = [
            "Aumentar el número de médicos",
            "Mejorar el rendimiento de médicos actuales (pasar a 'por encima')",
            "Incrementar el ratio de especialistas (mayor margen)",
            "Revisar estructura de gastos"
        ]
    elif facturacion_hhmm_por_medico < facturacion_media * 0.8:
        recomendacion = "🟢 **Escenario sostenible**: La facturación necesaria está por debajo del objetivo."
        items = [
            "El modelo es rentable con la composición actual",
            "Posibilidad de reinvertir en crecimiento",
            "Evaluar aumento de plantilla"
        ]
    else:
        recomendacion = "🟡 **Escenario alcanzable**: La facturación necesaria está dentro del rango objetivo."
        items = [
            "Mantener la composición actual de médicos",
            "Enfocar en mantener a médicos por encima del promedio",
            "Seguimiento mensual de márgenes"
        ]
    
    st.markdown(f"""
    <div style='background-color: {COLORES['background']}; padding: 20px; border-radius: 10px;'>
        <h4 style='color: {COLORES['primary']};'>{recomendacion}</h4>
        <ul style='margin-top: 10px;'>
            {''.join([f'<li>{item}</li>' for item in items])}
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Botón de descarga de proyección
    if st.button("📥 Descargar Proyección (Excel)", use_container_width=True, type="primary"):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Hoja 1: Gastos fijos
            df_gastos = pd.DataFrame([
                {'Concepto': 'SF', 'Monto': 3290},
                {'Concepto': 'IR', 'Monto': 2835},
                {'Concepto': 'Jefe Servicio', 'Monto': 3000},
                {'Concepto': 'RC Profesional', 'Monto': 500},
                {'Concepto': 'Otros', 'Monto': 100},
                {'Concepto': 'Despacho legal y laboral', 'Monto': 400},
                {'Concepto': 'TOTAL', 'Monto': total_gastos_fijos}
            ])
            df_gastos.to_excel(writer, index=False, sheet_name='Gastos_Fijos')
            
            # Hoja 2: Proyección
            df_proyeccion = pd.DataFrame([{
                'Composición': f'{escenario_consultores}C / {escenario_especialistas}E',
                'Total Médicos': total_medicos_escenario,
                '% Encima Promedio': f'{pct_encima_promedio}%',
                'Margen Ponderado': f'{margen_ponderado:.1f}%',
                'Facturación HHMM Necesaria': facturacion_hhmm_necesaria,
                'Facturación Vithas Necesaria': facturacion_vithas_necesaria,
                'Facturación HHMM x Médico': facturacion_hhmm_por_medico,
                'Gastos Fijos Mensuales': total_gastos_fijos,
                'Aporte OSA Estimado': total_aportes if 'total_aportes' in locals() else 0,
                'Diferencia': (total_aportes - total_gastos_fijos) if 'total_aportes' in locals() else 0
            }])
            df_proyeccion.to_excel(writer, index=False, sheet_name='Proyeccion')
            
            # Hoja 3: Distribución detallada
            if not df_distribucion.empty:
                df_distribucion.to_excel(writer, index=False, sheet_name='Distribucion')
        
        output.seek(0)
        
        st.download_button(
            label="⬇️ Confirmar Descarga Proyección",
            data=output,
            file_name=f"proyeccion_gerencia_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# -------------------------------------------------------------------
# FUNCIÓN DE MATCH DE ARCHIVOS (PARA ADMIN) - CORREGIDA
# -------------------------------------------------------------------
def match_archivos():
    """Compara dos archivos Excel (Mes finalizado real vs Mes Pagado) y encuentra coincidencias"""
    
    st.markdown(f"""
    <div class='custom-card'>
        <h2 style='color: {COLORES['primary']}; margin-bottom: 0;'>🔍 Match de Pagos</h2>
        <p style='color: {COLORES['secondary']};'>Compara lo que debería pagarse vs lo que realmente se pagó</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Función auxiliar para normalizar nombres de médicos
    def normalizar_nombre_medico(nombre):
        """
        Normaliza el nombre del médico para poder comparar:
        - Elimina comas
        - Convierte a mayúsculas
        - Elimina espacios extras
        - Ordena apellido y nombre de forma consistente
        """
        if pd.isna(nombre):
            return ""
        
        nombre_str = str(nombre).strip().upper()
        
        # Eliminar comas y espacios múltiples
        nombre_sin_comas = nombre_str.replace(',', ' ')
        nombre_sin_comas = ' '.join(nombre_sin_comas.split())
        
        # Dividir en partes y ordenar alfabéticamente
        partes = nombre_sin_comas.split()
        partes_ordenadas = sorted(partes)
        
        return ' '.join(partes_ordenadas)
    
    # Explicación del proceso
    with st.expander("ℹ️ ¿Cómo funciona este match?", expanded=False):
        st.markdown("""
        **Criterios de comparación:**
        
        **Archivo 1 - Mes finalizado real** (Lo que deberían haber pagado)
        - Columna: `Fecha`
        - Columna: `Paciente`
        - Columna: `Denomin.prestación`
        - Columna: `Médico de tratamiento (nombre)`
        
        **Archivo 2 - Mes Pagado** (Lo que realmente pagaron)
        - Columna: `Fecha del Servicio`
        - Columna: `NHC Paciente`
        - Columna: `Descripción de Prestación`
        - Columna: `Profesional`
        
        **Importante:** Los nombres de los médicos se normalizan automáticamente:
        - Se eliminan comas
        - Se convierten a mayúsculas
        - Se ordenan las palabras alfabéticamente
        
        Si **las 4 columnas coinciden** después de la normalización, la fila se considera como **"Pagado correctamente"**.
        
        **Nuevas columnas añadidas:**
        - En pestaña "Pagados": Columna "Cobrado OSA (€)" (Importe HHMM del Archivo 2)
        - En pestaña "No Pagados": Columna "Por Cobrar OSA (€)" (SIEMPRE 0, ya que no aparecen en el archivo de pagos)
        """)
    
    # Crear dos columnas para los archivos
    col_arch1, col_arch2 = st.columns(2)
    
    with col_arch1:
        st.markdown(f"**📁 Archivo 1: Mes finalizado real**")
        archivo1 = st.file_uploader(
            "Sube el archivo de lo que deberían haber pagado",
            type=['xlsx', 'xls'],
            key="match_archivo1"
        )
        
        if archivo1 is not None:
            st.success(f"✅ Archivo cargado: {archivo1.name}")
    
    with col_arch2:
        st.markdown(f"**📁 Archivo 2: Mes Pagado**")
        archivo2 = st.file_uploader(
            "Sube el archivo de lo que realmente pagaron",
            type=['xlsx', 'xls'],
            key="match_archivo2"
        )
        
        if archivo2 is not None:
            st.success(f"✅ Archivo cargado: {archivo2.name}")
    
    st.markdown("---")
    
    # Botón para ejecutar el match
    if archivo1 is not None and archivo2 is not None:
        if st.button("🔍 EJECUTAR MATCH", use_container_width=True, type="primary"):
            
            with st.spinner("Procesando archivos y buscando coincidencias..."):
                
                # Cargar archivos
                df1 = pd.read_excel(archivo1)
                df2 = pd.read_excel(archivo2)
                
                # Mostrar información básica
                st.info(f"📊 Archivo 1: {len(df1)} registros | Archivo 2: {len(df2)} registros")
                
                # Verificar que existan las columnas necesarias
                columnas_df1 = ['Fecha', 'Paciente', 'Denomin.prestación', 'Médico de tratamiento (nombre)']
                columnas_df2 = ['Fecha del Servicio', 'NHC Paciente', 'Descripción de Prestación', 'Profesional']
                
                columnas_faltantes_df1 = [col for col in columnas_df1 if col not in df1.columns]
                columnas_faltantes_df2 = [col for col in columnas_df2 if col not in df2.columns]
                
                if columnas_faltantes_df1 or columnas_faltantes_df2:
                    if columnas_faltantes_df1:
                        st.error(f"❌ Archivo 1: Faltan columnas: {', '.join(columnas_faltantes_df1)}")
                    if columnas_faltantes_df2:
                        st.error(f"❌ Archivo 2: Faltan columnas: {', '.join(columnas_faltantes_df2)}")
                    
                    with st.expander("🔍 Ver columnas disponibles en Archivo 1"):
                        st.write(df1.columns.tolist())
                    with st.expander("🔍 Ver columnas disponibles en Archivo 2"):
                        st.write(df2.columns.tolist())
                    
                    st.stop()
                
                # -----------------------------------------------------------------
                # PASO 1: NORMALIZAR COLUMNAS PARA LA COMPARACIÓN
                # -----------------------------------------------------------------
                
                # Copias para no modificar originales
                df1_norm = df1.copy()
                df2_norm = df2.copy()
                
                # Normalizar fechas
                df1_norm['Fecha_norm'] = pd.to_datetime(df1_norm['Fecha'], errors='coerce').dt.date
                df2_norm['Fecha_norm'] = pd.to_datetime(df2_norm['Fecha del Servicio'], errors='coerce').dt.date
                
                # Normalizar paciente (quitar espacios, mayúsculas)
                df1_norm['Paciente_norm'] = df1_norm['Paciente'].astype(str).str.strip().str.upper()
                df2_norm['Paciente_norm'] = df2_norm['NHC Paciente'].astype(str).str.strip().str.upper()
                
                # Normalizar prestación
                df1_norm['Prestacion_norm'] = df1_norm['Denomin.prestación'].astype(str).str.strip().str.upper()
                df2_norm['Prestacion_norm'] = df2_norm['Descripción de Prestación'].astype(str).str.strip().str.upper()
                
                # -----------------------------------------------------------------
                # PASO 2: NORMALIZAR NOMBRES DE MÉDICOS (ELIMINAR COMAS)
                # -----------------------------------------------------------------
                # Aplicar la función de normalización a los nombres de médicos
                df1_norm['Medico_norm'] = df1_norm['Médico de tratamiento (nombre)'].apply(normalizar_nombre_medico)
                df2_norm['Medico_norm'] = df2_norm['Profesional'].apply(normalizar_nombre_medico)
                
                # Mostrar ejemplos de normalización para verificar
                with st.expander("🔍 Ver ejemplos de normalización de nombres", expanded=False):
                    col_ex1, col_ex2 = st.columns(2)
                    
                    with col_ex1:
                        st.markdown("**Archivo 1 - Nombres originales vs normalizados:**")
                        ejemplos_df1 = df1_norm[['Médico de tratamiento (nombre)', 'Medico_norm']].dropna().head(10)
                        st.dataframe(ejemplos_df1, use_container_width=True)
                    
                    with col_ex2:
                        st.markdown("**Archivo 2 - Nombres originales vs normalizados:**")
                        ejemplos_df2 = df2_norm[['Profesional', 'Medico_norm']].dropna().head(10)
                        st.dataframe(ejemplos_df2, use_container_width=True)
                
                # -----------------------------------------------------------------
                # PASO 3: CREAR COLUMNA LLAVE PARA MATCH
                # -----------------------------------------------------------------
                df1_norm['llave_match'] = (
                    df1_norm['Fecha_norm'].astype(str) + '|' +
                    df1_norm['Paciente_norm'] + '|' +
                    df1_norm['Prestacion_norm'] + '|' +
                    df1_norm['Medico_norm']
                )
                
                df2_norm['llave_match'] = (
                    df2_norm['Fecha_norm'].astype(str) + '|' +
                    df2_norm['Paciente_norm'] + '|' +
                    df2_norm['Prestacion_norm'] + '|' +
                    df2_norm['Medico_norm']
                )
                
                # -----------------------------------------------------------------
                # PASO 4: ENCONTRAR COINCIDENCIAS
                # -----------------------------------------------------------------
                
                # Crear conjunto de llaves del archivo 2 (lo pagado)
                llaves_pagadas = set(df2_norm['llave_match'].dropna().unique())
                
                # Marcar en df1 qué registros tienen match
                df1_norm['Match'] = df1_norm['llave_match'].isin(llaves_pagadas)
                
                # Crear DataFrame de resultados (solo los que hicieron match)
                df_match = df1[df1_norm['Match']].copy()
                
                # Crear DataFrame de no pagados (los que NO hicieron match)
                df_no_pagados = df1[~df1_norm['Match']].copy()
                
                # -----------------------------------------------------------------
                # PASO 5: AÑADIR COLUMNAS DE IMPORTES - CORREGIDO
                # -----------------------------------------------------------------
                
                # Para los pagados, añadir columna "Cobrado OSA (€)" con el Importe HHMM del archivo 2
                if not df_match.empty:
                    # Crear un diccionario para mapear llave_match a Importe HHMM del archivo 2
                    # Asegurarse de que la columna Importe HHMM existe en df2
                    if 'Importe HHMM' in df2.columns:
                        df2_norm['Importe_HHMM_Archivo2'] = pd.to_numeric(df2['Importe HHMM'], errors='coerce')
                    else:
                        df2_norm['Importe_HHMM_Archivo2'] = 0
                    
                    mapa_importes = dict(zip(df2_norm['llave_match'], df2_norm['Importe_HHMM_Archivo2']))
                    
                    # Añadir la columna a df_match
                    df_match_con_importes = df_match.copy()
                    df_match_con_importes['Cobrado OSA (€)'] = df_match_con_importes.index.map(
                        lambda idx: mapa_importes.get(df1_norm.loc[idx, 'llave_match'], 0) if idx in df1_norm.index else 0
                    )
                else:
                    df_match_con_importes = df_match.copy()
                    df_match_con_importes['Cobrado OSA (€)'] = 0
                
                # Para los no pagados, añadir columna "Por Cobrar OSA (€)" con valor 0
                # CORREGIDO: Siempre 0 porque no aparecen en el archivo de pagos
                if not df_no_pagados.empty:
                    df_no_pagados_con_importes = df_no_pagados.copy()
                    df_no_pagados_con_importes['Por Cobrar OSA (€)'] = 0  # Siempre 0
                else:
                    df_no_pagados_con_importes = df_no_pagados.copy()
                    df_no_pagados_con_importes['Por Cobrar OSA (€)'] = 0
                
                # -----------------------------------------------------------------
                # PASO 6: MOSTRAR RESULTADOS
                # -----------------------------------------------------------------
                
                st.markdown("---")
                st.subheader("📊 Resultados del Match")
                
                # Métricas principales
                col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                
                with col_m1:
                    st.markdown(f"""
                    <div class='stMetric'>
                        <label>📋 Total Archivo 1</label>
                        <div class='metric-highlight'>{len(df1):,}</div>
                        <small>Registros a verificar</small>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_m2:
                    st.markdown(f"""
                    <div class='stMetric'>
                        <label>✅ Coincidencias</label>
                        <div class='metric-highlight' style='color: #28a745;'>{len(df_match_con_importes):,}</div>
                        <small>Pagados correctamente</small>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_m3:
                    st.markdown(f"""
                    <div class='stMetric'>
                        <label>❌ No pagados</label>
                        <div class='metric-highlight' style='color: #dc3545;'>{len(df_no_pagados_con_importes):,}</div>
                        <small>No encontrados en Archivo 2</small>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_m4:
                    porcentaje_coincidencia = (len(df_match_con_importes) / len(df1) * 100) if len(df1) > 0 else 0
                    st.markdown(f"""
                    <div class='stMetric'>
                        <label>📊 % Coincidencia</label>
                        <div class='metric-highlight'>{porcentaje_coincidencia:.1f}%</div>
                        <small>Tasa de pago</small>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("---")
                
                # -----------------------------------------------------------------
                # PASO 7: FILTROS POR PROFESIONAL Y DESCRIPCIÓN DE PRESTACIÓN
                # -----------------------------------------------------------------
                st.subheader("🔍 Análisis Detallado con Filtros")
                
                col_f1, col_f2 = st.columns(2)
                
                with col_f1:
                    # Obtener lista de profesionales únicos del archivo 1 (usando el original, no el normalizado)
                    profesionales = ['TODOS'] + sorted(df1['Médico de tratamiento (nombre)'].dropna().unique().tolist())
                    profesional_filtro = st.selectbox(
                        "👨‍⚕️ Filtrar por Profesional",
                        profesionales,
                        key="match_filtro_profesional"
                    )
                
                with col_f2:
                    # Obtener lista de prestaciones únicas del archivo 1
                    prestaciones = ['TODAS'] + sorted(df1['Denomin.prestación'].dropna().unique().tolist())
                    prestacion_filtro = st.selectbox(
                        "🩺 Filtrar por Descripción de Prestación",
                        prestaciones,
                        key="match_filtro_prestacion"
                    )
                
                # Aplicar filtros
                df1_filtrado = df1.copy()
                df_match_filtrado = df_match_con_importes.copy()
                df_no_pagados_filtrado = df_no_pagados_con_importes.copy()
                
                if profesional_filtro != 'TODOS':
                    df1_filtrado = df1_filtrado[df1_filtrado['Médico de tratamiento (nombre)'] == profesional_filtro]
                    df_match_filtrado = df_match_filtrado[df_match_filtrado['Médico de tratamiento (nombre)'] == profesional_filtro]
                    df_no_pagados_filtrado = df_no_pagados_filtrado[df_no_pagados_filtrado['Médico de tratamiento (nombre)'] == profesional_filtro]
                
                if prestacion_filtro != 'TODAS':
                    df1_filtrado = df1_filtrado[df1_filtrado['Denomin.prestación'] == prestacion_filtro]
                    df_match_filtrado = df_match_filtrado[df_match_filtrado['Denomin.prestación'] == prestacion_filtro]
                    df_no_pagados_filtrado = df_no_pagados_filtrado[df_no_pagados_filtrado['Denomin.prestación'] == prestacion_filtro]
                
                # Métricas con filtros aplicados
                col_fm1, col_fm2, col_fm3 = st.columns(3)
                
                with col_fm1:
                    st.metric(
                        "📋 Registros en filtro",
                        f"{len(df1_filtrado):,}"
                    )
                
                with col_fm2:
                    st.metric(
                        "✅ Pagados en filtro",
                        f"{len(df_match_filtrado):,}",
                        delta=f"{(len(df_match_filtrado)/len(df1_filtrado)*100):.1f}%" if len(df1_filtrado) > 0 else "0%"
                    )
                
                with col_fm3:
                    st.metric(
                        "❌ No pagados en filtro",
                        f"{len(df_no_pagados_filtrado):,}",
                        delta=f"{(len(df_no_pagados_filtrado)/len(df1_filtrado)*100):.1f}%" if len(df1_filtrado) > 0 else "0%",
                        delta_color="inverse"
                    )
                
                # -----------------------------------------------------------------
                # PASO 8: MOSTRAR TABLAS
                # -----------------------------------------------------------------
                
                tab1, tab2, tab3 = st.tabs(["✅ Pagados", "❌ No Pagados", "📊 Resumen por Profesional"])
                
                with tab1:
                    st.subheader(f"Registros Pagados Correctamente ({len(df_match_filtrado)})")
                    if not df_match_filtrado.empty:
                        # Seleccionar columnas a mostrar incluyendo Cobrado OSA
                        columnas_mostrar = df_match_filtrado.columns.tolist()
                        if 'Cobrado OSA (€)' in df_match_filtrado.columns:
                            st.dataframe(
                                df_match_filtrado,
                                use_container_width=True,
                                hide_index=True,
                                column_config={
                                    "Cobrado OSA (€)": st.column_config.NumberColumn(
                                        "Cobrado OSA (€)",
                                        format="€%.2f",
                                        help="Importe HHMM del Archivo 2 (pagado)"
                                    )
                                }
                            )
                        else:
                            st.dataframe(
                                df_match_filtrado,
                                use_container_width=True,
                                hide_index=True
                            )
                        
                        # Botón de descarga
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            df_match_filtrado.to_excel(writer, index=False, sheet_name='Pagados')
                        output.seek(0)
                        
                        st.download_button(
                            label="📥 Descargar Pagados (Excel)",
                            data=output,
                            file_name=f"pagados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    else:
                        st.info("No hay registros pagados con los filtros seleccionados.")
                
                with tab2:
                    st.subheader(f"Registros No Pagados ({len(df_no_pagados_filtrado)})")
                    if not df_no_pagados_filtrado.empty:
                        # Seleccionar columnas a mostrar incluyendo Por Cobrar OSA (siempre 0)
                        if 'Por Cobrar OSA (€)' in df_no_pagados_filtrado.columns:
                            st.dataframe(
                                df_no_pagados_filtrado,
                                use_container_width=True,
                                hide_index=True,
                                column_config={
                                    "Por Cobrar OSA (€)": st.column_config.NumberColumn(
                                        "Por Cobrar OSA (€)",
                                        format="€%.2f",
                                        help="SIEMPRE 0 - No aparecen en el archivo de pagos"
                                    )
                                }
                            )
                        else:
                            st.dataframe(
                                df_no_pagados_filtrado,
                                use_container_width=True,
                                hide_index=True
                            )
                        
                        # Botón de descarga
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            df_no_pagados_filtrado.to_excel(writer, index=False, sheet_name='No_Pagados')
                        output.seek(0)
                        
                        st.download_button(
                            label="📥 Descargar No Pagados (Excel)",
                            data=output,
                            file_name=f"no_pagados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    else:
                        st.info("No hay registros no pagados con los filtros seleccionados.")
                
                with tab3:
                    st.subheader("Resumen por Profesional")
                    
                    # Crear resumen por profesional con las nuevas columnas - CORREGIDO
                    resumen_profesional = []
                    
                    for profesional in df1['Médico de tratamiento (nombre)'].dropna().unique():
                        # Filtrar registros del profesional
                        df_prof = df1[df1['Médico de tratamiento (nombre)'] == profesional]
                        df_prof_match = df_match[df_match['Médico de tratamiento (nombre)'] == profesional]
                        
                        total_registros = len(df_prof)
                        pagados = len(df_prof_match)
                        no_pagados = total_registros - pagados
                        porcentaje_pago = (pagados / total_registros * 100) if total_registros > 0 else 0
                        
                        # Calcular importes
                        # Para pagados, buscar el importe en el archivo 2
                        cobrado_total = 0
                        for idx in df_prof_match.index:
                            if idx in df1_norm.index:
                                llave = df1_norm.loc[idx, 'llave_match']
                                if llave and llave in llaves_pagadas:
                                    # Buscar en df2_norm
                                    registro_pagado = df2_norm[df2_norm['llave_match'] == llave]
                                    if not registro_pagado.empty and 'Importe HHMM' in df2.columns:
                                        importe = pd.to_numeric(registro_pagado.iloc[0].get('Importe HHMM', 0), errors='coerce')
                                        cobrado_total += importe if pd.notna(importe) else 0
                        
                        # Para no pagados, el importe es 0 (CORREGIDO)
                        por_cobrar_total = 0  # Siempre 0
                        
                        resumen_profesional.append({
                            'Profesional': profesional,
                            'Total Registros': total_registros,
                            'Pagados': pagados,
                            'No Pagados': no_pagados,
                            '% Pago': f"{porcentaje_pago:.1f}%",
                            'Cobrado (€)': cobrado_total,
                            'Por Cobrar (€)': por_cobrar_total  # Siempre 0
                        })
                    
                    df_resumen = pd.DataFrame(resumen_profesional)
                    df_resumen = df_resumen.sort_values('Total Registros', ascending=False)
                    
                    st.dataframe(
                        df_resumen,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Profesional": "Profesional",
                            "Total Registros": st.column_config.NumberColumn("Total", format="%d"),
                            "Pagados": st.column_config.NumberColumn("✅ Pagados", format="%d"),
                            "No Pagados": st.column_config.NumberColumn("❌ No Pagados", format="%d"),
                            "% Pago": "% Pago",
                            "Cobrado (€)": st.column_config.NumberColumn("Cobrado (€)", format="€%.2f"),
                            "Por Cobrar (€)": st.column_config.NumberColumn("Por Cobrar (€)", format="€%.2f")
                        }
                    )
                    
                    # Botón de descarga del resumen
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df_resumen.to_excel(writer, index=False, sheet_name='Resumen_Profesional')
                    output.seek(0)
                    
                    st.download_button(
                        label="📥 Descargar Resumen (Excel)",
                        data=output,
                        file_name=f"resumen_match_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                
                # -----------------------------------------------------------------
                # PASO 9: GUARDAR ARCHIVOS PARA LOS MÉDICOS
                # -----------------------------------------------------------------
                # Guardar los archivos originales para que los médicos puedan consultarlos
                DataManager.save_dataframe(df1, 'archivo1_match.parquet')
                DataManager.save_dataframe(df2, 'archivo2_match.parquet')
                
                # Guardar también los DataFrames con las nuevas columnas para los médicos
                DataManager.save_dataframe(df_match_con_importes, 'match_pagados.parquet')
                DataManager.save_dataframe(df_no_pagados_con_importes, 'match_nopagados.parquet')
                
                st.success("✅ Archivos guardados. Los médicos ya pueden ver su match personal.")
    
    else:
        st.info("👆 Por favor, sube ambos archivos para realizar el match.")

# -------------------------------------------------------------------
# MATCH PERSONAL PARA MÉDICOS (SOLO SUS DATOS) - CORREGIDO
# -------------------------------------------------------------------
def match_personal_medico(df_archivo1, df_archivo2, nombre_medico):
    """
    Realiza el match específico para un médico individual
    usando los archivos que subió el administrador
    """
    
    # Función auxiliar para normalizar nombres de médicos
    def normalizar_nombre_medico(nombre):
        if pd.isna(nombre):
            return ""
        nombre_str = str(nombre).strip().upper()
        nombre_sin_comas = nombre_str.replace(',', ' ')
        nombre_sin_comas = ' '.join(nombre_sin_comas.split())
        partes = nombre_sin_comas.split()
        partes_ordenadas = sorted(partes)
        return ' '.join(partes_ordenadas)
    
    # Verificar que los DataFrames no estén vacíos
    if df_archivo1 is None or df_archivo2 is None or df_archivo1.empty or df_archivo2.empty:
        st.warning("El administrador aún no ha subido los archivos para realizar el match.")
        return
    
    # Verificar columnas necesarias
    columnas_df1 = ['Fecha', 'Paciente', 'Denomin.prestación', 'Médico de tratamiento (nombre)']
    columnas_df2 = ['Fecha del Servicio', 'NHC Paciente', 'Descripción de Prestación', 'Profesional']
    
    columnas_faltantes_df1 = [col for col in columnas_df1 if col not in df_archivo1.columns]
    columnas_faltantes_df2 = [col for col in columnas_df2 if col not in df_archivo2.columns]
    
    if columnas_faltantes_df1 or columnas_faltantes_df2:
        st.error("❌ Los archivos no tienen las columnas necesarias.")
        if columnas_faltantes_df1:
            st.error(f"Archivo 1 faltan: {', '.join(columnas_faltantes_df1)}")
        if columnas_faltantes_df2:
            st.error(f"Archivo 2 faltan: {', '.join(columnas_faltantes_df2)}")
        return
    
    with st.spinner("Procesando tus datos..."):
        
        # Normalizar datos
        df1_norm = df_archivo1.copy()
        df2_norm = df_archivo2.copy()
        
        # Normalizar fechas
        df1_norm['Fecha_norm'] = pd.to_datetime(df1_norm['Fecha'], errors='coerce').dt.date
        df2_norm['Fecha_norm'] = pd.to_datetime(df2_norm['Fecha del Servicio'], errors='coerce').dt.date
        
        # Normalizar paciente
        df1_norm['Paciente_norm'] = df1_norm['Paciente'].astype(str).str.strip().str.upper()
        df2_norm['Paciente_norm'] = df2_norm['NHC Paciente'].astype(str).str.strip().str.upper()
        
        # Normalizar prestación
        df1_norm['Prestacion_norm'] = df1_norm['Denomin.prestación'].astype(str).str.strip().str.upper()
        df2_norm['Prestacion_norm'] = df2_norm['Descripción de Prestación'].astype(str).str.strip().str.upper()
        
        # Normalizar nombres de médicos
        df1_norm['Medico_norm'] = df1_norm['Médico de tratamiento (nombre)'].apply(normalizar_nombre_medico)
        df2_norm['Medico_norm'] = df2_norm['Profesional'].apply(normalizar_nombre_medico)
        
        # Normalizar el nombre del médico actual para filtrar
        nombre_medico_norm = normalizar_nombre_medico(nombre_medico)
        
        # Filtrar solo los registros del médico actual en ambos archivos
        df1_medico = df1_norm[df1_norm['Medico_norm'] == nombre_medico_norm].copy()
        df2_medico = df2_norm[df2_norm['Medico_norm'] == nombre_medico_norm].copy()
        
        # Crear llaves de match
        df1_medico['llave_match'] = (
            df1_medico['Fecha_norm'].astype(str) + '|' +
            df1_medico['Paciente_norm'] + '|' +
            df1_medico['Prestacion_norm'] + '|' +
            df1_medico['Medico_norm']
        )
        
        df2_medico['llave_match'] = (
            df2_medico['Fecha_norm'].astype(str) + '|' +
            df2_medico['Paciente_norm'] + '|' +
            df2_medico['Prestacion_norm'] + '|' +
            df2_medico['Medico_norm']
        )
        
        # Crear conjunto de llaves pagadas
        llaves_pagadas = set(df2_medico['llave_match'].dropna().unique())
        
        # Marcar qué registros del médico tienen match
        df1_medico['Match'] = df1_medico['llave_match'].isin(llaves_pagadas)
        
        # Obtener los registros originales (sin normalizar) para mostrar
        indices_match = df1_medico[df1_medico['Match']].index
        indices_no_match = df1_medico[~df1_medico['Match']].index
        
        df_match = df_archivo1.loc[indices_match] if not indices_match.empty else pd.DataFrame()
        df_no_pagados = df_archivo1.loc[indices_no_match] if not indices_no_match.empty else pd.DataFrame()
        
        # -----------------------------------------------------------------
        # AÑADIR COLUMNAS DE IMPORTES PARA EL MÉDICO - CORREGIDO
        # -----------------------------------------------------------------
        
        # Para los pagados, añadir columna "Cobrado OSA (€)" con el Importe HHMM del archivo 2
        if not df_match.empty:
            # Crear un diccionario para mapear llave_match a Importe HHMM del archivo 2
            if 'Importe HHMM' in df_archivo2.columns:
                df2_medico['Importe_HHMM_Archivo2'] = pd.to_numeric(df2_medico['Importe HHMM'], errors='coerce')
            else:
                df2_medico['Importe_HHMM_Archivo2'] = 0
            
            mapa_importes = dict(zip(df2_medico['llave_match'], df2_medico['Importe_HHMM_Archivo2']))
            
            # Añadir la columna a df_match
            df_match_con_importes = df_match.copy()
            df_match_con_importes['Cobrado OSA (€)'] = df_match_con_importes.index.map(
                lambda idx: mapa_importes.get(df1_medico.loc[idx, 'llave_match'], 0) if idx in df1_medico.index else 0
            )
        else:
            df_match_con_importes = df_match.copy()
            df_match_con_importes['Cobrado OSA (€)'] = 0
        
        # Para los no pagados, añadir columna "Por Cobrar OSA (€)" con valor 0
        # CORREGIDO: Siempre 0 porque no aparecen en el archivo de pagos
        if not df_no_pagados.empty:
            df_no_pagados_con_importes = df_no_pagados.copy()
            df_no_pagados_con_importes['Por Cobrar OSA (€)'] = 0  # Siempre 0
        else:
            df_no_pagados_con_importes = df_no_pagados.copy()
            df_no_pagados_con_importes['Por Cobrar OSA (€)'] = 0
        
        # MOSTRAR RESULTADOS
        st.markdown("---")
        st.subheader(f"📊 Tu Match de Pagos")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div class='stMetric'>
                <label>📋 Tus registros totales</label>
                <div class='metric-highlight'>{len(df1_medico):,}</div>
                <small>En el período analizado</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class='stMetric'>
                <label>✅ Pagados</label>
                <div class='metric-highlight' style='color: #28a745;'>{len(df_match_con_importes):,}</div>
                <small>Coinciden en archivo de pagos</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class='stMetric'>
                <label>⏳ Pendientes</label>
                <div class='metric-highlight' style='color: #dc3545;'>{len(df_no_pagados_con_importes):,}</div>
                <small>No aparecen en pagos</small>
            </div>
            """, unsafe_allow_html=True)
        
        # Mostrar tablas
        tab1, tab2 = st.tabs(["✅ Pagados", "⏳ Pendientes de cobro"])
        
        with tab1:
            st.subheader(f"Servicios Pagados ({len(df_match_con_importes)})")
            if not df_match_con_importes.empty:
                # Seleccionar columnas relevantes para mostrar
                columnas_mostrar = ['Fecha', 'Paciente', 'Denomin.prestación']
                columnas_existentes = [col for col in columnas_mostrar if col in df_match_con_importes.columns]
                
                # Mostrar con columna de Cobrado OSA
                if 'Cobrado OSA (€)' in df_match_con_importes.columns:
                    st.dataframe(
                        df_match_con_importes[columnas_existentes + ['Cobrado OSA (€)']],
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Cobrado OSA (€)": st.column_config.NumberColumn(
                                "Cobrado OSA (€)",
                                format="€%.2f",
                                help="Importe HHMM del Archivo 2 (pagado)"
                            )
                        }
                    )
                else:
                    st.dataframe(
                        df_match_con_importes[columnas_existentes],
                        use_container_width=True,
                        hide_index=True
                    )
                
                # Botón de descarga
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_match_con_importes.to_excel(writer, index=False, sheet_name='Pagados')
                output.seek(0)
                
                st.download_button(
                    label="📥 Descargar mis pagados (Excel)",
                    data=output,
                    file_name=f"mis_pagados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.info("No tienes servicios pagados en este período.")
        
        with tab2:
            st.subheader(f"Servicios Pendientes ({len(df_no_pagados_con_importes)})")
            if not df_no_pagados_con_importes.empty:
                columnas_mostrar = ['Fecha', 'Paciente', 'Denomin.prestación']
                columnas_existentes = [col for col in columnas_mostrar if col in df_no_pagados_con_importes.columns]
                
                # Mostrar con columna de Por Cobrar OSA (siempre 0)
                if 'Por Cobrar OSA (€)' in df_no_pagados_con_importes.columns:
                    st.dataframe(
                        df_no_pagados_con_importes[columnas_existentes + ['Por Cobrar OSA (€)']],
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Por Cobrar OSA (€)": st.column_config.NumberColumn(
                                "Por Cobrar OSA (€)",
                                format="€%.2f",
                                help="SIEMPRE 0 - No aparecen en el archivo de pagos"
                            )
                        }
                    )
                else:
                    st.dataframe(
                        df_no_pagados_con_importes[columnas_existentes],
                        use_container_width=True,
                        hide_index=True
                    )
                
                # Botón de descarga
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_no_pagados_con_importes.to_excel(writer, index=False, sheet_name='Pendientes')
                output.seek(0)
                
                st.download_button(
                    label="📥 Descargar mis pendientes (Excel)",
                    data=output,
                    file_name=f"mis_pendientes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.success("¡Todos tus servicios han sido pagados! ✅")
        
        # Resumen ejecutivo con importes - CORREGIDO
        st.markdown("---")
        st.subheader("📋 Resumen Ejecutivo")
        
        total_servicios = len(df1_medico)
        if total_servicios > 0:
            # Calcular totales de importes
            total_cobrado = df_match_con_importes['Cobrado OSA (€)'].sum() if not df_match_con_importes.empty and 'Cobrado OSA (€)' in df_match_con_importes.columns else 0
            total_por_cobrar = 0  # Siempre 0
            
            col_r1, col_r2 = st.columns(2)
            
            with col_r1:
                st.markdown(f"""
                <div style='background-color: #e8f5e9; padding: 20px; border-radius: 10px;'>
                    <h4 style='color: #2e7d32;'>✅ Lo cobrado</h4>
                    <p style='font-size: 18px;'><strong>{len(df_match_con_importes)} servicios</strong> ({len(df_match_con_importes)/total_servicios*100:.1f}%)</p>
                    <p style='font-size: 16px;'><strong>Total cobrado: €{total_cobrado:,.2f}</strong></p>
                    <p>Estos servicios ya aparecen en el archivo de pagos.</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col_r2:
                st.markdown(f"""
                <div style='background-color: #ffebee; padding: 20px; border-radius: 10px;'>
                    <h4 style='color: #c62828;'>⏳ Pendiente</h4>
                    <p style='font-size: 18px;'><strong>{len(df_no_pagados_con_importes)} servicios</strong> ({len(df_no_pagados_con_importes)/total_servicios*100:.1f}%)</p>
                    <p style='font-size: 16px;'><strong>Total por cobrar: €0.00</strong> (no aparecen en pagos)</p>
                    <p>Estos servicios aún no aparecen en pagos. El importe pendiente es 0 porque no están registrados como pagados.</p>
                </div>
                """, unsafe_allow_html=True)

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
# DASHBOARD MÉDICO - CON PESTAÑA DE MATCH PERSONAL Y ESTILOS MEJORADOS
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
    
    # Header personalizado con colores mejorados
    st.markdown(f"""
    <div class='custom-card' style='background: linear-gradient(135deg, {COLORES['primary']} 0%, {COLORES['primary']}ee 100%);'>
        <h2 style='color: {COLORES['secondary']} !important; margin-bottom: 5px; font-size: 28px;'>👨‍⚕️ {profesional_nombre}</h2>
        <p style='color: white !important; font-size: 20px; margin-bottom: 0; font-weight: 500;'>
            {subespecialidad}
        </p>
        <p style='color: {COLORES['secondary']} !important; font-size: 16px; margin-top: 5px; font-weight: bold;'>
            {kpis['tipo_medico']}
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
    # ANÁLISIS POR TIPO DE PRESTACIÓN
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
    # TABLA ORIGINAL FILTRADA
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
        
        # Verificar si la columna Aseguradora existe
        tiene_aseguradora = 'Aseguradora' in df_detalle.columns
        
        # Construir orden de columnas dinámicamente
        orden_columnas = ['Fecha del servicio', 'Profesional']
        
        if tiene_aseguradora:
            orden_columnas.append('Aseguradora')
        
        orden_columnas.extend([
            'Descripción de Prestación',
            'Monto Cobrado por Vithas (€)',
            '% Liquidación',
            'Importe Cobrado OSA (€)'
        ])
        
        # Solo mantener columnas que existen
        orden_columnas = [col for col in orden_columnas if col in df_detalle.columns]
        df_detalle = df_detalle[orden_columnas]
        
        # Formatear fechas
        if 'Fecha del servicio' in df_detalle.columns:
            df_detalle['Fecha del servicio'] = pd.to_datetime(df_detalle['Fecha del servicio']).dt.strftime('%d/%m/%Y')
        
        # Configuración de columnas para la tabla
        column_config = {
            "Fecha del servicio": "Fecha",
            "Profesional": "Médico",
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
        
        # Agregar Aseguradora a la configuración solo si existe
        if tiene_aseguradora:
            column_config["Aseguradora"] = "Aseguradora"
        
        # Mostrar la tabla
        st.dataframe(
            df_detalle,
            use_container_width=True,
            hide_index=True,
            column_config=column_config
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
    
    st.markdown("---")
    
    # -------------------------------------------------------------------
    # MATCH PERSONAL (SOLO PARA EL MÉDICO)
    # -------------------------------------------------------------------
    with st.expander("🔍 Ver Match de Pagos (vs archivo de administrador)", expanded=False):
        st.info("Para ver tu match personal, el administrador debe haber subido los dos archivos en su panel.")
        
        # Cargar los archivos de match desde el DataManager
        archivo1_match = DataManager.load_dataframe('archivo1_match.parquet')
        archivo2_match = DataManager.load_dataframe('archivo2_match.parquet')
        
        if archivo1_match is not None and archivo2_match is not None:
            # Usar la función de match personal
            match_personal_medico(archivo1_match, archivo2_match, profesional_nombre)
        else:
            st.warning("El administrador aún no ha subido los archivos para realizar el match.")
            
            # Botón para solicitar al admin (opcional)
            if st.button("📧 Notificar al administrador", use_container_width=True):
                st.info("Funcionalidad de notificación en desarrollo. Por ahora, contacta al administrador directamente.")

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
    
    # Pestañas del administrador
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📤 Carga de Datos", 
        "📊 Dashboard General", 
        "📈 Proyección Gerencia", 
        "🔍 Match",
        "ℹ️ Información"
    ])
    
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
        if df_actual is not None and not df_actual.empty:
            proyeccion_gerencia(df_actual)
        else:
            # Si no hay datos, mostrar proyección con escenario simulado
            proyeccion_gerencia(None)
    
    with tab4:
        match_archivos()
    
    with tab5:
        st.subheader("Información del Sistema")
        st.markdown(f"""
        **Versión:** 3.2.0  
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
    
    # Mostrar header en área principal
    mostrar_header()
    
    # Área principal según el rol
    if rol == 'admin':
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
