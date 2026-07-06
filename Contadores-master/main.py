from kivymd.app import MDApp
from kivy.app import App
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
try:
    from kivy.uix.camera import Camera
except Exception as e:
    Camera = None
    print(f"[FlexRex] Camera no disponible en este dispositivo/compilacion: {e}")
from kivy.uix.widget import Widget
from kivy.uix.gridlayout import GridLayout
from kivy.animation import Animation
from kivy.graphics import Color, Rectangle, Line
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton, MDFillRoundFlatButton
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.textfield import MDTextField
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.utils import platform
import os
import math
import json

# ==========================================
# ACELERÓMETRO (funciona en Android vía Plyer)
# ==========================================
from plyer import accelerometer

# Import necesario para Android (el permiso se pide más adelante, en on_start)
if platform == "android":
    from android.permissions import request_permissions, Permission

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
    "membresia_activa": False
}

COLOR_AMARILLO = (1, 0.84, 0, 1)
COLOR_BLANCO = (1, 1, 1, 1)
CONTENIDO_PLANES = {
    "Premium Mensual": "Incluye:\n- Todos los ejercicios\n- Historial ilimitado\n- Rutinas personalizadas con IA",
    "Premium Anual": "Incluye:\n- Todo lo del plan mensual\n- Ahorro del 33%\n- Soporte prioritario",
    "Gratis": "Incluye:\n- 3 ejercicios básicos\n- Historial limitado\n- Sin rutinas personalizadas"
}

def get_userdata_path():
    if platform == "android" and App.get_running_app():
        base_dir = App.get_running_app().user_data_dir
    else:
        base_dir = os.path.dirname(__file__)
    os.makedirs(base_dir, exist_ok=True)
    return os.path.join(base_dir, "userdata.json")


def save_user_data():
    path = get_userdata_path()
    try:
        with open(path, "w", encoding="utf-8") as archivo:
            json.dump(DATOS_USUARIO, archivo, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[FlexRex] Error guardando userdata.json: {e}")


def load_user_data():
    path = get_userdata_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as archivo:
                datos = json.load(archivo)
            if isinstance(datos, dict):
                DATOS_USUARIO.update(datos)
        except Exception as e:
            print(f"[FlexRex] Error leyendo userdata.json: {e}")


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

def hacer_texto_ajustable(label):
    """Evita que el texto de un MDLabel se salga de su ancho y se monte sobre widgets vecinos."""
    def actualizar(instancia, valor):
        instancia.text_size = (valor[0], None)
        instancia.texture_update()
        instancia.height = max(instancia.texture_size[1], instancia.height)
    label.bind(size=actualizar)
    label.text_size = (label.width or 1, None)
    return label


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
        
        layout_pantalla = FloatLayout()
        
        # Imagen de fondo a pantalla completa
        ruta_manual = "logo_cropped.png"
        self.logo = Image(
            source=ruta_manual, 
            size_hint=(1, 1),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            fit_mode="contain"
        )
        layout_pantalla.add_widget(self.logo)
        
        # Overlay oscuro semitransparente para legibilidad
        from kivy.uix.widget import Widget
        from kivy.graphics import Color, Rectangle
        overlay = Widget(size_hint=(1, 1))
        with overlay.canvas:
            Color(0, 0, 0, 0.4)
            self.overlay_rect = Rectangle(pos=overlay.pos, size=overlay.size)
        overlay.bind(pos=lambda w, p: setattr(self.overlay_rect, 'pos', p),
                     size=lambda w, s: setattr(self.overlay_rect, 'size', s))
        layout_pantalla.add_widget(overlay)
        
        # Título FLEX-REX en la parte superior
        layout_pantalla.add_widget(MDLabel(
            text="FLEX-REX", halign="center", font_style="H3", bold=True,
            theme_text_color="Custom", text_color=(1, 1, 1, 1),
            size_hint=(1, None), height=50,
            pos_hint={"center_x": 0.5, "top": 0.92}
        ))
        layout_pantalla.add_widget(MDLabel(
            text="Tu entrenador personal dinámico", halign="center", font_style="Subtitle1",
            theme_text_color="Custom", text_color=(0.85, 0.85, 0.85, 1),
            size_hint=(1, None), height=30,
            pos_hint={"center_x": 0.5, "top": 0.85}
        ))
        
        # Botón "Comenzar Ahora" grande y centrado abajo
        self.btn_comenzar = MDFillRoundFlatButton(
            text="Comenzar Ahora", 
            pos_hint={"center_x": 0.5, "center_y": 0.18},
            size_hint=(0.8, None), height=55,
            md_bg_color=(1, 0.2, 0.2, 1), 
            font_size="18sp",
            on_release=lambda x: self.ir_a_registro()
        )
        layout_pantalla.add_widget(self.btn_comenzar)
        self.animar_boton_pulso()
        
        # Botón "Ver Planes Premium" con recuadro/borde
        btn_planes = MDFillRoundFlatButton(
            text="Ver Planes Premium",
            pos_hint={"center_x": 0.5, "center_y": 0.08},
            size_hint=(0.8, None), height=48,
            md_bg_color=COLOR_AMARILLO,
            text_color=COLOR_BLANCO,
            font_size="16sp",
            on_release=lambda x: self.ir_a_membresias()
        )
        layout_pantalla.add_widget(btn_planes)
        
        # Botón perfil
        btn_perfil = MDIconButton(
            icon="account-circle", 
            pos_hint={"right": 0.95, "top": 0.98},
            theme_text_color="Custom", text_color=(1, 1, 1, 1),
            on_release=lambda x: self.ir_a_perfil()
        )
        layout_pantalla.add_widget(btn_perfil)
        
        self.add_widget(layout_pantalla)
        animar_botones_en_layout(layout_pantalla)

    def animar_logo_dinamico(self):
        pass  # Logo is now full-screen background, no animation needed

    def animar_boton_pulso(self):
        animar_boton_en_movimiento(self.btn_comenzar)

    def ir_a_registro(self):
        self.manager.transition.direction = "left"
        self.manager.current = "registro"

    def ir_a_membresias(self):
        self.manager.transition.direction = "left"
        self.manager.current = "membresias"

    def ir_a_perfil(self):
        self.manager.transition.direction = "left"
        self.manager.current = "perfil"


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
        
        self.btn_sexo_dropdown = MDFillRoundFlatButton(
            text=DATOS_USUARIO["sexo"], size_hint=(1, None), height=45, 
            md_bg_color=(0.2, 0.2, 0.2, 1), on_release=self.abrir_menu_sexo
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
            self.container_plan.height = 0
            self.container_botones.height = 220
            self.container_botones.opacity = 1
            self.animar_botones_cascada()

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
        
        self.container_plan = BoxLayout(orientation='vertical', size_hint_y=None, height=0)
        layout_principal.add_widget(self.container_plan)
        
        self.container_botones = GridLayout(cols=3, spacing=15, size_hint_y=None, height=180)
        
        def crear_tarjeta_ejercicio(titulo, desc, img_source, color, callback):
            card = MDCard(orientation="vertical", padding=10, spacing=10, size_hint_y=None, height=180, md_bg_color=(0.15, 0.15, 0.15, 1), radius=[20])
            img = Image(source=img_source, allow_stretch=True, size_hint_y=0.6)
            card.add_widget(img)
            text_box = BoxLayout(orientation="vertical", size_hint_y=0.4)
            text_box.add_widget(MDLabel(text=titulo, font_style="Subtitle2", bold=True, theme_text_color="Primary", halign="center"))
            text_box.add_widget(MDLabel(text=desc, font_style="Caption", theme_text_color="Secondary", halign="center"))
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
        self.container_plan.height = 110

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
        tutorial_placeholder = BoxLayout(orientation='vertical', padding=12, spacing=8, size_hint_x=0.4)
        tutorial_placeholder.add_widget(hacer_texto_ajustable(MDLabel(text="Video de tutorial no disponible en Android", halign="center", theme_text_color="Secondary", size_hint_y=None, height=40)))
        tutorial_placeholder.add_widget(hacer_texto_ajustable(MDLabel(text="Usa el botón de simulación para practicar repeticiones reales desde tu teléfono.", halign="center", theme_text_color="Secondary", size_hint_y=None, height=50)))
        tutorial_placeholder.add_widget(hacer_texto_ajustable(MDLabel(text="Sigue las instrucciones y aumenta la carga poco a poco.", halign="center", theme_text_color="Secondary", size_hint_y=None, height=50)))
        contenido.add_widget(tutorial_placeholder)
        
        pasos_layout = BoxLayout(orientation='vertical', spacing=4, size_hint_x=0.6)
        pasos = instrucciones.get(ejercicio, ["Selecciona un ejercicio para ver instrucciones."])
        for paso in pasos:
            pasos_layout.add_widget(hacer_texto_ajustable(MDLabel(text=paso, font_style="Caption", theme_text_color="Primary", size_hint_y=None, height=35)))
        contenido.add_widget(pasos_layout)
        
        card_vid.add_widget(contenido)
        self.container_video.add_widget(card_vid)

    def comenzar_entrenamiento_camara(self):
        if not DATOS_USUARIO["ejercicio"]:
            dialog = MDDialog(title="⚠️ Error", text="Por favor, selecciona un ejercicio antes de encender la cámara.", buttons=[MDFlatButton(text="Entendido", on_release=lambda x: dialog.dismiss())])
            dialog.open()
            return
        self.manager.transition.direction = "left"
        self.manager.current = "entrenamiento_activo"


# PANTALLA 5: DETECCIÓN EN TIEMPO REAL (Cámara real + Acelerómetro)
class PantallaEntrenamiento(Screen):
    # Umbrales de movimiento por ejercicio (m/s^2 sobre la gravedad ~9.8)
    UMBRALES = {
        "Flexiones":   {"pico": 12.5, "valle": 8.5},
        "Dominadas":   {"pico": 13.0, "valle": 8.0},
        "Sentadillas": {"pico": 13.5, "valle": 8.5},
    }

    def on_enter(self, *args):
        ejercicio = DATOS_USUARIO["ejercicio"] or "Sentadillas"
        self.lbl_ejercicio.text = f"Entrenando: {str(ejercicio).upper()}"
        self.contador_reps = 0
        self.lbl_contador.text = "0"
        self.estado_fase = "arriba"
        self.umbral = self.UMBRALES.get(ejercicio, self.UMBRALES["Sentadillas"])

        self.scanner_text.text = "Escaneando cuerpo con IA..."
        self.scanner_line_y = 0
        self.scanner_event = Clock.schedule_interval(self.actualizar_escaneo, 1 / 30.0)

        try:
            accelerometer.enable()
            self.sensor_disponible = True
        except Exception as e:
            self.sensor_disponible = False
            self.lbl_ejercicio.text = "⚠️ Sensor no disponible, usa los botones manuales"
            print(f"Error al iniciar el acelerómetro: {e}")

        self.activar_camara()

        Clock.schedule_interval(self.leer_sensor, 1.0 / 20.0)

    def activar_camara(self):
        if Camera is None:
            return
        try:
            if self.camera_widget is None:
                self.camera_widget = Camera(play=False, size_hint=(0.95, 0.95), pos_hint={"center_x": 0.5, "center_y": 0.5}, resolution=(640, 480))
                scanner_container = self.scanner_widget.parent
                scanner_container.add_widget(self.camera_widget, index=len(scanner_container.children))
            self.camera_widget.play = True
            self.camera_disponible = True
        except Exception as e:
            self.camera_disponible = False
            print(f"[FlexRex] No se pudo activar la camara: {e}")

    def on_leave(self, *args):
        Clock.unschedule(self.leer_sensor)
        if hasattr(self, 'scanner_event') and self.scanner_event:
            self.scanner_event.cancel()
            self.scanner_event = None
        try:
            accelerometer.disable()
        except Exception:
            pass
        try:
            if self.camera_widget is not None:
                self.camera_widget.play = False
        except Exception:
            pass

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sensor_disponible = False
        self.scanner_line_y = 0
        layout = FloatLayout()

        scanner_container = FloatLayout(size_hint=(1, 0.75), pos_hint={"center_x": 0.5, "top": 0.98})

        # Espacio reservado para la cámara real; se crea de forma segura en on_enter,
        # así que si falla, la app sigue funcionando con el efecto simulado de respaldo.
        self.camera_widget = None
        self.camera_disponible = False

        self.scanner_widget = Widget(size_hint=(0.95, 0.95), pos_hint={"center_x": 0.5, "center_y": 0.5})
        with self.scanner_widget.canvas:
            Color(0.08, 0.08, 0.12, 1)
            self.scanner_bg = Rectangle(pos=self.scanner_widget.pos, size=self.scanner_widget.size)
            Color(0, 0.5, 1, 0.25)
            self.scanner_line = Rectangle(pos=(self.scanner_widget.x, self.scanner_widget.y), size=(self.scanner_widget.width, 6))
            Color(0.5, 0.8, 1, 0.18)
            self.scanner_outline = Line(rectangle=(self.scanner_widget.x, self.scanner_widget.y, self.scanner_widget.width, self.scanner_widget.height), width=1.6, dash_length=10, dash_offset=5)
        self.scanner_widget.bind(pos=self._update_scanner_canvas, size=self._update_scanner_canvas)
        scanner_container.add_widget(self.scanner_widget)

        self.scanner_text = MDLabel(
            text="Escaneando cuerpo con IA...",
            halign="center",
            theme_text_color="Custom",
            text_color=(0.5, 0.9, 1, 1),
            size_hint=(1, None),
            height=30,
            pos_hint={"center_x": 0.5, "y": 0.03}
        )
        scanner_container.add_widget(self.scanner_text)
        layout.add_widget(scanner_container)

        panel_inferior = BoxLayout(orientation='vertical', size_hint=(1, 0.25), pos_hint={"x": 0, "y": 0}, padding=15, spacing=8)

        fondo_panel = MDCard(orientation='vertical', padding=12, spacing=8, md_bg_color=(0.1, 0.1, 0.1, 0.85), radius=[20, 20, 0, 0])

        self.lbl_ejercicio = MDLabel(text="Iniciando componentes...", halign="center", font_style="H6", theme_text_color="Custom", text_color=(0, 0.8, 1, 1))
        fondo_panel.add_widget(self.lbl_ejercicio)

        layout_numeros = BoxLayout(orientation='horizontal', padding=[20, 0, 20, 0])
        layout_numeros.add_widget(MDLabel(text="REPETICIONES:", font_style="H6", halign="left", theme_text_color="Secondary"))
        self.lbl_contador = MDLabel(text="0", font_style="H2", bold=True, halign="right", theme_text_color="Custom", text_color=(0, 0.8, 0.3, 1))
        layout_numeros.add_widget(self.lbl_contador)
        fondo_panel.add_widget(layout_numeros)

        layout_manual = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=45)
        btn_menos = MDFillRoundFlatButton(text="- 1", md_bg_color=(0.3, 0.3, 0.3, 1), size_hint=(0.5, 1), on_release=lambda x: self.ajustar_manual(-1))
        btn_mas = MDFillRoundFlatButton(text="+ 1", md_bg_color=(0.1, 0.5, 0.2, 1), size_hint=(0.5, 1), on_release=lambda x: self.ajustar_manual(1))
        layout_manual.add_widget(btn_menos)
        layout_manual.add_widget(btn_mas)
        fondo_panel.add_widget(layout_manual)

        btn_simular = MDFillRoundFlatButton(text="Simular Repetición", md_bg_color=(0.1, 0.5, 0.8, 1), size_hint=(1, None), height=50, on_release=lambda x: self.simular_repeticion())
        fondo_panel.add_widget(btn_simular)

        btn_terminar = MDFillRoundFlatButton(text="Finalizar Entrenamiento", md_bg_color=(1, 0.2, 0.2, 1), size_hint=(1, None), height=50, on_release=lambda x: self.terminar())
        fondo_panel.add_widget(btn_terminar)

        panel_inferior.add_widget(fondo_panel)

        layout.add_widget(panel_inferior)
        self.add_widget(layout)
        animar_botones_en_layout(layout)

    def _update_scanner_canvas(self, *args):
        self.scanner_bg.pos = self.scanner_widget.pos
        self.scanner_bg.size = self.scanner_widget.size
        self.scanner_line.size = (self.scanner_widget.width, 6)
        self.scanner_line.pos = (self.scanner_widget.x, self.scanner_widget.y + self.scanner_line_y)
        self.scanner_outline.rectangle = (self.scanner_widget.x, self.scanner_widget.y, self.scanner_widget.width, self.scanner_widget.height)

    def actualizar_escaneo(self, dt):
        if not self.scanner_widget:
            return
        self.scanner_line_y += self.scanner_widget.height * dt * 0.4
        if self.scanner_line_y > self.scanner_widget.height:
            self.scanner_line_y = 0
        self.scanner_line.pos = (self.scanner_widget.x, self.scanner_widget.y + self.scanner_line_y)

    def simular_repeticion(self):
        self.contador_reps = max(0, getattr(self, 'contador_reps', 0) + 1)
        self.lbl_contador.text = str(self.contador_reps)

    def ajustar_manual(self, delta):
        self.contador_reps = max(0, self.contador_reps + delta)
        self.lbl_contador.text = str(self.contador_reps)

    def leer_sensor(self, dt):
        if not self.sensor_disponible:
            return
        try:
            valores = accelerometer.acceleration
            if not valores or valores[0] is None:
                return
            x, y, z = valores[0], valores[1], valores[2]
            magnitud = math.sqrt(x * x + y * y + z * z)

            if magnitud > self.umbral["pico"] and self.estado_fase == "abajo":
                self.contador_reps += 1
                self.lbl_contador.text = str(self.contador_reps)
                self.estado_fase = "arriba"
            elif magnitud < self.umbral["valle"]:
                self.estado_fase = "abajo"
        except Exception as e:
            pass

    def terminar(self):
        dialog = MDDialog(
            title="¡Buen Trabajo!",
            text=f"Completaste un total de {self.contador_reps} repeticiones.",
            buttons=[MDFlatButton(text="Volver", on_release=lambda x: self.salir_limpio(dialog))]
        )
        dialog.open()
        save_user_data()

    def salir_limpio(self, dialogo):
        dialogo.dismiss()
        self.manager.transition.direction = "right"
        self.manager.current = "bienvenida"


# ==========================================
# NUEVAS PANTALLAS: PERFIL, PROGRESO, MEMBRESÍAS, PAGO, CONFIRMACIÓN
# ==========================================

class PantallaPerfil(Screen):
    def on_enter(self, *args):
        self.lbl_nombre.text = DATOS_USUARIO["nombre"] if DATOS_USUARIO["nombre"] else "Usuario"
        self.lbl_detalles.text = f"{DATOS_USUARIO['edad']} años | {DATOS_USUARIO['peso']} kg | {DATOS_USUARIO['altura']} cm"
        self.lbl_membresia.text = f"Membresía: {DATOS_USUARIO['membresia']}"
        self.lbl_membresia.text_color = (1, 0.84, 0, 1) if DATOS_USUARIO["membresia_activa"] else (0.7, 0.7, 0.7, 1)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = FloatLayout()
        box = BoxLayout(orientation='vertical', padding=25, spacing=20)
        
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        btn_back = MDIconButton(icon="arrow-left", on_release=lambda x: self.volver())
        header.add_widget(btn_back)
        header.add_widget(MDLabel(text="Mi Perfil", font_style="H5", bold=True))
        box.add_widget(header)

        avatar_box = BoxLayout(orientation='vertical', size_hint_y=None, height=150, spacing=10)
        avatar_box.add_widget(MDIconButton(icon="account-circle", icon_size="80sp", pos_hint={"center_x": 0.5}, theme_text_color="Custom", text_color=(1, 0.2, 0.2, 1)))
        self.lbl_nombre = MDLabel(text="Usuario", halign="center", font_style="H5", bold=True)
        self.lbl_detalles = MDLabel(text="-", halign="center", font_style="Subtitle1", theme_text_color="Secondary")
        self.lbl_membresia = MDLabel(text="Membresía: Gratis", halign="center", font_style="Subtitle2", theme_text_color="Custom", text_color=(0.7, 0.7, 0.7, 1))
        
        avatar_box.add_widget(self.lbl_nombre)
        avatar_box.add_widget(self.lbl_detalles)
        avatar_box.add_widget(self.lbl_membresia)
        box.add_widget(avatar_box)

        stats_card = MDCard(orientation='horizontal', padding=15, size_hint_y=None, height=80, md_bg_color=(0.15, 0.15, 0.15, 1), radius=[15])
        
        stat1 = BoxLayout(orientation='vertical')
        stat1.add_widget(MDLabel(text="12", halign="center", font_style="H6", text_color=(0, 0.8, 1, 1), theme_text_color="Custom"))
        stat1.add_widget(MDLabel(text="Sesiones", halign="center", font_style="Caption"))
        
        stat2 = BoxLayout(orientation='vertical')
        stat2.add_widget(MDLabel(text="5", halign="center", font_style="H6", text_color=(1, 0.5, 0, 1), theme_text_color="Custom"))
        stat2.add_widget(MDLabel(text="Racha (días)", halign="center", font_style="Caption"))

        stats_card.add_widget(stat1)
        stats_card.add_widget(stat2)
        box.add_widget(stats_card)

        box.add_widget(MDFillRoundFlatButton(text="Ver Mi Progreso", size_hint=(1, None), height=50, md_bg_color=(0.2, 0.2, 0.2, 1), on_release=lambda x: self.ir_a_progreso()))
        box.add_widget(MDFillRoundFlatButton(text="Gestionar Membresía", size_hint=(1, None), height=50, md_bg_color=(1, 0.84, 0, 1), text_color=(0, 0, 0, 1), on_release=lambda x: self.ir_a_membresias()))
        
        box.add_widget(MDLabel(text="", size_hint_y=1))
        
        layout.add_widget(box)
        self.add_widget(layout)
        animar_botones_en_layout(layout)

    def volver(self):
        self.manager.transition.direction = "right"
        self.manager.current = "bienvenida"

    def ir_a_progreso(self):
        self.manager.transition.direction = "left"
        self.manager.current = "progreso"

    def ir_a_membresias(self):
        self.manager.transition.direction = "left"
        self.manager.current = "membresias"

class PantallaProgreso(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = FloatLayout()
        box = BoxLayout(orientation='vertical', padding=25, spacing=20)
        
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        btn_back = MDIconButton(icon="arrow-left", on_release=lambda x: self.volver())
        header.add_widget(btn_back)
        header.add_widget(MDLabel(text="Estadísticas", font_style="H5", bold=True))
        box.add_widget(header)

        grid = BoxLayout(orientation='horizontal', size_hint_y=None, height=100, spacing=15)
        
        card_reps = MDCard(orientation='vertical', padding=10, md_bg_color=(0.15, 0.15, 0.15, 1), radius=[15])
        card_reps.add_widget(MDIconButton(icon="arm-flex", pos_hint={"center_x": 0.5}, theme_text_color="Custom", text_color=(1, 0.2, 0.2, 1)))
        card_reps.add_widget(MDLabel(text="345", halign="center", font_style="H5", bold=True))
        card_reps.add_widget(MDLabel(text="Reps Totales", halign="center", font_style="Caption"))
        
        card_dias = MDCard(orientation='vertical', padding=10, md_bg_color=(0.15, 0.15, 0.15, 1), radius=[15])
        card_dias.add_widget(MDIconButton(icon="calendar-check", pos_hint={"center_x": 0.5}, theme_text_color="Custom", text_color=(0, 0.8, 0.3, 1)))
        card_dias.add_widget(MDLabel(text="Lunes", halign="center", font_style="H5", bold=True))
        card_dias.add_widget(MDLabel(text="Mejor Día", halign="center", font_style="Caption"))

        grid.add_widget(card_reps)
        grid.add_widget(card_dias)
        box.add_widget(grid)

        box.add_widget(MDLabel(text="Últimas Sesiones", font_style="Subtitle1", bold=True, size_hint_y=None, height=30))
        historial = MDCard(orientation='vertical', padding=15, spacing=10, md_bg_color=(0.1, 0.1, 0.1, 1), radius=[10], size_hint_y=None, height=120)
        historial.add_widget(MDLabel(text="Hoy: Flexiones - 45 reps", theme_text_color="Secondary"))
        historial.add_widget(MDLabel(text="Ayer: Sentadillas - 60 reps", theme_text_color="Secondary"))
        historial.add_widget(MDLabel(text="Hace 3 días: Dominadas - 20 reps", theme_text_color="Secondary"))
        box.add_widget(historial)

        msg = MDCard(md_bg_color=(1, 0.5, 0, 0.2), padding=15, radius=[10], size_hint_y=None, height=80)
        msg.add_widget(MDLabel(text="¡Estás en el 10% superior de usuarios activos esta semana! Sigue así.", theme_text_color="Custom", text_color=(1, 0.6, 0, 1), halign="center", font_style="Subtitle2"))
        box.add_widget(msg)

        box.add_widget(MDLabel(text="", size_hint_y=1))
        layout.add_widget(box)
        self.add_widget(layout)
        animar_botones_en_layout(layout)

    def volver(self):
        self.manager.transition.direction = "right"
        self.manager.current = "perfil"

class PantallaMembresias(Screen):
    def on_enter(self, *args):
        self.actualizar_ui()

    def actualizar_ui(self):
        self.card_gratis.md_bg_color = (0.15, 0.15, 0.15, 1)
        self.card_mensual.md_bg_color = (0.15, 0.15, 0.25, 1)
        self.card_anual.md_bg_color = (0.25, 0.2, 0.1, 1)
        
        self.btn_gratis.text = "Seleccionar"
        self.btn_mensual.text = "Seleccionar"
        self.btn_anual.text = "Seleccionar"

        if DATOS_USUARIO["membresia"] == "Gratis":
            self.card_gratis.md_bg_color = (0.3, 0.3, 0.3, 1)
            self.btn_gratis.text = "Plan Actual"
        elif DATOS_USUARIO["membresia"] == "Premium Mensual":
            self.card_mensual.md_bg_color = (0.2, 0.3, 0.5, 1)
            self.btn_mensual.text = "Plan Actual"
        elif DATOS_USUARIO["membresia"] == "Premium Anual":
            self.card_anual.md_bg_color = (0.5, 0.4, 0.1, 1)
            self.btn_anual.text = "Plan Actual"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = FloatLayout()
        scroll = ScrollView(size_hint=(1, 1))
        box = BoxLayout(orientation='vertical', padding=20, spacing=15, size_hint_y=None)
        box.bind(minimum_height=box.setter('height'))
        
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        btn_back = MDIconButton(icon="arrow-left", on_release=lambda x: self.volver())
        header.add_widget(btn_back)
        header.add_widget(MDLabel(text="Planes Premium", font_style="H5", bold=True))
        box.add_widget(header)

        self.card_gratis = MDCard(orientation='horizontal', padding=14, spacing=14, size_hint_y=None, height=250, radius=[20])
        self.card_gratis.add_widget(Image(source='img_plan_gratis.png', allow_stretch=True, keep_ratio=True, size_hint=(0.48, 1)))
        info_gratis = BoxLayout(orientation='vertical', spacing=8, size_hint_x=0.52)
        info_gratis.add_widget(MDLabel(text="Básico", font_style="H6"))
        info_gratis.add_widget(MDLabel(text="$0.00 / mes", font_style="H5", bold=True))
        info_gratis.add_widget(MDLabel(text="3 Ejercicios básicos\nHistorial limitado\nSin rutinas personalizadas", font_style="Caption"))
        self.btn_gratis = MDFillRoundFlatButton(text="Seleccionar", size_hint=(1, None), height=46, md_bg_color=(0.4, 0.4, 0.4, 1), on_release=lambda x: self.seleccionar_plan("Gratis", 0))
        info_gratis.add_widget(self.btn_gratis)
        self.card_gratis.add_widget(info_gratis)
        box.add_widget(self.card_gratis)

        self.card_mensual = MDCard(orientation='horizontal', padding=14, spacing=14, size_hint_y=None, height=250, radius=[20])
        self.card_mensual.add_widget(Image(source='img_plan_mensual.png', allow_stretch=True, keep_ratio=True, size_hint=(0.48, 1)))
        info_mensual = BoxLayout(orientation='vertical', spacing=8, size_hint_x=0.52)
        info_mensual.add_widget(MDLabel(text="Premium Mensual", font_style="H6", text_color=(0, 0.8, 1, 1), theme_text_color="Custom"))
        info_mensual.add_widget(MDLabel(text="$9.99 / mes", font_style="H5", bold=True))
        info_mensual.add_widget(MDLabel(text="Todos los ejercicios\nHistorial ilimitado\nRutinas IA", font_style="Caption"))
        self.btn_mensual = MDFillRoundFlatButton(text="Seleccionar", size_hint=(1, None), height=46, md_bg_color=(0, 0.5, 0.8, 1), on_release=lambda x: self.seleccionar_plan("Premium Mensual", 9.99))
        info_mensual.add_widget(self.btn_mensual)
        self.card_mensual.add_widget(info_mensual)
        box.add_widget(self.card_mensual)

        self.card_anual = MDCard(orientation='horizontal', padding=14, spacing=14, size_hint_y=None, height=270, radius=[20])
        self.card_anual.add_widget(Image(source='img_plan_anual.png', allow_stretch=True, keep_ratio=True, size_hint=(0.48, 1)))
        info_anual = BoxLayout(orientation='vertical', spacing=8, size_hint_x=0.52)
        badge = MDLabel(text="MEJOR VALOR", font_style="Caption", bold=True, text_color=(1, 0.84, 0, 1), theme_text_color="Custom")
        info_anual.add_widget(badge)
        info_anual.add_widget(MDLabel(text="Premium Anual", font_style="H6", text_color=(1, 0.84, 0, 1), theme_text_color="Custom"))
        info_anual.add_widget(MDLabel(text="$79.99 / año", font_style="H5", bold=True))
        info_anual.add_widget(MDLabel(text="Todo lo mensual\nAhorra un 33%\nSoporte prioritario", font_style="Caption"))
        self.btn_anual = MDFillRoundFlatButton(text="Seleccionar", size_hint=(1, None), height=46, md_bg_color=(0.8, 0.7, 0, 1), on_release=lambda x: self.seleccionar_plan("Premium Anual", 79.99))
        info_anual.add_widget(self.btn_anual)
        self.card_anual.add_widget(info_anual)
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
            self.actualizar_ui()
            dialog = MDDialog(title="Plan Actualizado", text="Has vuelto al plan Gratis.", buttons=[MDFlatButton(text="OK", on_release=lambda x: dialog.dismiss())])
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
        self.lbl_contenido_plan.text = CONTENIDO_PLANES.get(plan, "Incluye beneficios premium de FLEX-REX.")
        self.txt_nombre.text = ""
        self.txt_tarjeta.text = ""
        self.txt_fecha.text = ""
        self.txt_cvv.text = ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = FloatLayout()
        box = BoxLayout(orientation='vertical', padding=25, spacing=15)
        
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        btn_back = MDIconButton(icon="arrow-left", on_release=lambda x: self.volver())
        header.add_widget(btn_back)
        header.add_widget(MDLabel(text="Pago Seguro", font_style="H5", bold=True))
        box.add_widget(header)

        self.lbl_resumen = MDLabel(text="Pagando: Plan", font_style="Subtitle1", text_color=(0, 0.8, 0.3, 1), theme_text_color="Custom", size_hint_y=None, height=30)
        box.add_widget(self.lbl_resumen)

        card_contenido = MDCard(
            orientation="vertical",
            padding=15,
            spacing=6,
            md_bg_color=(0.12, 0.12, 0.16, 1),
            radius=[15],
            size_hint_y=None,
            height=120
        )
        card_contenido.add_widget(MDLabel(
            text="Contenido del plan",
            font_style="Subtitle1",
            bold=True,
            theme_text_color="Custom",
            text_color=(1, 0.84, 0, 1),
            size_hint_y=None,
            height=28
        ))
        self.lbl_contenido_plan = MDLabel(
            text="",
            font_style="Caption",
            theme_text_color="Primary"
        )
        card_contenido.add_widget(self.lbl_contenido_plan)
        box.add_widget(card_contenido)

        preview = MDCard(md_bg_color=(0.1, 0.1, 0.2, 1), radius=[15], size_hint_y=None, height=150, padding=20, orientation="vertical")
        preview.add_widget(MDIconButton(icon="integrated-circuit", theme_text_color="Custom", text_color=(1, 0.84, 0, 1)))
        preview.add_widget(MDLabel(text="**** **** **** ****", font_style="H5", theme_text_color="Secondary"))
        
        row_prev = BoxLayout(orientation="horizontal")
        row_prev.add_widget(MDLabel(text="TITULAR", font_style="Caption"))
        row_prev.add_widget(MDLabel(text="MM/AA", font_style="Caption", halign="right"))
        preview.add_widget(row_prev)
        box.add_widget(preview)

        self.txt_nombre = MDTextField(hint_text="Nombre del Titular", mode="rectangle", icon_left="account", size_hint_y=None, height=50)
        self.txt_tarjeta = MDTextField(hint_text="Número de Tarjeta", mode="rectangle", icon_left="credit-card", size_hint_y=None, height=50, max_text_length=16)
        
        row_fechas = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=50)
        self.txt_fecha = MDTextField(hint_text="MM/AA", mode="rectangle")
        self.txt_cvv = MDTextField(hint_text="CVV", mode="rectangle", max_text_length=3, password=True)
        row_fechas.add_widget(self.txt_fecha)
        row_fechas.add_widget(self.txt_cvv)

        box.add_widget(self.txt_nombre)
        box.add_widget(self.txt_tarjeta)
        box.add_widget(row_fechas)

        btn_pagar = MDFillRoundFlatButton(text="Procesar Pago", icon="lock", size_hint=(1, None), height=50, md_bg_color=(0, 0.7, 0.3, 1), on_release=lambda x: self.procesar_pago())
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
        
        DATOS_USUARIO["membresia"] = DATOS_USUARIO.get("plan_temp", "Premium")
        DATOS_USUARIO["membresia_activa"] = True
        self.manager.transition.direction = "left"
        self.manager.current = "confirmacion"

class PantallaConfirmacion(Screen):
    def on_enter(self, *args):
        self.lbl_plan.text = f"Plan Activado: {DATOS_USUARIO['membresia']}"
        self.lbl_beneficios.text = CONTENIDO_PLANES.get(DATOS_USUARIO["membresia"], "Beneficios premium activados.")
        self.animar_check()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = FloatLayout()
        box = BoxLayout(orientation='vertical', padding=30, spacing=20)
        
        box.add_widget(MDLabel(text="", size_hint_y=0.2))

        self.icon_check = MDIconButton(
            icon="check-circle", 
            icon_size="100sp", 
            theme_text_color="Custom", 
            text_color=(0, 0.8, 0.3, 1),
            pos_hint={"center_x": 0.5},
            size_hint=(None, None), size=(120, 120)
        )
        box.add_widget(self.icon_check)
        box.add_widget(MDLabel(text="Pago realizado con exito", halign="center", font_style="H4", bold=True))

        box.add_widget(MDLabel(text="¡Pago Exitoso!", halign="center", font_style="H4", bold=True))
        self.lbl_plan = MDLabel(text="Plan Activado: -", halign="center", font_style="Subtitle1", theme_text_color="Secondary")
        box.add_widget(self.lbl_plan)

        card_beneficios = MDCard(
            orientation="vertical",
            padding=18,
            spacing=8,
            md_bg_color=(0.12, 0.12, 0.16, 1),
            radius=[15],
            size_hint_y=None,
            height=145
        )
        card_beneficios.add_widget(MDLabel(
            text="Todo lo que recibes",
            halign="center",
            font_style="Subtitle1",
            bold=True,
            theme_text_color="Custom",
            text_color=(1, 0.84, 0, 1),
            size_hint_y=None,
            height=30
        ))
        self.lbl_beneficios = MDLabel(
            text="",
            halign="center",
            font_style="Caption",
            theme_text_color="Primary"
        )
        card_beneficios.add_widget(self.lbl_beneficios)
        box.add_widget(card_beneficios)

        box.add_widget(MDLabel(text="Gracias por confiar en FLEX-REX. Disfruta de tus nuevos beneficios premium.", halign="center", font_style="Body2", theme_text_color="Secondary"))

        box.add_widget(MDLabel(text="", size_hint_y=0.2))

        btn_comenzar = MDFillRoundFlatButton(text="Comenzar a Entrenar", size_hint=(1, None), height=50, md_bg_color=(1, 0.2, 0.2, 1), on_release=lambda x: self.ir_inicio())
        box.add_widget(btn_comenzar)

        layout.add_widget(box)
        self.add_widget(layout)
        animar_botones_en_layout(layout)

    def animar_check(self):
        self.icon_check.icon_size = "10sp"
        anim = Animation(icon_size="100sp", duration=0.6, t='out_bounce')
        anim.start(self.icon_check)

    def ir_inicio(self):
        self.manager.transition.direction = "right"
        self.manager.current = "bienvenida"

# ORQUESTADOR CENTRAL
class FlexRexApp(MDApp):
    def build(self):
        load_user_data()
        self.theme_cls.theme_style = 'Dark'
        self.theme_cls.primary_palette = 'Red'
        
        sm = ScreenManager()
        sm.add_widget(PantallaBienvenida(name='bienvenida'))
        sm.add_widget(PantallaRegistro(name='registro'))
        sm.add_widget(PantallaEjercicios(name='ejercicios'))
        sm.add_widget(PantallaEntrenamiento(name='entrenamiento_activo'))
        sm.add_widget(PantallaPerfil(name='perfil'))
        sm.add_widget(PantallaProgreso(name='progreso'))
        sm.add_widget(PantallaMembresias(name='membresias'))
        sm.add_widget(PantallaPago(name='pago'))
        sm.add_widget(PantallaConfirmacion(name='confirmacion'))
        return sm

    def on_start(self):
        if platform == "android":
            request_permissions([Permission.CAMERA])

if __name__ == "__main__":
    FlexRexApp().run()
