from kivymd.app import MDApp
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image  
from kivy.uix.video import Video
from kivy.uix.gridlayout import GridLayout
from kivy.animation import Animation 
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton, MDFillRoundFlatButton, MDRectangleFlatIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.textfield import MDTextField  
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock  
from kivy.graphics.texture import Texture
from kivy.metrics import dp
from kivy.uix.widget import Widget
from kivy.core.window import Window
import os
import cv2
import math
import datetime
from collections import Counter
import webbrowser
import json
from datetime import timedelta

# ==========================================
# IMPORTACIÓN ESTÁNDAR DE MEDIAPIPE (LIMPIA)
# ==========================================
import mediapipe as mp
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

# Datos del usuario globales
DATOS_USUARIO = {
    "nombre": "",
    "edad": "",
    "sexo": "Seleccionar...",
    "altura": "",
    "peso": "",
    "ejercicio": None,
    "plan_sugerido": None,
    "membresia": "Gratis",
    "membresia_activa": False,
    # Rutina generada por la IA al pagar una membresía premium
    "rutina_ia": None,
    # Progreso real del usuario
    "historial_sesiones": [],   # lista de dicts: fecha, ejercicio, reps, dia_semana
    "reps_totales": 0,
    "total_sesiones": 0,
    "racha_actual": 0,
    "ultima_fecha_entreno": None,
}

# Persistencia simple en JSON
USERDATA_FILE = os.path.join(os.path.dirname(__file__), "userdata.json")

def save_user_data():
    try:
        with open(USERDATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(DATOS_USUARIO, f, default=str, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Error guardando userdata:", e)

def load_user_data():
    try:
        if os.path.exists(USERDATA_FILE):
            with open(USERDATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # merge loaded fields into DATOS_USUARIO
                for k, v in data.items():
                    DATOS_USUARIO[k] = v
    except Exception as e:
        print("Error cargando userdata:", e)

COLOR_AMARILLO = (1, 0.84, 0, 1)
COLOR_BLANCO = (1, 1, 1, 1)
CONTENIDO_PLANES = {
    "Premium Mensual": "Incluye:\n- Todos los ejercicios\n- Historial ilimitado\n- Rutinas personalizadas con IA",
    "Premium Anual": "Incluye:\n- Todo lo del plan mensual\n- Ahorro del 33%\n- Soporte prioritario",
    "Gratis": "Incluye:\n- Cámara IA gratuita para todos los ejercicios\n- Historial limitado\n- Sin rutinas personalizadas"
}

DIAS_SEMANA = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]


def generar_rutina_ia(plan):
    """Genera una rutina de entrenamiento (semanal o mensual) según el plan pagado."""
    if plan == "Premium Mensual":
        # Generar 4 semanas con ejercicios de peso corporal diarios (Domingo descanso)
        semanas = []
        semana_base = [
            {"dia": "Lunes", "ejercicios": [{"nombre": "Sentadillas", "series": "3", "reps": "15"}, {"nombre": "Flexiones", "series": "3", "reps": "10"}], "tiempo": "20-30 min"},
            {"dia": "Martes", "ejercicios": [{"nombre": "Dominadas", "series": "3", "reps": "5"}, {"nombre": "Sentadillas", "series": "3", "reps": "15"}], "tiempo": "20-30 min"},
            {"dia": "Miércoles", "ejercicios": [{"nombre": "Flexiones", "series": "4", "reps": "10"}, {"nombre": "Dominadas", "series": "3", "reps": "5"}], "tiempo": "20-30 min"},
            {"dia": "Jueves", "ejercicios": [{"nombre": "Sentadillas", "series": "4", "reps": "15"}, {"nombre": "Flexiones", "series": "3", "reps": "12"}], "tiempo": "20-30 min"},
            {"dia": "Viernes", "ejercicios": [{"nombre": "Dominadas", "series": "4", "reps": "5"}, {"nombre": "Sentadillas", "series": "3", "reps": "20"}], "tiempo": "20-30 min"},
            {"dia": "Sábado", "ejercicios": [{"nombre": "Flexiones", "series": "4", "reps": "12"}, {"nombre": "Dominadas", "series": "3", "reps": "6"}], "tiempo": "20-30 min"},
            {"dia": "Domingo", "ejercicios": [], "tiempo": "Descanso"},
        ]
        for w in range(1, 5):
            dias = []
            for d in semana_base:
                dia_entry = {
                    "semana": w,
                    "dia": d["dia"],
                    "ejercicios": d["ejercicios"],
                    "tiempo": d["tiempo"],
                    "estado": "Pendiente"
                }
                dias.append(dia_entry)
            semanas.append({"semana_num": w, "dias": dias})
        return {
            "tipo": "Mensual (4 semanas)",
            "duracion": "4 semanas",
            "estructura": semanas,
            "total_dias": 7 * 4
        }

    elif plan == "Premium Anual":
        # Generar 12 meses con progresión gradual
        meses = []
        for m in range(1, 13):
            factor = 1 + (m - 1) * 0.08  # aumento gradual
            # base values
            def scaled(series, reps):
                s = max(1, int(round(series * (1 + (m - 1) * 0.08))))
                r = max(1, int(round(reps * (1 + (m - 1) * 0.06))))
                return s, r

            s_sen, r_sen = scaled(3 + (m//4), 15 + (m//3)*2)
            s_flex, r_flex = scaled(3 + (m//4), 10 + (m//3)*2)
            s_dom, r_dom = scaled(3 + (m//6), 5 + (m//6)*1)

            mes_plan = {
                "mes": m,
                "descripcion": f"Mes {m} - Progresión automática",
                "semanas": []
            }
            # cada mes contiene 4 semanas similares con ligera variación
            for w in range(1, 5):
                semana = []
                semana.append({"dia": "Lunes", "ejercicios": [{"nombre": "Sentadillas", "series": str(s_sen), "reps": str(r_sen)}, {"nombre": "Flexiones", "series": str(s_flex), "reps": str(r_flex)}], "tiempo": "25-35 min", "estado": "Pendiente"})
                semana.append({"dia": "Martes", "ejercicios": [{"nombre": "Dominadas", "series": str(s_dom), "reps": str(r_dom)}, {"nombre": "Sentadillas", "series": str(s_sen), "reps": str(r_sen)}], "tiempo": "25-35 min", "estado": "Pendiente"})
                semana.append({"dia": "Miércoles", "ejercicios": [{"nombre": "Flexiones", "series": str(s_flex), "reps": str(r_flex)}, {"nombre": "Dominadas", "series": str(s_dom), "reps": str(r_dom)}], "tiempo": "25-35 min", "estado": "Pendiente"})
                semana.append({"dia": "Jueves", "ejercicios": [{"nombre": "Sentadillas", "series": str(s_sen), "reps": str(r_sen)}, {"nombre": "Flexiones", "series": str(s_flex), "reps": str(r_flex)}], "tiempo": "25-35 min", "estado": "Pendiente"})
                semana.append({"dia": "Viernes", "ejercicios": [{"nombre": "Dominadas", "series": str(s_dom), "reps": str(r_dom)}, {"nombre": "Sentadillas", "series": str(s_sen), "reps": str(r_sen)}], "tiempo": "25-35 min", "estado": "Pendiente"})
                semana.append({"dia": "Sábado", "ejercicios": [{"nombre": "Flexiones", "series": str(s_flex), "reps": str(r_flex)}, {"nombre": "Dominadas", "series": str(s_dom), "reps": str(r_dom)}], "tiempo": "25-35 min", "estado": "Pendiente"})
                semana.append({"dia": "Domingo", "ejercicios": [], "tiempo": "Descanso", "estado": "Pendiente"})
                mes_plan["semanas"].append({"semana_num": w, "dias": semana})
            meses.append(mes_plan)
        return {
            "tipo": "Anual (12 meses)",
            "duracion": "12 meses",
            "estructura": meses,
            "total_meses": 12
        }
    return None


def registrar_sesion(ejercicio, reps):
    """Guarda una sesión de entrenamiento real y actualiza racha / totales."""
    hoy = datetime.date.today()
    DATOS_USUARIO["historial_sesiones"].insert(0, {
        "fecha": hoy,
        "ejercicio": ejercicio if ejercicio else "Entrenamiento libre",
        "reps": reps,
        "dia_semana": DIAS_SEMANA[hoy.weekday()]
    })
    DATOS_USUARIO["reps_totales"] += reps
    DATOS_USUARIO["total_sesiones"] += 1

    ultima = DATOS_USUARIO["ultima_fecha_entreno"]
    if ultima is None:
        DATOS_USUARIO["racha_actual"] = 1
    else:
        if isinstance(ultima, str):
            try:
                ultima = datetime.date.fromisoformat(ultima)
            except Exception:
                try:
                    ultima = datetime.datetime.fromisoformat(ultima).date()
                except Exception:
                    ultima = None
        if ultima is None:
            DATOS_USUARIO["racha_actual"] = 1
        else:
            diferencia = (hoy - ultima).days
            if diferencia == 0:
                pass  # ya se entrenó hoy, la racha no cambia
            elif diferencia == 1:
                DATOS_USUARIO["racha_actual"] += 1
            else:
                DATOS_USUARIO["racha_actual"] = 1
    DATOS_USUARIO["ultima_fecha_entreno"] = hoy


def calcular_mejor_dia():
    historial = DATOS_USUARIO.get("historial_sesiones", [])
    if not historial:
        return "N/A"
    conteo = Counter(s["dia_semana"] for s in historial)
    return conteo.most_common(1)[0][0]


def animar_boton_en_movimiento(boton, delay=0):
    if getattr(boton, "_animacion_movimiento_activa", False):
        return boton
    boton._animacion_movimiento_activa = True

    def iniciar_animacion(dt):
        anim = Animation(opacity=0.78, duration=0.65, t='in_out_sine') + \
               Animation(opacity=1, duration=0.65, t='in_out_sine')
        anim.repeat = True
        anim.start(boton)

        if hasattr(boton, "elevation"):
            anim_elevacion = Animation(elevation=10, duration=0.65, t='in_out_sine') + \
                             Animation(elevation=2, duration=0.65, t='in_out_sine')
            anim_elevacion.repeat = True
            anim_elevacion.start(boton)

    Clock.schedule_once(iniciar_animacion, delay)
    return boton

def animar_botones_en_layout(layout, delay_base=0.04):
    botones = (MDRaisedButton, MDFlatButton, MDIconButton, MDFillRoundFlatButton)
    delay = 0
    for widget in layout.walk():
        if isinstance(widget, botones):
            animar_boton_en_movimiento(widget, delay)
            delay += delay_base

# PANTALLA 1: BIENVENIDA
class PantallaBienvenida(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        from kivy.uix.widget import Widget
        from kivymd.uix.button import MDRoundFlatButton

        layout_pantalla = FloatLayout()

        # Imagen de fondo a pantalla completa
        fondo = Image(
            source="logo_nuevo.png",
            size_hint=(1, 1),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            allow_stretch=True,
            keep_ratio=False,
            opacity=0.95
        )
        layout_pantalla.add_widget(fondo)

        box_centro = BoxLayout(
            orientation='vertical',
            size_hint=(0.95, None),
            height=dp(260),
            pos_hint={"center_x": 0.5, "y": 0.05},
            padding=[dp(16), dp(12), dp(16), dp(12)],
            spacing=dp(12)
        )

        box_centro.add_widget(MDLabel(
            text="TU RUTINA FITNESS COMIENZA AQUÍ",
            halign="center",
            font_style="Caption",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            size_hint_y=None,
            height=dp(26)
        ))

        app = MDApp.get_running_app()
        self.btn_comenzar = MDFillRoundFlatButton(
            text="COMENZAR",
            pos_hint={"center_x": 0.5},
            size_hint=(0.95, None), height=dp(56),
            md_bg_color=app.theme_cls.primary_color,
            text_color=(1, 1, 1, 1),
            font_size="18sp",
            on_release=lambda x: self.ir_a_registro()
        )
        box_centro.add_widget(self.btn_comenzar)
        self.animar_boton_pulso()

        box_centro.add_widget(Widget(size_hint_y=None, height=dp(10)))

        login_row = BoxLayout(orientation='horizontal', size_hint=(0.95, None), height=dp(56), spacing=dp(12), pos_hint={"center_x": 0.5})
        btn_google = MDFillRoundFlatButton(
            text="Google",
            icon="google",
            icon_size="20sp",
            size_hint_x=0.5,
            height=dp(56),
            md_bg_color=app.theme_cls.primary_color,
            text_color=(1, 1, 1, 1),
            theme_text_color="Custom",
            on_release=lambda x: self.login_social("Google")
        )
        btn_apple = MDFillRoundFlatButton(
            text="Apple",
            icon="apple",
            icon_size="20sp",
            size_hint_x=0.5,
            height=dp(56),
            md_bg_color=app.theme_cls.primary_color,
            text_color=(1, 1, 1, 1),
            theme_text_color="Custom",
            on_release=lambda x: self.login_social("Apple")
        )
        login_row.add_widget(btn_google)
        login_row.add_widget(btn_apple)
        box_centro.add_widget(login_row)

        layout_pantalla.add_widget(box_centro)

        social_row = BoxLayout(orientation='horizontal', size_hint=(0.5, None), height=dp(60), spacing=dp(8), pos_hint={"x": 0.02, "top": 0.95})
        for nombre, icono in [("Instagram", "instagram"), ("Facebook", "facebook"), ("Twitter", "twitter")]:
            social_col = BoxLayout(orientation='vertical', size_hint_x=None, width=dp(80), spacing=dp(2))
            social_col.add_widget(MDIconButton(
                icon=icono,
                icon_size='24sp',
                theme_text_color='Custom',
                text_color=app.theme_cls.primary_color,
                pos_hint={"center_x": 0.5},
                md_bg_color=(0, 0, 0, 0)
            ))
            social_col.add_widget(MDLabel(
                text=nombre,
                halign='center',
                font_style='Caption',
                theme_text_color='Custom',
                text_color=(1, 1, 1, 1),
                size_hint_y=None,
                height=dp(18)
            ))
            social_row.add_widget(social_col)
        layout_pantalla.add_widget(social_row)

        btn_perfil = MDIconButton(
            icon="account-circle",
            pos_hint={"right": 0.97, "top": 0.97},
            theme_text_color="Custom", text_color=(0.6, 0.6, 0.6, 1),
            on_release=lambda x: self.ir_a_perfil()
        )
        layout_pantalla.add_widget(btn_perfil)

        self.add_widget(layout_pantalla)
        animar_botones_en_layout(layout_pantalla)

    def animar_boton_pulso(self):
        animar_boton_en_movimiento(self.btn_comenzar)

    def ir_a_registro(self):
        self.manager.transition.direction = "left"
        self.manager.current = "registro"

    def login_social(self, proveedor):
        # Guardamos el proveedor elegido y llevamos al usuario a una
        # pantalla de inicio de sesión antes de continuar con el registro.
        DATOS_USUARIO["proveedor_login"] = proveedor
        if proveedor == "Google":
            DATOS_USUARIO["correo_temp"] = "usuario@gmail.com"
        else:
            DATOS_USUARIO["correo_temp"] = "usuario@icloud.com"

        self.manager.transition.direction = "left"
        self.manager.current = "login_social"

    def ir_a_membresias(self):
        self.manager.transition.direction = "left"
        self.manager.current = "membresias"

    def ir_a_perfil(self):
        self.manager.transition.direction = "left"
        self.manager.current = "perfil"


# PANTALLA 1.5: INICIO DE SESIÓN (GOOGLE / APPLE)
class PantallaLoginSocial(Screen):
    def on_enter(self, *args):
        proveedor = DATOS_USUARIO.get("proveedor_login", "Google")
        self.lbl_titulo.text = f"Iniciar sesión con {proveedor}"
        self.icon_proveedor.icon = "google" if proveedor == "Google" else "apple"
        self.txt_correo.text = DATOS_USUARIO.get("correo_temp", "")
        self.txt_clave.text = ""
        self.lbl_error.text = ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = FloatLayout()
        box = BoxLayout(
            orientation='vertical', padding=dp(30), spacing=dp(18),
            size_hint=(0.9, None), pos_hint={"center_x": 0.5, "center_y": 0.55}
        )
        box.bind(minimum_height=box.setter('height'))

        self.icon_proveedor = MDIconButton(
            icon="google", icon_size="60sp", pos_hint={"center_x": 0.5},
            theme_text_color="Custom", text_color=(1, 1, 1, 1)
        )
        box.add_widget(self.icon_proveedor)

        self.lbl_titulo = MDLabel(
            text="Iniciar sesión con Google", halign="center", font_style="H6",
            bold=True, size_hint_y=None, height=dp(35)
        )
        box.add_widget(self.lbl_titulo)

        self.txt_correo = MDTextField(hint_text="Correo electrónico", mode="rectangle", size_hint_y=None, height=dp(50), icon_left="email")
        self.txt_clave = MDTextField(hint_text="Contraseña", mode="rectangle", password=True, size_hint_y=None, height=dp(50), icon_left="lock")
        box.add_widget(self.txt_correo)
        box.add_widget(self.txt_clave)

        self.lbl_error = MDLabel(
            text="", halign="center", theme_text_color="Custom",
            text_color=(1, 0.3, 0.3, 1), font_style="Caption", size_hint_y=None, height=dp(20)
        )
        box.add_widget(self.lbl_error)

        app = MDApp.get_running_app()
        btn_login = MDFillRoundFlatButton(
            text="Continuar", size_hint=(1, None), height=dp(50),
            md_bg_color=app.theme_cls.primary_color, text_color=(1, 1, 1, 1),
            on_release=lambda x: self.iniciar_sesion()
        )
        box.add_widget(btn_login)

        layout.add_widget(box)

        btn_back = MDIconButton(
            icon="arrow-left", md_bg_color=(0.25, 0.25, 0.25, 1),
            pos_hint={"x": 0.04, "top": 0.96}, on_release=lambda x: self.regresar()
        )
        layout.add_widget(btn_back)

        self.add_widget(layout)
        animar_botones_en_layout(layout)

    def regresar(self):
        self.manager.transition.direction = "right"
        self.manager.current = "bienvenida"

    def iniciar_sesion(self):
        if not self.txt_correo.text or not self.txt_clave.text:
            self.lbl_error.text = "Completa correo y contraseña para continuar."
            return

        proveedor = DATOS_USUARIO.get("proveedor_login", "Google")
        DATOS_USUARIO["nombre"] = f"Usuario {proveedor}"
        DATOS_USUARIO["correo"] = self.txt_correo.text

        pantalla_reg = self.manager.get_screen("registro")
        pantalla_reg.txt_nombre.text = DATOS_USUARIO["nombre"]

        self.manager.transition.direction = "left"
        self.manager.current = "registro"


# PANTALLA 2: REGISTRO
class PantallaRegistro(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        layout_pantalla = FloatLayout()
        scroll = ScrollView(size_hint=(1, 1))
        layout_principal = BoxLayout(orientation='vertical', padding=25, spacing=15, size_hint_y=None)
        layout_principal.bind(minimum_height=layout_principal.setter('height'))
        
        layout_principal.add_widget(MDLabel(
            text="¡Bienvenido!\nCuéntanos un poco sobre ti", 
            halign="center", font_style="H5", size_hint_y=None, height=70
        ))
        
        self.txt_nombre = MDTextField(hint_text="¿Cómo te llamas?", size_hint_y=None, height=50, mode="rectangle", icon_left="account")
        self.txt_edad = MDTextField(hint_text="¿Qué edad tienes?", size_hint_y=None, height=50, mode="rectangle", icon_left="calendar")
        self.txt_altura = MDTextField(hint_text="Altura (cm)", size_hint_y=None, height=50, mode="rectangle", icon_left="human-male-height")
        self.txt_peso = MDTextField(hint_text="Peso (kg)", size_hint_y=None, height=50, mode="rectangle", icon_left="weight")
        
        layout_principal.add_widget(self.txt_nombre)
        layout_principal.add_widget(self.txt_edad)
        layout_principal.add_widget(self.txt_altura)
        layout_principal.add_widget(self.txt_peso)
        
        layout_sexo = BoxLayout(orientation='vertical', spacing=5, size_hint_y=None, height=75)
        layout_sexo.add_widget(MDLabel(text="Sexo:", font_style="Caption", theme_text_color="Secondary", size_hint_y=None, height=20))
        
        app = MDApp.get_running_app()
        self.btn_sexo_dropdown = MDFillRoundFlatButton(
            text=DATOS_USUARIO["sexo"], size_hint=(1, None), height=45, 
            md_bg_color=app.theme_cls.primary_color, text_color=(1, 1, 1, 1), on_release=self.abrir_menu_sexo
        )
        layout_sexo.add_widget(self.btn_sexo_dropdown)
        layout_principal.add_widget(layout_sexo)
        
        opciones = ["Masculino", "Femenino", "Prefiero no decirlo"]
        self.menu_sexo = MDDropdownMenu(
            caller=self.btn_sexo_dropdown,
            items=[{"text": op, "viewclass": "OneLineListItem", "on_release": lambda x=op: self.cambiar_sexo(x)} for op in opciones],
            width_mult=4,
        )
        
        btn_siguiente = MDFillRoundFlatButton(
            text="Continuar", size_hint=(0.85, None), height=50,
            pos_hint={"center_x": 0.5}, md_bg_color=(1, 0.2, 0.2, 1), on_release=lambda x: self.ir_a_sugerencia()
        )
        layout_principal.add_widget(btn_siguiente)
        
        scroll.add_widget(layout_principal)
        layout_pantalla.add_widget(scroll)
        
        self.btn_regresar_flotante = MDIconButton(
            icon="arrow-left", md_bg_color=(0.25, 0.25, 0.25, 1),     
            pos_hint={"x": 0.04, "top": 0.96}, on_release=lambda x: self.regresar_pantalla()
        )
        layout_pantalla.add_widget(self.btn_regresar_flotante)
        self.add_widget(layout_pantalla)
        animar_botones_en_layout(layout_pantalla)

    def abrir_menu_sexo(self, boton):
        self.menu_sexo.open()

    def cambiar_sexo(self, sexo_elegido):
        self.btn_sexo_dropdown.text = sexo_elegido
        DATOS_USUARIO["sexo"] = sexo_elegido
        self.menu_sexo.dismiss()

    def regresar_pantalla(self):
        self.manager.transition.direction = "right"
        self.manager.current = "bienvenida"

    def ir_a_sugerencia(self):
        DATOS_USUARIO["nombre"] = self.txt_nombre.text if self.txt_nombre.text else "Anónimo"
        DATOS_USUARIO["edad"] = self.txt_edad.text if self.txt_edad.text else "25"
        DATOS_USUARIO["altura"] = self.txt_altura.text if self.txt_altura.text else "170"
        DATOS_USUARIO["peso"] = self.txt_peso.text if self.txt_peso.text else "70"
        DATOS_USUARIO["plan_sugerido"] = None
        DATOS_USUARIO["ejercicio"] = None
        self.manager.transition.direction = "left"
        self.manager.current = "ejercicios"


# PANTALLA 3: SUGERENCIA DE PLAN
class PantallaSugerenciaPlan(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.plan_generado = None
        
    def on_enter(self, *args):
        self.generar_plan_personalizado()
        self.animar_botones_entrada()
    
    def generar_plan_personalizado(self):
        altura = DATOS_USUARIO["altura"]
        peso = DATOS_USUARIO["peso"]
        imc = float(peso) / ((float(altura) / 100) ** 2)
        
        if imc < 18.5:
            self.plan_generado = {"objetivo": "Ganar masa muscular", "ejercicio_recomendado": "Sentadillas", "repeticiones": " Meta: 10 repeticiones", "consejo": "Enfócate en la técnica baja."}
        elif imc < 25:
            self.plan_generado = {"objetivo": "Mantener y tonificar", "ejercicio_recomendado": "Flexiones", "repeticiones": "Meta: 15 repeticiones", "consejo": "Controla el descenso suave."}
        else:
            self.plan_generado = {"objetivo": "Acondicionamiento", "ejercicio_recomendado": "Sentadillas", "repeticiones": "Meta: 12 repeticiones", "consejo": "Mantén la espalda recta."}
        self.build_ui()
    
    def build_ui(self):
        self.clear_widgets()
        layout_pantalla = FloatLayout()
        layout_principal = BoxLayout(orientation='vertical', padding=25, spacing=15)
        
        layout_principal.add_widget(MDLabel(text=f"Plan para {DATOS_USUARIO['nombre']}", halign="center", font_style="H5", bold=True, size_hint_y=None, height=50))
        
        # Card modernizada con badge simulado
        card_plan = MDCard(orientation='vertical', padding=20, spacing=12, size_hint=(0.95, None), height=320, pos_hint={"center_x": 0.5}, md_bg_color=(0.1, 0.1, 0.15, 1), radius=[20])
        badge = MDLabel(text="RECOMENDACIÓN IA", font_style="Caption", bold=True, text_color=(0, 0.8, 1, 1), theme_text_color="Custom")
        card_plan.add_widget(badge)
        card_plan.add_widget(MDLabel(text=f"Objetivo: {self.plan_generado['objetivo']}", font_style="Subtitle1"))
        card_plan.add_widget(MDLabel(text=f"SUGERIDO: {self.plan_generado['ejercicio_recomendado']}", font_style="H6", bold=True, text_color=(1,0.5,0.2,1), theme_text_color="Custom"))
        card_plan.add_widget(MDLabel(text=f"{self.plan_generado['repeticiones']}", font_style="Body1"))
        card_plan.add_widget(MDLabel(text=f"Consejo: {self.plan_generado['consejo']}", font_style="Caption", theme_text_color="Secondary"))
        layout_principal.add_widget(card_plan)
        
        self.contenedor_botones = FloatLayout(size_hint=(1, None), height=60)
        self.btn_aceptar = MDFillRoundFlatButton(text="Aceptar Plan", size_hint=(0.45, 0.9), pos_hint={"x": -0.5, "center_y": 0.5}, md_bg_color=(0.1, 0.7, 0.1, 1), on_release=lambda x: self.aceptar_plan())
        self.btn_omitir = MDFlatButton(text="Elegir Yo", size_hint=(0.45, 0.9), pos_hint={"right": 1.5, "center_y": 0.5}, theme_text_color="Custom", text_color=(0.8, 0.8, 0.8, 1), on_release=lambda x: self.omitir_plan())
        self.contenedor_botones.add_widget(self.btn_aceptar)
        self.contenedor_botones.add_widget(self.btn_omitir)
        layout_principal.add_widget(self.contenedor_botones)
        
        layout_pantalla.add_widget(layout_principal)
        self.add_widget(layout_pantalla)
        animar_botones_en_layout(layout_pantalla)
    
    def animar_botones_entrada(self):
        Animation(pos_hint={"x": 0.03, "center_y": 0.5}, duration=0.8, t='out_back').start(self.btn_aceptar)
        Animation(pos_hint={"right": 0.97, "center_y": 0.5}, duration=0.8, t='out_back').start(self.btn_omitir)

    def aceptar_plan(self):
        DATOS_USUARIO["plan_sugerido"] = self.plan_generado
        DATOS_USUARIO["ejercicio"] = self.plan_generado['ejercicio_recomendado']
        self.ir_a_ejercicios()
    
    def omitir_plan(self):
        DATOS_USUARIO["plan_sugerido"] = None
        DATOS_USUARIO["ejercicio"] = None
        self.ir_a_ejercicios()
    
    def ir_a_ejercicios(self):
        self.manager.transition.direction = "left"
        self.manager.current = "ejercicios"


# PANTALLA 4: SELECCIÓN DE EJERCICIOS
class PantallaEjercicios(Screen):
    def on_enter(self, *args):
        self.actualizar_resumen()
        if DATOS_USUARIO["plan_sugerido"]:
            self.mostrar_plan_aceptado()
            self.container_botones.height = 0
            self.container_botones.opacity = 0
        else:
            self.lbl_titulo.text = "¿Qué vas a entrenar hoy?"
            self.container_plan.clear_widgets()
            self.container_botones.height = dp(330)
            self.container_botones.opacity = 1
            self.animar_botones_cascada()
        
        self.actualizar_por_membresia()

    def actualizar_por_membresia(self):
        membresia = DATOS_USUARIO.get("membresia", "Gratis")

        # La cámara con conteo automático de repeticiones es GRATIS para todos.
        # Quien no paga puede entrenar por su cuenta con total normalidad.
        self.btn_entrenar.disabled = False
        self.btn_entrenar.text = "Iniciar Cámara de Entrenamiento"
        self.btn_entrenar.md_bg_color = (0.1, 0.6, 0.1, 1)
        self.btn_entrenar.text_color = (1, 1, 1, 1)

        if membresia in ["Premium Mensual", "Premium Anual"]:
            self.lbl_titulo.text = "Entrenamiento Premium"
            if membresia == "Premium Anual":
                self.lbl_titulo.text = "Entrenamiento Premium Anual"

            rutina = DATOS_USUARIO.get("rutina_ia")

            if not hasattr(self, "card_ia") or self.card_ia not in self.container_plan.children:
                self.card_ia = MDCard(
                    orientation="vertical", padding=dp(16), spacing=dp(6),
                    size_hint=(0.95, None), pos_hint={"center_x": 0.5},
                    radius=[15], md_bg_color=[0.05, 0.05, 0.05, 1], line_color=COLOR_AMARILLO
                )
                self.container_plan.add_widget(self.card_ia, index=0)

            self.card_ia.clear_widgets()
            titulo_rutina = rutina["tipo"] if rutina else "Rutina IA"
            self.card_ia.add_widget(MDLabel(
                text=f"[b]{titulo_rutina} Personalizado[/b]", halign="center", markup=True,
                theme_text_color="Custom", text_color=COLOR_AMARILLO, size_hint_y=None, height=dp(26)
            ))
            alto = dp(26) + dp(32)
            if rutina:
                preview_items = []
                if isinstance(rutina.get('estructura'), list):
                    # tomar primeros días del primer bloque
                    primer = rutina['estructura'][0]
                    dias = primer.get('dias', [])
                    for d in dias[:2]:
                        if d.get('ejercicios'):
                            ejercicios = d['ejercicios']
                            resumen = ' + '.join(f"{e['nombre']}" for e in ejercicios)
                        else:
                            resumen = d.get('tiempo','Descanso')
                        preview_items.append(f"{d.get('dia')}: {resumen}")
                else:
                    dias = rutina.get('dias', [])
                    for d in dias[:2]:
                        preview_items.append(f"{d.get('dia')}: {d.get('ejercicio')}")
                preview = "  •  ".join(preview_items) if preview_items else "Rutina personalizada"
                self.card_ia.add_widget(MDLabel(
                    text=preview, halign="center", font_style="Caption",
                    theme_text_color="Custom", text_color=(0.8, 0.8, 0.8, 1), size_hint_y=None, height=dp(20)
                ))
                alto += dp(20)
            self.card_ia.add_widget(MDLabel(
                text="Ve el detalle completo en tu Perfil", halign="center", font_style="Caption",
                theme_text_color="Secondary", size_hint_y=None, height=dp(20)
            ))
            alto += dp(20)
            self.card_ia.height = alto
        else:
            if hasattr(self, "card_ia") and self.card_ia in self.container_plan.children:
                self.container_plan.remove_widget(self.card_ia)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout_pantalla = FloatLayout()
        scroll = ScrollView(size_hint=(1, 1))
        layout_principal = BoxLayout(orientation='vertical', padding=25, spacing=15, size_hint_y=None)
        layout_principal.bind(minimum_height=layout_principal.setter('height'))
        
        self.lbl_resumen = MDLabel(text="", halign="center", font_style="Subtitle2", theme_text_color="Secondary", size_hint_y=None, height=25)
        layout_principal.add_widget(self.lbl_resumen)
        
        self.lbl_titulo = MDLabel(text="", halign="center", font_style="H6", bold=True, size_hint_y=None, height=35)
        layout_principal.add_widget(self.lbl_titulo)
        
        self.container_plan = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(10))
        self.container_plan.bind(minimum_height=self.container_plan.setter('height'))
        layout_principal.add_widget(self.container_plan)
        
        self.container_botones = BoxLayout(orientation='vertical', spacing=dp(15), size_hint_y=None, height=dp(330))
        
        def crear_tarjeta_ejercicio(titulo, desc, img_source, color, callback):
            card = MDCard(orientation="horizontal", padding=dp(15), spacing=dp(15), size_hint_y=None, height=dp(100), md_bg_color=(0.15, 0.15, 0.15, 1), radius=[20], line_color=(0.2, 0.2, 0.2, 1))
            img = Image(source=img_source, allow_stretch=True, size_hint_x=0.35, keep_ratio=True)
            card.add_widget(img)
            text_box = BoxLayout(orientation="vertical", size_hint_x=0.65, spacing=dp(5))
            
            lbl_tit = MDLabel(text=titulo, font_style="Subtitle1", bold=True, theme_text_color="Primary", halign="left")
            lbl_desc = MDLabel(text=desc, font_style="Caption", theme_text_color="Secondary", halign="left")
            
            text_box.add_widget(lbl_tit)
            text_box.add_widget(lbl_desc)
            card.add_widget(text_box)
            card.bind(on_release=lambda x: callback(titulo, card))
            return card

        self.btn_dominadas = crear_tarjeta_ejercicio("Dominadas", "Espalda", "img_dominadas.png", (0, 0.8, 1, 1), self.seleccionar_ejercicio)
        self.btn_flexiones = crear_tarjeta_ejercicio("Flexiones", "Pecho", "img_flexiones.png", (1, 0.5, 0, 1), self.seleccionar_ejercicio)
        self.btn_sentadillas = crear_tarjeta_ejercicio("Sentadillas", "Piernas", "img_sentadillas.png", (0.2, 0.8, 0.2, 1), self.seleccionar_ejercicio)
        
        animar_boton_en_movimiento(self.btn_dominadas)
        animar_boton_en_movimiento(self.btn_flexiones, 0.08)
        animar_boton_en_movimiento(self.btn_sentadillas, 0.16)
        
        self.container_botones.add_widget(self.btn_dominadas)
        self.container_botones.add_widget(self.btn_flexiones)
        self.container_botones.add_widget(self.btn_sentadillas)
        layout_principal.add_widget(self.container_botones)
        
        self.container_video = BoxLayout(orientation='vertical', size_hint_y=None, height=0, opacity=0)
        layout_principal.add_widget(self.container_video)
        
        btn_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=50)
        self.btn_entrenar = MDFillRoundFlatButton(
            text="Iniciar Cámara de Entrenamiento", size_hint=(0.85, None), height=50, 
            pos_hint={"center_x": 0.5}, md_bg_color=(0.1, 0.6, 0.1, 1),
            on_release=lambda x: self.comenzar_entrenamiento_camara()
        )
        btn_layout.add_widget(self.btn_entrenar)
        layout_principal.add_widget(btn_layout)
        
        scroll.add_widget(layout_principal)
        layout_pantalla.add_widget(scroll)
        self.btn_regresar_flotante = MDIconButton(
            icon="arrow-left",
            md_bg_color=(0.25, 0.25, 0.25, 1),
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            pos_hint={"x": 0.04, "top": 0.96},
            on_release=lambda x: self.regresar_pantalla()
        )
        layout_pantalla.add_widget(self.btn_regresar_flotante)
        self.add_widget(layout_pantalla)
        animar_botones_en_layout(layout_pantalla)
    
    def animar_botones_cascada(self):
        self.btn_dominadas.opacity = 0
        self.btn_flexiones.opacity = 0
        self.btn_sentadillas.opacity = 0
        Animation(opacity=1, duration=0.4).start(self.btn_dominadas)
        Clock.schedule_once(lambda dt: Animation(opacity=1, duration=0.4).start(self.btn_flexiones), 0.1)
        Clock.schedule_once(lambda dt: Animation(opacity=1, duration=0.4).start(self.btn_sentadillas), 0.2)

    def actualizar_resumen(self):
        self.lbl_resumen.text = f"Atleta: {DATOS_USUARIO['nombre']} | Ejercicio: {DATOS_USUARIO['ejercicio']}"

    def regresar_pantalla(self):
        self.manager.transition.direction = "right"
        self.manager.current = "registro"

    def mostrar_plan_aceptado(self):
        self.lbl_titulo.text = "PLAN SELECCIONADO"
        self.container_plan.clear_widgets()
        card = MDCard(orientation='vertical', padding=15, size_hint=(0.9, None), height=100, pos_hint={"center_x":0.5}, md_bg_color=(0.1, 0.2, 0.15, 1))
        card.add_widget(MDLabel(text=f"Rutina de: {DATOS_USUARIO['ejercicio']}", font_style="H6", halign="center"))
        self.container_plan.add_widget(card)

    def seleccionar_ejercicio(self, ejercicio, boton_pulsado):
        DATOS_USUARIO["ejercicio"] = ejercicio
        self.actualizar_resumen()
        for btn in [self.btn_dominadas, self.btn_flexiones, self.btn_sentadillas]:
            btn.md_bg_color = (0.15, 0.15, 0.15, 1)
        boton_pulsado.md_bg_color = (0.3, 0.1, 0.1, 1) 
        self.mostrar_video_tutorial(ejercicio)

    def mostrar_video_tutorial(self, ejercicio):
        self.container_video.clear_widgets()
        self.container_video.height = 300
        self.container_video.opacity = 1
        
        instrucciones = {
            "Dominadas": [
                "1. Agarra la barra con las palmas hacia afuera, manos al ancho de hombros.",
                "2. Cuelga con los brazos completamente extendidos.",
                "3. Sube el cuerpo hasta que la barbilla pase la barra.",
                "4. Baja lentamente hasta extender los brazos por completo."
            ],
            "Flexiones": [
                "1. Colócate boca abajo con las manos al ancho de hombros.",
                "2. Mantén el cuerpo recto como una tabla.",
                "3. Baja el pecho hasta casi tocar el suelo.",
                "4. Empuja hacia arriba hasta extender los brazos."
            ],
            "Sentadillas": [
                "1. De pie con los pies al ancho de hombros.",
                "2. Baja la cadera como si te sentaras en una silla.",
                "3. Las rodillas no deben pasar la punta de los pies.",
                "4. Sube apretando los glúteos hasta quedar de pie."
            ]
        }
        
        card_vid = MDCard(orientation='vertical', padding=15, spacing=8, radius=[15], md_bg_color=(0.1, 0.1, 0.1, 1), size_hint_y=None, height=290)
        lbl_info = MDLabel(text=f"Cómo hacer {ejercicio}", font_style="Subtitle1", size_hint_y=None, height=25, halign="center", bold=True, theme_text_color="Custom", text_color=(1, 0.4, 0.4, 1))
        card_vid.add_widget(lbl_info)
        
        contenido = BoxLayout(orientation='horizontal', spacing=10)
        video_ejercicio = Video(
            source=f"vid_{ejercicio.lower()}.mp4",
            state="play",
            options={"eos": "loop"},
            allow_stretch=True,
            keep_ratio=True,
            size_hint_x=0.4
        )
        contenido.add_widget(video_ejercicio)
        
        pasos_layout = BoxLayout(orientation='vertical', spacing=4, size_hint_x=0.6)
        pasos = instrucciones.get(ejercicio, ["Selecciona un ejercicio para ver instrucciones."])
        for paso in pasos:
            pasos_layout.add_widget(MDLabel(text=paso, font_style="Caption", theme_text_color="Primary", size_hint_y=None, height=35))
        contenido.add_widget(pasos_layout)
        
        card_vid.add_widget(contenido)
        self.container_video.add_widget(card_vid)

    def comenzar_entrenamiento_camara(self):
        if not DATOS_USUARIO["ejercicio"]:
            dialog = MDDialog(title="Error", text="Por favor, selecciona un ejercicio antes de encender la cámara.", buttons=[MDFlatButton(text="Entendido", on_release=lambda x: dialog.dismiss())])
            dialog.open()
            return
        self.manager.transition.direction = "left"
        self.manager.current = "entrenamiento_activo"


# PANTALLA 5: DETECCIÓN EN TIEMPO REAL
class PantallaEntrenamiento(Screen):
    def on_enter(self, *args):
        self.lbl_ejercicio.text = f"Entrenando: {str(DATOS_USUARIO['ejercicio']).upper()}"
        self.contador_reps = 0
        self.lbl_contador.text = "0"
        self.estado_fase = "arriba"
        
        try:
            # Inicialización directa usando las librerías oficiales del sistema
            self.pose = mp_pose.Pose(
                static_image_mode=False,
                model_complexity=1,  
                smooth_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
        except Exception as e:
            self.lbl_ejercicio.text = "Error al iniciar MediaPipe"
            print(f"Error detallado de MediaPipe: {e}")
            return
        
        try:
            self.captura = cv2.VideoCapture(0, cv2.CAP_DSHOW) 
            if not self.captura.isOpened():
                self.captura = cv2.VideoCapture(0) 
            
            if not self.captura.isOpened():
                self.lbl_ejercicio.text = "No se detecta una Webcam activa"
                return
        except Exception as e:
            self.lbl_ejercicio.text = "Error de Hardware de Cámara"
            return
        
        Clock.schedule_interval(self.procesar_frame_universal, 1.0 / 30.0)

    def on_leave(self, *args):
        Clock.unschedule(self.procesar_frame_universal)
        try:
            if hasattr(self, 'captura') and self.captura.isOpened():
                self.captura.release()
            if hasattr(self, 'pose'):
                self.pose.close()
        except:
            pass

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = FloatLayout()
        
        self.visor_camara = Image(size_hint=(1, 0.75), pos_hint={"center_x": 0.5, "top": 0.98})
        layout.add_widget(self.visor_camara)
        
        panel_inferior = BoxLayout(orientation='vertical', size_hint=(1, 0.25), pos_hint={"x": 0, "y": 0}, padding=15, spacing=10)
        
        fondo_panel = MDCard(orientation='vertical', padding=15, spacing=10, md_bg_color=(0.1, 0.1, 0.1, 0.8), radius=[20, 20, 0, 0])
        
        self.lbl_ejercicio = MDLabel(text="Iniciando componentes...", halign="center", font_style="H6", theme_text_color="Custom", text_color=(0, 0.8, 1, 1))
        fondo_panel.add_widget(self.lbl_ejercicio)
        
        layout_numeros = BoxLayout(orientation='horizontal', padding=[20, 0, 20, 0])
        layout_numeros.add_widget(MDLabel(text="REPETICIONES:", font_style="H6", halign="left", theme_text_color="Secondary"))
        self.lbl_contador = MDLabel(text="0", font_style="H2", bold=True, halign="right", theme_text_color="Custom", text_color=(0, 0.8, 0.3, 1))
        layout_numeros.add_widget(self.lbl_contador)
        fondo_panel.add_widget(layout_numeros)
        
        btn_terminar = MDFillRoundFlatButton(text="Finalizar Entrenamiento", md_bg_color=(1, 0.2, 0.2, 1), size_hint=(0.9, None), height=50, pos_hint={"center_x": 0.5}, on_release=lambda x: self.terminar())
        fondo_panel.add_widget(btn_terminar)
        
        panel_inferior.add_widget(fondo_panel)
        
        layout.add_widget(panel_inferior)
        self.add_widget(layout)
        animar_botones_en_layout(layout)

    def calcular_angulo(self, p1, p2, p3):
        x1, y1 = p1.x, p1.y
        x2, y2 = p2.x, p2.y
        x3, y3 = p3.x, p3.y
        angulo = math.degrees(math.atan2(y3 - y2, x3 - x2) - math.atan2(y1 - y2, x1 - x2))
        angulo = abs(angulo)
        if angulo > 180.0:
            angulo = 360 - angulo
        return angulo

    def procesar_frame_universal(self, dt):
        try:
            ret, frame = self.captura.read()
            if not ret or frame is None:
                return
                
            frame = cv2.flip(frame, 1) 
            alto, ancho, _ = frame.shape
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            resultados = self.pose.process(frame_rgb)
            
            if resultados.pose_landmarks:
                mp_drawing.draw_landmarks(frame, resultados.pose_landmarks, mp_pose.POSE_CONNECTIONS)
                puntos = resultados.pose_landmarks.landmark
                ejercicio_actual = DATOS_USUARIO["ejercicio"]
                
                if ejercicio_actual in ["Flexiones", "Dominadas"]:
                    hombro = puntos[mp_pose.PoseLandmark.LEFT_SHOULDER]
                    codo = puntos[mp_pose.PoseLandmark.LEFT_ELBOW]
                    muneca = puntos[mp_pose.PoseLandmark.LEFT_WRIST]
                    angulo = self.calcular_angulo(hombro, codo, muneca)
                    
                    if angulo > 160 and self.estado_fase == "abajo":
                        self.contador_reps += 1
                        self.lbl_contador.text = str(self.contador_reps)
                        self.estado_fase = "arriba"
                    elif angulo < 90:
                        self.estado_fase = "abajo"
                            
                elif ejercicio_actual == "Sentadillas":
                    cadera = puntos[mp_pose.PoseLandmark.LEFT_HIP]
                    rodilla = puntos[mp_pose.PoseLandmark.LEFT_KNEE]
                    tobillo = puntos[mp_pose.PoseLandmark.LEFT_ANKLE]
                    angulo = self.calcular_angulo(cadera, rodilla, tobillo)
                    
                    if angulo > 160 and self.estado_fase == "abajo":
                        self.contador_reps += 1
                        self.lbl_contador.text = str(self.contador_reps)
                        self.estado_fase = "arriba"
                    elif angulo < 100:
                        self.estado_fase = "abajo"

            buffer = cv2.flip(frame, 0).tobytes()
            textura_kivy = Texture.create(size=(ancho, alto), colorfmt='bgr')
            textura_kivy.blit_buffer(buffer, colorfmt='bgr', bufferfmt='ubyte')
            self.visor_camara.texture = textura_kivy
        except Exception as e:
            pass

    def terminar(self):
        # Registramos la sesión real para que Perfil y Progreso reflejen datos verdaderos
        registrar_sesion(DATOS_USUARIO["ejercicio"], self.contador_reps)
        dialog = MDDialog(
            title="¡Buen Trabajo!",
            text=f"Completaste un total de {self.contador_reps} repeticiones.",
            buttons=[MDFlatButton(text="Volver", on_release=lambda x: self.salir_limpio(dialog))]
        )
        dialog.open()

    def salir_limpio(self, dialogo):
        dialogo.dismiss()
        self.manager.transition.direction = "right"
        self.manager.current = "bienvenida"


# ==========================================
# PANTALLAS: PERFIL, PROGRESO, MEMBRESÍAS, PAGO, CONFIRMACIÓN
# ==========================================

class PantallaPerfil(Screen):
    def on_enter(self, *args):
        self.lbl_nombre.text = DATOS_USUARIO["nombre"] if DATOS_USUARIO["nombre"] else "Anónimo"
        self.lbl_detalles.text = f"{DATOS_USUARIO['edad']} años | {DATOS_USUARIO['peso']} kg | {DATOS_USUARIO['altura']} cm"
        
        membresia = DATOS_USUARIO.get("membresia", "Gratis")
        self.lbl_membresia.text = f"Membresía: {membresia}"
        if membresia != "Gratis":
            self.lbl_membresia.text_color = COLOR_AMARILLO
            self.box_membresia.line_color = COLOR_AMARILLO
        else:
            self.lbl_membresia.text_color = (0.7, 0.7, 0.7, 1)
            self.box_membresia.line_color = (0.7, 0.7, 0.7, 1)

        # Estadísticas reales
        self.lbl_sesiones.text = str(DATOS_USUARIO.get("total_sesiones", 0))
        self.lbl_racha.text = str(DATOS_USUARIO.get("racha_actual", 0))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = FloatLayout()
        box = BoxLayout(orientation='vertical', padding=dp(25), spacing=dp(20), size_hint=(0.95, 0.95), pos_hint={"center_x": 0.5, "center_y": 0.5})
        
        btn_back_fixed = MDIconButton(
            icon="arrow-left",
            pos_hint={"x": 0.02, "top": 0.96},
            size_hint=(None, None),
            size=(dp(44), dp(44)),
            on_release=lambda x: self.volver()
        )
        try:
            app = MDApp.get_running_app()
            btn_back_fixed.theme_text_color = 'Custom'
            btn_back_fixed.text_color = app.theme_cls.primary_color
        except Exception:
            pass
        layout.add_widget(btn_back_fixed)

        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50))
        header.add_widget(MDLabel(text="Mi Perfil", font_style="H5", bold=True, text_color=COLOR_AMARILLO, theme_text_color="Custom"))
        box.add_widget(header)

        avatar_box = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(200), spacing=dp(10))
        avatar_box.add_widget(MDIconButton(icon="account-circle", icon_size="80sp", pos_hint={"center_x": 0.5}, theme_text_color="Custom", text_color=(0.8, 0.1, 0.1, 1)))
        self.lbl_nombre = MDLabel(text="Anónimo", halign="center", font_style="H5", bold=True)
        self.lbl_detalles = MDLabel(text="-", halign="center", font_style="Subtitle2", theme_text_color="Secondary")
        
        self.box_membresia = MDCard(
            size_hint=(None, None), size=(dp(240), dp(35)),
            pos_hint={"center_x": 0.5}, radius=[18],
            md_bg_color=(0, 0, 0, 1), line_color=COLOR_AMARILLO
        )
        self.lbl_membresia = MDLabel(
            text="Membresía: Gratis", halign="center", font_style="Subtitle2", 
            theme_text_color="Custom", text_color=(0.7, 0.7, 0.7, 1)
        )
        self.box_membresia.add_widget(self.lbl_membresia)
        
        avatar_box.add_widget(self.lbl_nombre)
        avatar_box.add_widget(self.lbl_detalles)
        avatar_box.add_widget(self.box_membresia)
        box.add_widget(avatar_box)

        stats_card = MDCard(orientation='horizontal', padding=dp(15), size_hint_y=None, height=dp(80), md_bg_color=(0.1, 0.1, 0.1, 1), radius=[15], line_color=(0.2, 0.2, 0.2, 1))
        
        stat1 = BoxLayout(orientation='vertical')
        self.lbl_sesiones = MDLabel(text="0", halign="center", font_style="H5", text_color=(0, 0.6, 1, 1), theme_text_color="Custom", bold=True)
        stat1.add_widget(self.lbl_sesiones)
        stat1.add_widget(MDLabel(text="Sesiones", halign="center", font_style="Caption", theme_text_color="Secondary"))
        
        stat2 = BoxLayout(orientation='vertical')
        self.lbl_racha = MDLabel(text="0", halign="center", font_style="H5", text_color=(1, 0.4, 0, 1), theme_text_color="Custom", bold=True)
        stat2.add_widget(self.lbl_racha)
        stat2.add_widget(MDLabel(text="Racha (días)", halign="center", font_style="Caption", theme_text_color="Secondary"))

        stats_card.add_widget(stat1)
        stats_card.add_widget(stat2)
        box.add_widget(stats_card)

        app = MDApp.get_running_app()
        box.add_widget(MDFillRoundFlatButton(text="Ver Mi Progreso", size_hint=(1, None), height=dp(50), md_bg_color=app.theme_cls.primary_color if app else (0.12, 0.12, 0.12, 1), text_color=(1, 1, 1, 1), on_release=lambda x: self.ir_a_progreso()))
        box.add_widget(MDFillRoundFlatButton(text="Ver Mi Rutina IA", size_hint=(1, None), height=dp(50), md_bg_color=app.theme_cls.primary_color if app else (0.12, 0.12, 0.12, 1), text_color=COLOR_AMARILLO, on_release=lambda x: self.ver_rutina()))
        box.add_widget(MDFillRoundFlatButton(text="Gestionar Membresía", size_hint=(1, None), height=dp(50), md_bg_color=COLOR_AMARILLO, text_color=(0, 0, 0, 1), on_release=lambda x: self.ir_a_membresias()))
        box.add_widget(MDFillRoundFlatButton(text="Cambiar Tema", size_hint=(1, None), height=dp(50), md_bg_color=(0.2,0.2,0.2,1), text_color=(1,1,1,1), on_release=lambda x: self.abrir_selector_tema()))
        
        box.add_widget(MDLabel(text="", size_hint_y=1))
        
        layout.add_widget(box)
        self.add_widget(layout)
        animar_botones_en_layout(layout)

    def volver(self):
        self.manager.transition.direction = "right"
        self.manager.current = "bienvenida"

    def abrir_selector_tema(self):
        # diálogo con tres temas y botones visibles
        opciones = ["Red", "Blue", "Green"]
        dialog = MDDialog(
            title="Selecciona un tema",
            text="Elige la paleta de la aplicación:",
            size_hint=(0.8, None),
            buttons=[
                MDFlatButton(text="Red", on_release=lambda btn: (self.aplicar_tema("Red"), dialog.dismiss())),
                MDFlatButton(text="Blue", on_release=lambda btn: (self.aplicar_tema("Blue"), dialog.dismiss())),
                MDFlatButton(text="Green", on_release=lambda btn: (self.aplicar_tema("Green"), dialog.dismiss())),
                MDFlatButton(text="Cerrar", on_release=lambda btn: dialog.dismiss())
            ]
        )
        dialog.open()

    def aplicar_tema(self, paleta):
        try:
            app = MDApp.get_running_app()
            # aplicar paleta y ajustar el matiz por defecto
            app.theme_cls.primary_palette = paleta
            try:
                app.theme_cls.primary_hue = "500"
            except Exception:
                pass
            # guardar preferencia
            DATOS_USUARIO['tema'] = paleta
            DATOS_USUARIO['theme_style'] = app.theme_cls.theme_style
            save_user_data()
            # Guardado realizado. Ahora refrescar algunos widgets que usan md_bg_color
            try:
                from kivymd.uix.button import MDFillRoundFlatButton, MDRectangleFlatIconButton, MDRaisedButton, MDFlatButton
                from kivymd.uix.button import MDIconButton
                root = app.root
                if root:
                    for screen in getattr(root, 'screens', []):
                        for child in screen.walk(restrict=True):
                            try:
                                # Actualizar botones que no sean badges amarillos
                                if isinstance(child, (MDFillRoundFlatButton, MDRectangleFlatIconButton, MDRaisedButton, MDFlatButton)):
                                    mbg = getattr(child, 'md_bg_color', None)
                                    if mbg is None or (isinstance(mbg, (list, tuple)) and tuple(mbg) != tuple(COLOR_AMARILLO)):
                                        child.md_bg_color = app.theme_cls.primary_color
                                        child.text_color = (1,1,1,1)
                                if isinstance(child, MDIconButton):
                                    child.theme_text_color = 'Custom'
                                    child.text_color = app.theme_cls.primary_color
                            except Exception:
                                pass
            except Exception:
                pass
        except Exception as e:
            print('Error aplicando tema:', e)

    def ir_a_progreso(self):
        self.manager.transition.direction = "left"
        if DATOS_USUARIO.get("rutina_ia"):
            self.manager.current = "rutina"
        else:
            self.manager.current = "progreso"

    def ir_a_membresias(self):
        self.manager.transition.direction = "left"
        self.manager.current = "membresias"

    def ver_rutina(self):
        rutina = DATOS_USUARIO.get("rutina_ia")
        if not rutina:
            dialog = MDDialog(
                title="Sin Rutina IA",
                text="Activa un plan Premium para desbloquear tu rutina personalizada semanal o mensual.",
                buttons=[
                    MDFlatButton(text="Ver Planes", on_release=lambda x: (dialog.dismiss(), self.ir_a_membresias())),
                    MDFlatButton(text="Cerrar", on_release=lambda x: dialog.dismiss())
                ]
            )
            dialog.open()
            return

        tipo = rutina.get('tipo','Rutina')
        lines = []
        if isinstance(rutina.get('estructura'), list) and tipo.lower().find('mens') != -1:
            for semana in rutina['estructura']:
                for d in semana.get('dias', []):
                    ejercicios = d.get('ejercicios', [])
                    if ejercicios:
                        resumen = ' + '.join(f"{e['nombre']} ({e['series']}x{e['reps']})" for e in ejercicios)
                    else:
                        resumen = d.get('tiempo','Descanso')
                    lines.append(f"Semana {semana.get('semana_num')} - {d.get('dia')}: {resumen}")
        elif isinstance(rutina.get('estructura'), list) and tipo.lower().find('anual') != -1:
            mes = rutina['estructura'][0]
            lines.append(f"{mes.get('descripcion')}")
            for semana in mes.get('semanas', []):
                for d in semana.get('dias', []):
                    ejercicios = d.get('ejercicios', [])
                    resumen = ' + '.join(f"{e['nombre']} ({e['series']}x{e['reps']})" for e in ejercicios) if ejercicios else d.get('tiempo','Descanso')
                    lines.append(f"Semana {semana.get('semana_num')} - {d.get('dia')}: {resumen}")
        else:
            dias = rutina.get('dias', [])
            for d in dias:
                lines.append(f"{d.get('dia')}: {d.get('ejercicio')} — {d.get('series')}")

        detalle = "\n".join(lines[:50])
        dialog = MDDialog(
            title=f"{tipo} generado por IA",
            text=f"{rutina.get('duracion','')}\n\n{detalle}",
            buttons=[MDFlatButton(text="Cerrar", on_release=lambda x: dialog.dismiss())]
        )
        dialog.open()


class PantallaProgreso(Screen):
    def on_enter(self, *args):
        self.actualizar_datos()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = FloatLayout()
        scroll = ScrollView(size_hint=(1, 1))
        box = BoxLayout(orientation='vertical', padding=dp(25), spacing=dp(20), size_hint_y=None)
        box.bind(minimum_height=box.setter('height'))
        
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50))
        btn_back = MDIconButton(icon="arrow-left", on_release=lambda x: self.volver())
        header.add_widget(btn_back)
        header.add_widget(MDLabel(text="Estadísticas", font_style="H5", bold=True))
        box.add_widget(header)

        grid = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(100), spacing=dp(15))
        
        card_reps = MDCard(orientation='vertical', padding=dp(10), md_bg_color=(0.15, 0.15, 0.15, 1), radius=[15])
        card_reps.add_widget(MDIconButton(icon="arm-flex", pos_hint={"center_x": 0.5}, theme_text_color="Custom", text_color=(1, 0.2, 0.2, 1)))
        self.lbl_reps_totales = MDLabel(text="0", halign="center", font_style="H5", bold=True)
        card_reps.add_widget(self.lbl_reps_totales)
        card_reps.add_widget(MDLabel(text="Reps Totales", halign="center", font_style="Caption"))
        
        card_dias = MDCard(orientation='vertical', padding=dp(10), md_bg_color=(0.15, 0.15, 0.15, 1), radius=[15])
        card_dias.add_widget(MDIconButton(icon="calendar-check", pos_hint={"center_x": 0.5}, theme_text_color="Custom", text_color=(0, 0.8, 0.3, 1)))
        self.lbl_mejor_dia = MDLabel(text="N/A", halign="center", font_style="H5", bold=True)
        card_dias.add_widget(self.lbl_mejor_dia)
        card_dias.add_widget(MDLabel(text="Mejor Día", halign="center", font_style="Caption"))

        grid.add_widget(card_reps)
        grid.add_widget(card_dias)
        box.add_widget(grid)

        box.add_widget(MDLabel(text="Últimas Sesiones", font_style="Subtitle1", bold=True, size_hint_y=None, height=dp(30)))
        self.container_historial = BoxLayout(orientation='vertical', spacing=dp(4), size_hint_y=None, height=dp(30))
        box.add_widget(self.container_historial)

        self.card_mensaje = MDCard(md_bg_color=(1, 0.5, 0, 0.2), padding=dp(15), radius=[10], size_hint_y=None, height=dp(80))
        self.lbl_mensaje = MDLabel(text="", theme_text_color="Custom", text_color=(1, 0.6, 0, 1), halign="center", font_style="Subtitle2")
        self.card_mensaje.add_widget(self.lbl_mensaje)
        box.add_widget(self.card_mensaje)

        box.add_widget(MDLabel(text="", size_hint_y=None, height=dp(20)))
        scroll.add_widget(box)
        layout.add_widget(scroll)
        self.add_widget(layout)
        animar_botones_en_layout(layout)

    def actualizar_datos(self):
        self.lbl_reps_totales.text = str(DATOS_USUARIO.get("reps_totales", 0))
        self.lbl_mejor_dia.text = calcular_mejor_dia()

        self.container_historial.clear_widgets()
        historial = DATOS_USUARIO.get("historial_sesiones", [])

        if not historial:
            self.container_historial.add_widget(MDLabel(
                text="Aún no tienes sesiones registradas. ¡Empieza a entrenar!",
                theme_text_color="Secondary", font_style="Caption",
                size_hint_y=None, height=dp(40)
            ))
            self.container_historial.height = dp(40)
        else:
            hoy = datetime.date.today()
            visibles = historial[:5]
            for sesion in visibles:
                fecha = sesion.get("fecha")
                # convertir si la fecha viene como string
                if isinstance(fecha, str):
                    try:
                        fecha = datetime.date.fromisoformat(fecha)
                    except Exception:
                        try:
                            fecha = datetime.datetime.fromisoformat(fecha).date()
                        except Exception:
                            fecha = None
                if fecha == hoy:
                    etiqueta = "Hoy"
                elif fecha == hoy - datetime.timedelta(days=1):
                    etiqueta = "Ayer"
                elif isinstance(fecha, datetime.date):
                    dias = (hoy - fecha).days
                    etiqueta = f"Hace {dias} días"
                else:
                    etiqueta = "Fecha desconocida"
                self.container_historial.add_widget(MDLabel(
                    text=f"{etiqueta}: {sesion.get('ejercicio','-')} - {sesion.get('reps','-')} reps",
                    theme_text_color="Secondary", font_style="Body2",
                    size_hint_y=None, height=dp(25)
                ))
            self.container_historial.height = dp(25) * len(visibles)

        total = DATOS_USUARIO.get("total_sesiones", 0)
        racha = DATOS_USUARIO.get("racha_actual", 0)
        if total == 0:
            self.lbl_mensaje.text = "Realiza tu primer entrenamiento con la cámara IA para empezar a ver tu progreso."
        elif racha >= 3:
            self.lbl_mensaje.text = f"¡Llevas {racha} días seguidos entrenando! Sigue así."
        else:
            self.lbl_mensaje.text = f"Ya llevas {total} sesiones completadas y {DATOS_USUARIO.get('reps_totales', 0)} repeticiones en total. ¡Vas muy bien!"

    def volver(self):
        self.manager.transition.direction = "right"
        self.manager.current = "perfil"


class PantallaMembresias(Screen):
    def on_enter(self, *args):
        self.actualizar_ui()

    def actualizar_ui(self):
        self.card_gratis.line_color = (0.2, 0.2, 0.2, 1)
        self.card_mensual.line_color = (0.2, 0.2, 0.2, 1)
        self.card_anual.line_color = (0.2, 0.2, 0.2, 1)
        
        self.btn_gratis.text = "Seleccionar"
        self.btn_mensual.text = "Seleccionar"
        self.btn_anual.text = "Seleccionar"

        membresia_actual = DATOS_USUARIO.get("membresia", "Gratis")
        if membresia_actual == "Gratis":
            self.card_gratis.line_color = COLOR_AMARILLO
            self.btn_gratis.text = "Plan Actual (Activo)"
        elif membresia_actual == "Premium Mensual":
            self.card_mensual.line_color = COLOR_AMARILLO
            self.btn_mensual.text = "Plan Actual (Activo)"
        elif membresia_actual == "Premium Anual":
            self.card_anual.line_color = COLOR_AMARILLO
            self.btn_anual.text = "Plan Actual (Activo)"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = FloatLayout()
        scroll = ScrollView(size_hint=(1, 1))
        box = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15), size_hint_y=None)
        box.bind(minimum_height=box.setter('height'))
        
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50))
        btn_back = MDIconButton(icon="arrow-left", on_release=lambda x: self.volver())
        header.add_widget(btn_back)
        header.add_widget(MDLabel(text="Planes Premium", font_style="H5", bold=True, text_color=COLOR_AMARILLO, theme_text_color="Custom"))
        box.add_widget(header)

        # Básico
        self.card_gratis = MDCard(orientation='vertical', padding=dp(15), spacing=dp(10), size_hint_y=None, height=dp(160), radius=[15], md_bg_color=(0.1, 0.1, 0.1, 1), line_color=(0.2, 0.2, 0.2, 1))
        row1 = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50))
        row1.add_widget(MDIconButton(icon="currency-usd-off", theme_text_color="Secondary"))
        title_box = BoxLayout(orientation='vertical')
        title_box.add_widget(MDLabel(text="Básico", font_style="H6", bold=True))
        title_box.add_widget(MDLabel(text="$0.00 / mes", font_style="Caption", theme_text_color="Secondary"))
        row1.add_widget(title_box)
        self.card_gratis.add_widget(row1)
        self.card_gratis.add_widget(MDLabel(text="Cámara IA gratis para contar tus repeticiones • Historial limitado • Sin rutinas IA", font_style="Caption", theme_text_color="Secondary"))
        self.btn_gratis = MDFillRoundFlatButton(text="Seleccionar", size_hint=(1, None), height=dp(45), md_bg_color=(0.2,0.2,0.2,1), text_color=(1,1,1,1), on_release=lambda x: self.seleccionar_plan("Gratis", 0))
        self.card_gratis.add_widget(self.btn_gratis)
        box.add_widget(self.card_gratis)

        # Mensual
        self.card_mensual = MDCard(orientation='vertical', padding=dp(15), spacing=dp(10), size_hint_y=None, height=dp(200), radius=[15], md_bg_color=(0.1, 0.1, 0.1, 1), line_color=(0.2, 0.2, 0.2, 1))
        row2 = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50))
        row2.add_widget(MDIconButton(icon="star-outline", theme_text_color="Custom", text_color=COLOR_AMARILLO))
        title_box2 = BoxLayout(orientation='vertical')
        title_box2.add_widget(MDLabel(text="Premium Mensual", font_style="H6", bold=True, theme_text_color="Custom", text_color=COLOR_AMARILLO))
        title_box2.add_widget(MDLabel(text="$9.99 / mes", font_style="Caption", theme_text_color="Secondary"))
        row2.add_widget(title_box2)
        self.card_mensual.add_widget(row2)
        self.card_mensual.add_widget(MDLabel(text="Rutina IA semanal personalizada • Historial ilimitado • Todos los ejercicios", font_style="Caption", theme_text_color="Secondary"))
        self.btn_mensual = MDFillRoundFlatButton(text="Seleccionar", size_hint=(1, None), height=dp(45), md_bg_color=COLOR_AMARILLO, text_color=(0,0,0,1), on_release=lambda x: self.seleccionar_plan("Premium Mensual", 9.99))
        self.card_mensual.add_widget(self.btn_mensual)
        box.add_widget(self.card_mensual)

        # Anual
        self.card_anual = MDCard(orientation='vertical', padding=dp(15), spacing=dp(5), size_hint_y=None, height=dp(240), radius=[15], md_bg_color=(0.1, 0.1, 0.1, 1), line_color=COLOR_AMARILLO)
        
        badge_bg = MDCard(md_bg_color=COLOR_AMARILLO, radius=[10], size_hint=(None, None), size=(dp(120), dp(25)), pos_hint={"center_x": 0.5})
        badge = MDLabel(text="⭐ MEJOR VALOR", font_style="Caption", bold=True, theme_text_color="Custom", text_color=(0,0,0,1), halign="center")
        badge_bg.add_widget(badge)
        self.card_anual.add_widget(badge_bg)

        row3 = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50))
        row3.add_widget(MDIconButton(icon="crown-outline", theme_text_color="Custom", text_color=COLOR_AMARILLO))
        title_box3 = BoxLayout(orientation='vertical')
        title_box3.add_widget(MDLabel(text="Premium Anual", font_style="H6", bold=True, theme_text_color="Custom", text_color=COLOR_AMARILLO))
        title_box3.add_widget(MDLabel(text="$79.99 / año [color=#00cc44]Ahorra 33%[/color]", markup=True, font_style="Caption", theme_text_color="Secondary"))
        row3.add_widget(title_box3)
        self.card_anual.add_widget(row3)
        self.card_anual.add_widget(MDLabel(text="Rutina IA mensual de 4 semanas • Soporte prioritario • Acceso anticipado", font_style="Caption", theme_text_color="Secondary"))
        self.btn_anual = MDFillRoundFlatButton(text="Seleccionar", size_hint=(1, None), height=dp(45), md_bg_color=COLOR_AMARILLO, text_color=(0,0,0,1), on_release=lambda x: self.seleccionar_plan("Premium Anual", 79.99))
        self.card_anual.add_widget(self.btn_anual)
        box.add_widget(self.card_anual)

        scroll.add_widget(box)
        layout.add_widget(scroll)
        self.add_widget(layout)
        animar_botones_en_layout(layout)

    def volver(self):
        self.manager.transition.direction = "right"
        self.manager.current = "bienvenida"

    def seleccionar_plan(self, plan, precio):
        if plan == "Gratis":
            DATOS_USUARIO["membresia"] = "Gratis"
            DATOS_USUARIO["membresia_activa"] = False
            DATOS_USUARIO["rutina_ia"] = None
            self.actualizar_ui()
            dialog = MDDialog(title="Plan Actualizado", text="Has vuelto al plan Gratis. La cámara IA sigue disponible para ti sin costo.", buttons=[MDFlatButton(text="OK", on_release=lambda x: dialog.dismiss())])
            dialog.open()
        else:
            DATOS_USUARIO["plan_temp"] = plan
            DATOS_USUARIO["precio_temp"] = precio
            self.manager.transition.direction = "left"
            self.manager.current = "pago"

class PantallaPago(Screen):
    def on_enter(self, *args):
        plan = DATOS_USUARIO.get("plan_temp", "Premium")
        precio = DATOS_USUARIO.get("precio_temp", "0.00")
        self.lbl_resumen.text = f"Pagando: {plan} (${precio})"
        self.txt_nombre.text = ""
        self.txt_tarjeta.text = ""
        self.txt_fecha.text = ""
        self.txt_cvv.text = ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = FloatLayout()
        box = BoxLayout(orientation='vertical', padding=dp(25), spacing=dp(15))
        
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50))
        btn_back = MDIconButton(icon="arrow-left", on_release=lambda x: self.volver())
        header.add_widget(btn_back)
        header.add_widget(MDLabel(text="Pago Seguro", font_style="H5", bold=True, text_color=COLOR_AMARILLO, theme_text_color="Custom"))
        header.add_widget(MDIconButton(icon="lock-outline", theme_text_color="Custom", text_color=(0,0.8,0.3,1)))
        box.add_widget(header)

        self.card_resumen = MDCard(
            orientation='vertical', size_hint=(1, None), height=dp(50), padding=dp(10),
            md_bg_color=(0.1, 0.1, 0.05, 1), radius=[10], line_color=COLOR_AMARILLO
        )
        self.lbl_resumen = MDLabel(
            text="Pagando: Plan", font_style="Subtitle1", bold=True,
            text_color=COLOR_AMARILLO, theme_text_color="Custom", halign="center"
        )
        self.card_resumen.add_widget(self.lbl_resumen)
        box.add_widget(self.card_resumen)

        preview = MDCard(md_bg_color=(0.1, 0.1, 0.15, 1), line_color=(0.2,0.2,0.3,1), radius=[15], size_hint_y=None, height=dp(130), padding=dp(15), orientation="vertical")
        preview.add_widget(MDIconButton(icon="credit-card-chip", theme_text_color="Custom", text_color=COLOR_AMARILLO))
        preview.add_widget(MDLabel(text="**** **** **** ****", font_style="H5", theme_text_color="Secondary"))
        
        row_prev = BoxLayout(orientation="horizontal")
        row_prev.add_widget(MDLabel(text="TITULAR", font_style="Caption", theme_text_color="Secondary"))
        row_prev.add_widget(MDLabel(text="MM/AA", font_style="Caption", halign="right", theme_text_color="Secondary"))
        preview.add_widget(row_prev)
        box.add_widget(preview)

        self.txt_nombre = MDTextField(hint_text="Nombre del Titular", mode="rectangle", size_hint_y=None, height=dp(50))
        self.txt_tarjeta = MDTextField(hint_text="Número de Tarjeta", mode="rectangle", size_hint_y=None, height=dp(50), max_text_length=16)
        
        row_fechas = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(50))
        self.txt_fecha = MDTextField(hint_text="MM/AA", mode="rectangle")
        self.txt_cvv = MDTextField(hint_text="CVV", mode="rectangle", max_text_length=3, password=True)
        row_fechas.add_widget(self.txt_fecha)
        row_fechas.add_widget(self.txt_cvv)

        box.add_widget(self.txt_nombre)
        box.add_widget(self.txt_tarjeta)
        box.add_widget(row_fechas)

        btn_pagar = MDFillRoundFlatButton(text="Procesar Pago", size_hint=(1, None), height=dp(50), md_bg_color=COLOR_AMARILLO, text_color=(0,0,0,1), on_release=lambda x: self.procesar_pago())
        box.add_widget(btn_pagar)

        box.add_widget(MDLabel(text="", size_hint_y=1))
        layout.add_widget(box)
        self.add_widget(layout)
        animar_botones_en_layout(layout)

    def volver(self):
        self.manager.transition.direction = "right"
        self.manager.current = "membresias"

    def procesar_pago(self):
        if not self.txt_nombre.text or len(self.txt_tarjeta.text) < 15 or not self.txt_fecha.text or not self.txt_cvv.text:
            dialog = MDDialog(title="Error", text="Por favor completa todos los campos correctamente.", buttons=[MDFlatButton(text="OK", on_release=lambda x: dialog.dismiss())])
            dialog.open()
            return
        
        plan = DATOS_USUARIO.get("plan_temp", "Premium")
        DATOS_USUARIO["membresia"] = plan
        DATOS_USUARIO["membresia_activa"] = True
        # Fechas de inicio y expiración
        hoy = datetime.date.today()
        if plan == "Premium Mensual":
            expiracion = hoy + timedelta(days=30)
        else:
            expiracion = hoy + timedelta(days=365)
        DATOS_USUARIO["membresia_inicio"] = str(hoy)
        DATOS_USUARIO["membresia_expira"] = str(expiracion)

        # Generar y guardar la rutina correspondiente
        DATOS_USUARIO["rutina_ia"] = generar_rutina_ia(plan)
        DATOS_USUARIO.setdefault("progreso_rutina", {})
        # inicializar progreso: marcar todos los días como Pendiente
        DATOS_USUARIO["progreso_rutina"][plan] = {"marcas": [], "completados": 0}
        save_user_data()

        # Redirigir a confirmación y luego a la vista del plan específico
        self.manager.transition.direction = "left"
        self.manager.current = "confirmacion"

class PantallaConfirmacion(Screen):
    def on_enter(self, *args):
        self.lbl_plan.text = f"Plan Activado: {DATOS_USUARIO['membresia']}"
        self.animar_check()
        self.mostrar_rutina_ia()
        # Abrir automáticamente la vista detallada de la rutina (semanal/mensual)
        def abrir_rutina(dt):
            try:
                if self.manager:
                    self.manager.transition.direction = "left"
                    self.manager.current = "rutina"
            except:
                pass
        Clock.schedule_once(abrir_rutina, 1.2)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = FloatLayout()
        scroll = ScrollView(size_hint=(1, 1))
        box = BoxLayout(orientation='vertical', padding=dp(30), spacing=dp(15), size_hint_y=None)
        box.bind(minimum_height=box.setter('height'))
        
        box.add_widget(MDLabel(text="", size_hint_y=None, height=dp(10)))

        self.icon_check = MDIconButton(
            icon="check-circle-outline", 
            icon_size="100sp", 
            theme_text_color="Custom", 
            text_color=(0, 0.8, 0.3, 1),
            pos_hint={"center_x": 0.5},
            size_hint_y=None, height=dp(100),
            opacity=0
        )
        box.add_widget(self.icon_check)

        box.add_widget(MDLabel(text="¡Pago Exitoso!", halign="center", font_style="H4", bold=True, text_color=COLOR_AMARILLO, theme_text_color="Custom", size_hint_y=None, height=dp(45)))

        self.card_plan = MDCard(orientation='vertical', size_hint_y=None, height=dp(60), padding=dp(10), md_bg_color=(0.1, 0.1, 0.05, 1), radius=[10])
        self.lbl_plan = MDLabel(text="Plan Activado: -", halign="center", font_style="H6", bold=True)
        self.card_plan.add_widget(self.lbl_plan)
        box.add_widget(self.card_plan)

        card_beneficios = MDCard(
            orientation="vertical",
            padding=dp(15),
            spacing=dp(5),
            md_bg_color=(0.1, 0.1, 0.1, 1),
            radius=[15],
            size_hint_y=None,
            height=dp(110),
            line_color=(0.2, 0.3, 0.2, 1)
        )
        card_beneficios.add_widget(MDLabel(
            text="Desbloqueado para ti:",
            font_style="Subtitle2",
            bold=True,
            theme_text_color="Custom",
            text_color=(0, 0.8, 0.3, 1),
            size_hint_y=None, height=dp(25)
        ))
        
        self.lbl_beneficios = MDLabel(
            text="[color=#00cc44]-[/color] Rutina IA personalizada\n[color=#00cc44]-[/color] Historial ilimitado\n[color=#00cc44]-[/color] Cámara IA (también gratis para todos)",
            markup=True,
            font_style="Caption"
        )
        card_beneficios.add_widget(self.lbl_beneficios)
        box.add_widget(card_beneficios)

        # Contenedor dinámico donde se muestra la rutina generada por la IA
        self.container_rutina = BoxLayout(orientation='vertical', spacing=dp(6), size_hint_y=None, height=0)
        box.add_widget(self.container_rutina)

        box.add_widget(MDLabel(text="Gracias por confiar en FLEX-REX.\nDisfruta de tus nuevos beneficios premium.", halign="center", font_style="Caption", theme_text_color="Secondary", size_hint_y=None, height=dp(40)))

        btn_comenzar = MDFillRoundFlatButton(text="Comenzar a Entrenar", size_hint=(1, None), height=dp(50), md_bg_color=COLOR_AMARILLO, text_color=(0,0,0,1), on_release=lambda x: self.ir_inicio())
        box.add_widget(btn_comenzar)

        box.add_widget(MDLabel(text="", size_hint_y=None, height=dp(20)))

        scroll.add_widget(box)
        layout.add_widget(scroll)
        self.add_widget(layout)
        animar_botones_en_layout(layout)

    def mostrar_rutina_ia(self):
        self.container_rutina.clear_widgets()
        rutina = DATOS_USUARIO.get("rutina_ia")
        if not rutina:
            self.container_rutina.height = 0
            return

        card = MDCard(orientation='vertical', padding=dp(15), spacing=dp(6), md_bg_color=(0.08, 0.08, 0.12, 1), radius=[15], line_color=COLOR_AMARILLO, size_hint_y=None)
        tipo = rutina.get('tipo', 'Rutina IA')
        card.add_widget(MDLabel(text=f"{tipo} generado por IA", font_style="Subtitle1", bold=True, theme_text_color="Custom", text_color=COLOR_AMARILLO, size_hint_y=None, height=dp(28)))
        card.add_widget(MDLabel(text=str(rutina.get('duracion','')), font_style="Caption", theme_text_color="Secondary", size_hint_y=None, height=dp(30)))

        alto_card = dp(28) + dp(30) + dp(10)

        # Si es estructura mensual (4 semanas)
        if isinstance(rutina.get('estructura'), list) and tipo.lower().find('mens') != -1:
            # mostrar el resumen de cada semana (primer nivel)
            for semana in rutina['estructura']:
                alto_card += dp(20)
                card.add_widget(MDLabel(text=f"Semana {semana.get('semana_num')}", font_style="Subtitle2", size_hint_y=None, height=dp(20)))
                for d in semana.get('dias', []):
                    ejercicios = d.get('ejercicios', [])
                    if ejercicios:
                        resumen = ' + '.join(f"{e['nombre']} ({e['series']}x{e['reps']})" for e in ejercicios)
                    else:
                        resumen = d.get('tiempo','Descanso')
                    card.add_widget(MDLabel(text=f"- {d.get('dia')}: {resumen}", font_style="Body2", size_hint_y=None, height=dp(20)))
                    alto_card += dp(20)

        # Si es estructura anual (12 meses)
        elif isinstance(rutina.get('estructura'), list) and tipo.lower().find('anual') != -1:
            # mostrar resumen por meses (solo primeras 3 para no saturar)
            for mes in rutina['estructura'][:3]:
                card.add_widget(MDLabel(text=f"Mes {mes.get('mes')}: {mes.get('descripcion')}", font_style="Subtitle2", size_hint_y=None, height=dp(20)))
                alto_card += dp(20)
                # mostrar los ejercicios del primer día de la primera semana como ejemplo
                primer_sem = mes.get('semanas', [])[0] if mes.get('semanas') else None
                if primer_sem and primer_sem.get('dias'):
                    d = primer_sem['dias'][0]
                    ejercicios = d.get('ejercicios', [])
                    resumen = ' + '.join(f"{e['nombre']} ({e['series']}x{e['reps']})" for e in ejercicios) if ejercicios else d.get('tiempo','')
                    card.add_widget(MDLabel(text=f"- Ejemplo: {d.get('dia')}: {resumen}", font_style="Body2", size_hint_y=None, height=dp(20)))
                    alto_card += dp(20)

        else:
            # Fallback para estructuras antiguas
            dias = rutina.get('dias') or []
            for d in dias:
                card.add_widget(MDLabel(text=f"- {d.get('dia','Dia')}: {d.get('ejercicio','')} — {d.get('series','')}", font_style="Body2", size_hint_y=None, height=dp(20)))
                alto_card += dp(20)

        card.height = alto_card
        self.container_rutina.add_widget(card)
        self.container_rutina.height = alto_card

    def animar_check(self):
        # NOTA: "icon_size" es una propiedad de texto (ej. "100sp"), no numérica.
        # Animar directamente ese tipo de propiedad hace que Kivy lance una
        # excepción no controlada y cierre la app. Usamos "opacity" (numérica)
        # para lograr un efecto de aparición seguro y equivalente.
        self.icon_check.opacity = 0
        anim = Animation(opacity=1, duration=0.5, t='out_bounce')
        anim.start(self.icon_check)

    def ir_inicio(self):
        self.manager.transition.direction = "right"
        self.manager.current = "bienvenida"


class PantallaRutina(Screen):
    """Muestra la lista semanal o mensual según la rutina generada por la IA."""
    def on_enter(self, *args):
        self.build_ui()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = FloatLayout()
        self.scroll = ScrollView(size_hint=(1, 1))
        self.box = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(12), size_hint_y=None)
        self.box.bind(minimum_height=self.box.setter('height'))
        self.scroll.add_widget(self.box)
        self.layout.add_widget(self.scroll)
        btn_back = MDIconButton(icon="arrow-left", pos_hint={"x":0.02, "top":0.96}, on_release=lambda x: self.volver())
        self.layout.add_widget(btn_back)
        self.add_widget(self.layout)

    def build_ui(self):
        self.box.clear_widgets()
        rutina = DATOS_USUARIO.get("rutina_ia")
        if not rutina:
            self.box.add_widget(MDLabel(text="No hay rutina activa. Activa un plan para ver tu rutina personalizada.", size_hint_y=None, height=dp(40), theme_text_color="Secondary"))
            return

        # Comprobar expiración de membresía
        exp = DATOS_USUARIO.get("membresia_expira")
        if exp:
            try:
                fecha_exp = datetime.datetime.strptime(exp, "%Y-%m-%d").date()
                if datetime.date.today() > fecha_exp:
                    dialog = MDDialog(title="Suscripción expirada", text="Tu suscripción ha expirado. Renueva para acceder al plan.", buttons=[MDFlatButton(text="Ver Planes", on_release=lambda x: (dialog.dismiss(), self.ir_membresias())), MDFlatButton(text="Cerrar", on_release=lambda x: dialog.dismiss())])
                    dialog.open()
                    return
            except Exception:
                pass

        titulo = MDLabel(text=f"{rutina.get('tipo','Rutina')} - Detalle", font_style="H5", bold=True, halign="center", size_hint_y=None, height=dp(40))
        self.box.add_widget(titulo)

        # Mostrar plan mensual (estructura: lista de semanas)
        if isinstance(rutina.get('estructura'), list) and rutina.get('tipo','').lower().find('mens') != -1:
            semanas = rutina['estructura']
            total_dias = sum(len(s['dias']) for s in semanas)
            completados = 0
            for semana in semanas:
                self.box.add_widget(MDLabel(text=f"Semana {semana.get('semana_num')}", font_style="Subtitle1", size_hint_y=None, height=dp(28)))
                for d in semana.get('dias', []):
                    card = MDCard(orientation='vertical', padding=dp(12), spacing=dp(8), size_hint_y=None, radius=[16], md_bg_color=(0.06,0.07,0.09,1), line_color=(0.18,0.18,0.18,1))
                    dia = d.get('dia')
                    tiempo = d.get('tiempo','20-30 min')
                    estado = d.get('estado','Pendiente')
                    ejercicios = d.get('ejercicios', [])
                    # Header con label y check icon
                    header_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(28))
                    lbl = MDLabel(text=f"[b]{dia}[/b]    {tiempo}", markup=True, font_style="Subtitle2", halign="left")
                    icon_check = MDIconButton(icon="check-circle", theme_text_color="Custom", text_color=(0,0.8,0.3,1))
                    icon_check.opacity = 1 if estado == 'Completado' else 0.12
                    icon_check.disabled = True
                    header_box.add_widget(lbl)
                    header_box.add_widget(icon_check)
                    card.add_widget(header_box)
                    for ex in ejercicios:
                        card.add_widget(MDLabel(text=f"- {ex.get('nombre')} ({ex.get('series')}x{ex.get('reps')})", font_style="Body2", size_hint_y=None, height=dp(20)))
                    # Botones: marcar y comenzar ahora
                    btn_box = BoxLayout(orientation='horizontal', spacing=dp(8), size_hint_y=None, height=dp(44))
                    btn_toggle = MDFillRoundFlatButton(text=("Marcar completado" if estado=="Pendiente" else "Marcar pendiente"), size_hint=(0.6, None), height=dp(44), md_bg_color=(0.2,0.6,0.2,1) if estado=="Completado" else (0.2,0.2,0.2,1), on_release=lambda x, dd=d: self.toggle_estado(dd))
                    def comenzar_ahora(dd=d):
                        # establecer ejercicio principal y abrir cámara
                        primeros = dd.get('ejercicios', [])
                        if primeros:
                            DATOS_USUARIO['ejercicio'] = primeros[0].get('nombre')
                        self.manager.transition.direction = 'left'
                        self.manager.current = 'entrenamiento_activo'

                    btn_start = MDFillRoundFlatButton(text="Comenzar ahora", size_hint=(0.4, None), height=dp(44), md_bg_color=(0.1,0.5,0.9,1), on_release=lambda x, dd=d: comenzar_ahora(dd))
                    btn_box.add_widget(btn_toggle)
                    btn_box.add_widget(btn_start)
                    card.add_widget(btn_box)
                    # calcular altura del card para evitar superposición
                    card.height = dp(28) + max(1, len(ejercicios)) * dp(22) + dp(60)
                    self.box.add_widget(card)
                    if estado == 'Completado':
                        completados += 1

            progreso = int((completados / max(1, total_dias)) * 100)
            self.box.add_widget(MDLabel(text=f"Progreso del mes: {progreso}% ({completados}/{total_dias} días completados)", size_hint_y=None, height=dp(26)))

        # Mostrar plan anual (estructura: lista de meses)
        elif isinstance(rutina.get('estructura'), list) and rutina.get('tipo','').lower().find('anual') != -1:
            meses = rutina['estructura']
            total_meses = len(meses)
            dias_completados = 0
            dias_totales = 0
            for mes in meses:
                titulo_mes = MDLabel(text=f"Mes {mes.get('mes')}: {mes.get('descripcion')}", font_style="Subtitle1", size_hint_y=None, height=dp(26))
                self.box.add_widget(titulo_mes)
                for semana in mes.get('semanas', []):
                    self.box.add_widget(MDLabel(text=f"  Semana {semana.get('semana_num')}", font_style="Caption", size_hint_y=None, height=dp(22)))
                    for d in semana.get('dias', []):
                        estado = d.get('estado','Pendiente')
                        ejercicios = d.get('ejercicios', [])
                        card = MDCard(orientation='vertical', padding=dp(8), spacing=dp(6), size_hint_y=None, radius=[14], md_bg_color=(0.06,0.07,0.09,1), line_color=(0.18,0.18,0.18,1))
                        header_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(22))
                        header_box.add_widget(MDLabel(text=f"{d.get('dia')}    {d.get('tiempo','25-35 min')}", font_style="Caption", halign="left"))
                        ic = MDIconButton(icon="check-circle", theme_text_color="Custom", text_color=(0,0.8,0.3,1))
                        ic.opacity = 1 if estado == 'Completado' else 0.12
                        ic.disabled = True
                        header_box.add_widget(ic)
                        card.add_widget(header_box)
                        for ex in ejercicios:
                            card.add_widget(MDLabel(text=f"- {ex.get('nombre')} ({ex.get('series')}x{ex.get('reps')})", font_style="Caption", size_hint_y=None, height=dp(18)))
                        # añadir botón comenzar ahora en el plan anual también
                        btn_start = MDFillRoundFlatButton(text="Comenzar ahora", size_hint=(0.6, None), height=dp(40), md_bg_color=(0.1,0.5,0.9,1), on_release=lambda x, dd=d: (DATOS_USUARIO.update({'ejercicio': dd.get('ejercicios',[{}])[0].get('nombre') if dd.get('ejercicios') else DATOS_USUARIO.get('ejercicio')}), setattr(self.manager, 'transition', self.manager.transition) or self.manager.__setattr__('current','entrenamiento_activo')))
                        card.add_widget(btn_start)
                        # ajustar altura
                        card.height = dp(26) + max(1, len(ejercicios)) * dp(20) + dp(56)
                        self.box.add_widget(card)
                        dias_totales += 1
                        if estado == 'Completado':
                            dias_completados += 1

            porcentaje = int((dias_completados / max(1, dias_totales)) * 100) if dias_totales else 0
            self.box.add_widget(MDLabel(text=f"Progreso anual: {porcentaje}% ({dias_completados}/{dias_totales} días completados)", size_hint_y=None, height=dp(26)))

        self.box.add_widget(Widget(size_hint_y=None, height=dp(12)))
        self.box.add_widget(MDFillRoundFlatButton(text="Ir al Perfil", size_hint=(0.9, None), height=dp(48), pos_hint={"center_x":0.5}, on_release=lambda x: self.ir_perfil()))

    def volver(self):
        self.manager.transition.direction = "right"
        self.manager.current = "perfil"

    def ir_perfil(self):
        self.manager.transition.direction = "left"
        self.manager.current = "perfil"

    def toggle_estado(self, dia_obj):
        # alterna estado entre Pendiente y Completado y salva
        try:
            nuevo = 'Completado' if dia_obj.get('estado') == 'Pendiente' else 'Pendiente'
            dia_obj['estado'] = nuevo
            save_user_data()
            # animación de visto si marcó como completado
            if nuevo == 'Completado':
                try:
                    visto = MDIconButton(icon='check-circle', icon_size='140sp', theme_text_color='Custom', text_color=(0,0.9,0.3,1), pos_hint={'center_x':0.5,'center_y':0.55}, opacity=0)
                    self.layout.add_widget(visto)
                    anim = Animation(opacity=1, duration=0.18) + Animation(opacity=0, duration=0.6)
                    def _on_complete(anim, widget):
                        try:
                            self.layout.remove_widget(widget)
                        except:
                            pass
                    anim.bind(on_complete=_on_complete)
                    anim.start(visto)
                except Exception as e:
                    print('Error mostrando visto:', e)
            self.build_ui()
        except Exception as e:
            print("Error toggle_estado:", e)

    def ir_membresias(self):
        self.manager.transition.direction = 'left'
        self.manager.current = 'membresias'

# ORQUESTADOR CENTRAL
class FlexRexApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = 'Dark'
        self.theme_cls.primary_palette = 'Red'
        # Cargar datos de usuario y aplicar tema guardado
        try:
            load_user_data()
            pal = DATOS_USUARIO.get('tema')
            estilo = DATOS_USUARIO.get('theme_style', 'Dark')
            if pal:
                self.theme_cls.primary_palette = pal
            if estilo:
                self.theme_cls.theme_style = estilo
        except Exception:
            pass
        sm = ScreenManager()
        sm.add_widget(PantallaBienvenida(name='bienvenida'))
        sm.add_widget(PantallaLoginSocial(name='login_social'))
        sm.add_widget(PantallaRegistro(name='registro'))
        sm.add_widget(PantallaSugerenciaPlan(name='sugerencia'))
        sm.add_widget(PantallaEjercicios(name='ejercicios'))
        sm.add_widget(PantallaEntrenamiento(name='entrenamiento_activo'))
        sm.add_widget(PantallaPerfil(name='perfil'))
        sm.add_widget(PantallaProgreso(name='progreso'))
        sm.add_widget(PantallaMembresias(name='membresias'))
        sm.add_widget(PantallaPago(name='pago'))
        sm.add_widget(PantallaConfirmacion(name='confirmacion'))
        sm.add_widget(PantallaRutina(name='rutina'))
        return sm

if __name__ == "__main__":
    FlexRexApp().run()
