"""
╔══════════════════════════════════════════════════════════════╗
║        CAJA REGISTRADORA INTELIGENTE  ·  YOLOv8              ║
║        SENA — Centro de Materiales y Ensayos (CME)           ║
║        Taller Final · Visión por Computadora 2025            ║
╚══════════════════════════════════════════════════════════════╝

DEPENDENCIAS:
    pip install ultralytics opencv-python pillow numpy

MODELO RECOMENDADO PARA i7-9th + 32GB RAM (sin GPU):
    YOLOv8n  →  yolov8n.pt  (más rápido, ~6ms/frame en CPU)
    YOLOv8s  →  yolov8s.pt  (más preciso, ~12ms/frame en CPU)

El modelo se descarga automáticamente al primer uso si no existe.

ESTRUCTURA DE CARPETAS:
    caja_registradora_yolo.py   ← este archivo
    modelos/
        yolov8n.pt              ← descargado automáticamente
"""

import tkinter as tk
from tkinter import ttk, messagebox
import cv2
from PIL import Image, ImageTk, ImageDraw
import threading
import time
import datetime
import os
import sys
import math
import csv


# RUTAS DE ARCHIVOS

def recurso_path(rel_path):
        try:
            base_path = sys._MEIPASS
        except AttributeError:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, rel_path)


# IMPORTACIÓN YOLO

try:
    from ultralytics import YOLO
    YOLO_DISPONIBLE = True
except ImportError:
    YOLO_DISPONIBLE = False
    print("[ERROR] ultralytics no instalado. Ejecuta: pip install ultralytics")

# CONFIGURACIÓN GLOBAL

# Modelo propio a usar
NOMBRE_MODELO = "best.pt"

# Umbral mínimo de confianza para registrar detección
UMBRAL_CONFIANZA = 0.8

# Frames consecutivos necesarios para confirmar y agregar producto
FRAMES_CONFIRMACION = 15

# Frames del video por actualización de UI (ms)
INTERVALO_MS = 40   # ≈ 25fps en pantalla

# Carpeta de modelos
RUTA_MODELOS = "modelos"

# CATÁLOGO DE PRECIOS (COP)
CATALOGO_PRECIOS = {
    "arroz_albar": ("Arroz Albar", 15_000),
    "arroz_roa": ("Arroz Roa", 10_000),
    "Chicle_Doublemint": ("Chicle Doublemint", 1_000),
    "Chicle_Trident": ("Chicle Trident", 2_000),
    "condon_sex": ("Condon", 19_000),
    "corrector_Mimundo": ("Corrector Mimundo", 15_000),
    "corrector_trendy": ("Corrector Trendy", 14_000),
    "delineador_karite": ("Delineador Karite", 20_000),
    "desodorante_axe": ("Desodorante Axe", 8_000),
    "desodorante_speed": ("Desodorante Speed Stick", 7_000),
    "fruti_Fresa": ("Frutino Fresa", 4_000),
    "fruti_Mora": ("Frutino Mora", 5_000),
    "fruti_pina": ("Frutino Pina", 6_000),
    "galleta_chokis": ("Galletas Chokis", 3_000),
    "galletas_festival": ("Galletas Festival", 2_000),
    "libro_elemento": ("Libro El Elemento", 50_000),
    "libro_poe": ("Libro Edgar Allan Poe", 30_000),
    "mani_bary": ("Mani Bary", 1_000),
    "mani_especial": ("Mani Especial", 2_000),
    "mantequilla_Lilipink": ("Mantequilla Lilipink", 20_000),
    "mantequilla_ummer": ("Mantequilla Ummer", 25_000),
    "mascara_volumen": ("Mascara Volumen", 30_000),
    "masme_italo": ("Masmelos Italo", 5_000),
    "masme_millows": ("Masmelos Millows", 6_000),
    "mia_blush": ("Blush Mia", 27_000),
    "microfono_temu": ("Microfono Temu", 35_000),
    "perfume_asad": ("Perfume Asad", 100_000),
    "perfume_versace": ("Perfume Versace", 150_000),
    "polvo_compacto_samy": ("Polvo Compacto Samy", 75_000),
    "polvo_matte_samy": ("Polvo Matte Samy", 60_000),
    "popetas_queso": ("Popetas Queso", 3_000),
    "rubor_mocmallure": ("Rubor Mocmallure", 14_000),
    "samy_delineador": ("Delineador Samy", 26_000)
}

# CATÁLOGO DE DINERO (COP)
CATALOGO_DINERO = {
    "Moneda_1000": 1_000,
    "Billete_2000": 2_000,
    "Billete_5000": 5_000,
    "Billete_10000": 10_000,
    "Billete_20000": 20_000,
    "Billete_50000": 50_000
}

# PALETA DE COLORES HUD
C_FONDO          = "#0A0E1A"    # azul noche profundo
C_PANEL          = "#0D1425"    # panel ligeramente más claro
C_ACENTO         = "#00E5FF"    # cyan eléctrico
C_VERDE          = "#00FF88"    # verde neón
C_NARANJA        = "#FF6B00"    # naranja advertencia
C_ROJO           = "#FF2D55"    # rojo alerta
C_TEXTO          = "#E8F4FD"    # texto blanco azulado
C_TEXTO_DIM      = "#4A6FA5"    # texto secundario
C_LINEA          = "#1A2744"    # línea separadora
C_VERDE_SENA     = "#39A900"    # verde institucional SENA
C_AMARILLO       = "#FFD700"    # dorado / acento total


# CLASE PRINCIPAL

class CajaRegistradoraYOLO:
    """
    Sistema de caja registradora con detección YOLOv8 en tiempo real.
    Interfaz gráfica HUD cyberpunk con animaciones de carga por objeto.
    """

    def __init__(self, ventana_raiz: tk.Tk):
        self.ventana = ventana_raiz
        self.ventana.title("SENA CME · Caja Registradora YOLO")
        self.ventana.geometry("1400x820")
        self.ventana.configure(bg=C_FONDO)
        self.ventana.resizable(True, True)

        # Estado de detección
        self.modelo_yolo         = None
        self.camara              = None
        self.camara_activa       = False
        self.hilo_deteccion      = None
        self.frame_actual        = None
        self.frame_anotado       = None

        # Detección actual (Lógica Multiobjeto)
        self.contadores_productos = {}
        self.contadores_dinero    = {}
        self.bloqueos_temporales  = {}
        self.frames_ausente = {}
        self.confianza_actual     = 0.0

        # Animación de la barra de carga (Global para el HUD)
        self.progreso_carga       = 0.0
        self.animando_barra       = False

        # Carrito de venta
        self.productos_venta      = {}

        # Variables Tkinter
        self.var_dinero_recibido = tk.StringVar(value="$ 0")
        self.imagen_canvas_ref   = None

        # Construir UI
        self._construir_ui()
        self._cargar_modelo_hilo()
        self._actualizar_reloj()
        self._loop_canvas()


    # CARGA DEL MODELO EN HILO SEPARADO

    def _cargar_modelo_hilo(self):
        """Carga YOLOv8 en un hilo para no bloquear la UI."""
        self._set_estado("⏳  Cargando modelo YOLOv8...", C_AMARILLO)
        hilo = threading.Thread(target=self._cargar_modelo, daemon=True)
        hilo.start()

    def _cargar_modelo(self):
        if not YOLO_DISPONIBLE:
            self.ventana.after(0, lambda: self._set_estado(
                "ERROR: Ultralytics no instalado · pip install ultralytics", C_ROJO))
            return

        os.makedirs(RUTA_MODELOS, exist_ok=True)
        ruta_modelo = recurso_path(os.path.join(RUTA_MODELOS, NOMBRE_MODELO))

        try:
            # Si existe localmente lo usa; si no, Ultralytics lo descarga
            self.modelo_yolo = YOLO(ruta_modelo if os.path.exists(ruta_modelo)
                                    else NOMBRE_MODELO)
            
            # Guardar en carpeta local si fue descargado
            if not os.path.exists(ruta_modelo):
                self.modelo_yolo.export(format="pt")

            self.ventana.after(0, lambda: self._set_estado(
                f"Modelo {NOMBRE_MODELO} listo · CPU inference", C_VERDE))
            self.ventana.after(0, lambda: self.boton_camara.config(state=tk.NORMAL))
        except Exception as e:
            print(f'Error al cargar el modelo: {e}')
            self.ventana.after(0, lambda: self._set_estado(
                f"ERROR al cargar modelo: {e}", C_ROJO))



    # CONSTRUCCIÓN DE LA INTERFAZ

    def _construir_ui(self):
        self._barra_superior()
        contenedor = tk.Frame(self.ventana, bg=C_FONDO)
        contenedor.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 10))
        contenedor.columnconfigure(0, weight=9)
        contenedor.columnconfigure(1, weight=1)
        contenedor.rowconfigure(0, weight=1)

        self._panel_camara(contenedor)
        self._panel_derecho(contenedor)
        self._barra_inferior()

        estilo = ttk.Style()
        estilo.theme_use("clam")

        # CLONAR el layout del scrollbar original
        estilo.layout("Cyber.Vertical.TScrollbar",
                    estilo.layout("Vertical.TScrollbar"))

        # CONFIGURACIÓN
        estilo.configure("Cyber.Vertical.TScrollbar",
            gripcount=0,
            background=C_ACENTO,
            darkcolor=C_ACENTO,
            lightcolor=C_ACENTO,
            troughcolor=C_PANEL,
            bordercolor=C_PANEL,
            arrowcolor=C_ACENTO,
            relief="flat",
            width=8
        )

        estilo.map("Cyber.Vertical.TScrollbar",
            background=[("active", C_VERDE), ("pressed", C_VERDE_SENA)]
        )

        estilo.layout("Cyber.Vertical.TScrollbar",
            [('Vertical.Scrollbar.trough',
            {'children': [('Vertical.Scrollbar.thumb',
                            {'expand': '1', 'sticky': 'nswe'})],
            'sticky': 'ns'})]
        )

    # Barra superior
    def _barra_superior(self):
        barra = tk.Frame(self.ventana, bg=C_PANEL, height=60)
        barra.pack(fill=tk.X)
        barra.pack_propagate(False)

        # Línea neón inferior
        linea = tk.Frame(barra, bg=C_ACENTO, height=2)
        linea.pack(side=tk.BOTTOM, fill=tk.X)

        # Logo / título
        marco_logo = tk.Frame(barra, bg=C_PANEL)
        marco_logo.pack(side=tk.LEFT, padx=18, pady=8)

        tk.Label(marco_logo, text="◈", bg=C_PANEL, fg=C_ACENTO,
                 font=("Courier", 22, "bold")).pack(side=tk.LEFT)
        tk.Label(marco_logo, text="  CAJA REGISTRADORA", bg=C_PANEL, fg=C_TEXTO,
                 font=("Courier", 16, "bold")).pack(side=tk.LEFT)
        tk.Label(marco_logo, text="  ·  YOLOv8", bg=C_PANEL, fg=C_ACENTO,
                 font=("Courier", 16)).pack(side=tk.LEFT)

        # Reloj digital
        self.etiqueta_reloj = tk.Label(barra, text="", bg=C_PANEL, fg=C_ACENTO,
                                        font=("Courier", 13, "bold"))
        self.etiqueta_reloj.pack(side=tk.RIGHT, padx=20)

        tk.Label(barra, text="SENA CME", bg=C_PANEL, fg=C_TEXTO_DIM,
                 font=("Courier", 10)).pack(side=tk.RIGHT, padx=10)

    # Panel de cámara (izquierda)
    def _panel_camara(self, padre):
        marco = tk.Frame(padre, bg=C_PANEL, bd=0)
        marco.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=8)

        # Título del panel
        cab = tk.Frame(marco, bg=C_PANEL)
        cab.pack(fill=tk.X, padx=12, pady=(10, 4))
        tk.Label(cab, text="▷  VISIÓN EN TIEMPO REAL", bg=C_PANEL, fg=C_ACENTO,
                 font=("Courier", 11, "bold")).pack(side=tk.LEFT)
        self.etiqueta_fps = tk.Label(cab, text="-- fps", bg=C_PANEL, fg=C_TEXTO_DIM,
                                      font=("Courier", 10))
        self.etiqueta_fps.pack(side=tk.RIGHT)

        # Canvas de video
        self.lienzo = tk.Canvas(marco, bg="#050810",
                                highlightthickness=1,
                                highlightbackground=C_ACENTO)
        self.lienzo.pack(fill=tk.BOTH, expand=True, padx=12, pady=4)

        # Etiqueta del objeto detectado
        self.etiqueta_objeto = tk.Label(
            marco,
            text="◌  Sin objeto detectado",
            bg=C_PANEL, fg=C_TEXTO_DIM,
            font=("Courier", 13, "bold"),
            pady=6
        )
        self.etiqueta_objeto.pack(fill=tk.X, padx=12)

        # Botón de cámara
        marco_btn = tk.Frame(marco, bg=C_PANEL)
        marco_btn.pack(fill=tk.X, padx=12, pady=(4, 12))

        self.boton_camara = tk.Button(
            marco_btn,
            text="▶  INICIAR CÁMARA",
            command=self._toggle_camara,
            bg=C_VERDE_SENA, fg=C_TEXTO,
            font=("Courier", 11, "bold"),
            relief=tk.FLAT, cursor="hand2",
            padx=20, pady=8,
            state=tk.DISABLED,
            activebackground="#2d7f00"
        )
        self.boton_camara.pack(side=tk.LEFT)

        self.boton_agregar = tk.Button(
            marco_btn,
            text="⊕  FORZAR REGISTRO",
            command=self._forzar_registro,
            bg="#1A2744", fg=C_ACENTO,
            font=("Courier", 10, "bold"),
            relief=tk.FLAT, cursor="hand2",
            padx=14, pady=8,
            state=tk.DISABLED,
            activebackground="#253560"
        )
        self.boton_agregar.pack(side=tk.LEFT, padx=(10, 0))

    # Panel derecho
    def _panel_derecho(self, padre):
        marco = tk.Frame(padre, bg=C_PANEL)
        marco.grid(row=0, column=1, sticky="nsew", pady=8)
        marco.rowconfigure(0, weight=1)
        marco.rowconfigure(1, weight=0)

        self._tabla_productos(marco)
        self._panel_cobro(marco)

    def _tabla_productos(self, padre):
        marco = tk.Frame(padre, bg=C_PANEL)
        marco.grid(row=0, column=0, sticky="nsew", padx=8, pady=(8, 4))

        cab = tk.Frame(marco, bg=C_PANEL)
        cab.pack(fill=tk.X, pady=(4, 8))
        tk.Label(cab, text="▷  CARRITO DE VENTA", bg=C_PANEL, fg=C_ACENTO,
                 font=("Courier", 11, "bold")).pack(side=tk.LEFT)

        # Estilo Treeview oscuro
        estilo = ttk.Style()
        estilo.theme_use("clam")
        estilo.configure("HUD.Treeview",
                         background=C_FONDO,
                         fieldbackground=C_FONDO,
                         foreground=C_TEXTO,
                         rowheight=30,
                         font=("Courier", 10))
        estilo.configure("HUD.Treeview.Heading",
                         background=C_LINEA,
                         foreground=C_ACENTO,
                         font=("Courier", 10, "bold"),
                         relief=tk.FLAT)
        estilo.map("HUD.Treeview",
                   background=[("selected", "#1A3055")],
                   foreground=[("selected", C_ACENTO)])

        cols = ("producto", "cant", "precio", "subtotal")
        self.tabla = ttk.Treeview(marco, columns=cols, show="headings",
                                   style="HUD.Treeview", height=10)
        self.tabla.heading("producto",  text="Producto")
        self.tabla.heading("cant",      text="Cant")
        self.tabla.heading("precio",    text="Precio")
        self.tabla.heading("subtotal",  text="Subtotal")
        self.tabla.column("producto",   width=200, anchor="center")
        self.tabla.column("cant",       width=75, anchor="center")
        self.tabla.column("precio",     width=115, anchor="center")
        self.tabla.column("subtotal",   width=115, anchor="center")

        scroll = ttk.Scrollbar(
            marco,
            orient=tk.VERTICAL,
            command=self.tabla.yview,
            style="Cyber.Vertical.TScrollbar"
        )
        self.tabla.configure(yscrollcommand=scroll.set)
        self.tabla.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Botón quitar
        tk.Button(
            padre, text="⊖  QUITAR SELECCIONADO",
            command=self._quitar_seleccionado,
            bg="#1A0E0E", fg=C_ROJO,
            font=("Courier", 9, "bold"),
            relief=tk.FLAT, cursor="hand2", pady=5
        ).grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 4))

    def _panel_cobro(self, padre):
        marco = tk.Frame(padre, bg=C_PANEL,
                         highlightthickness=1,
                         highlightbackground=C_LINEA)
        marco.grid(row=2, column=0, sticky="nsew", padx=8, pady=(0, 8))

        tk.Label(marco, text="▷  COBRO", bg=C_PANEL, fg=C_ACENTO,
                 font=("Courier", 11, "bold")).pack(anchor=tk.W, padx=12, pady=(8, 4))

        # Total
        marco_total = tk.Frame(marco, bg="#0A0E1A",
                                highlightthickness=1,
                                highlightbackground=C_ACENTO)
        marco_total.pack(fill=tk.X, padx=12, pady=4)

        tk.Label(marco_total, text="TOTAL A PAGAR", bg="#0A0E1A",
                 fg=C_TEXTO_DIM, font=("Courier", 9, "bold")).pack(side=tk.LEFT, padx=10, pady=8)

        self.etiqueta_total = tk.Label(
            marco_total, text="$ 0",
            bg="#0A0E1A", fg=C_VERDE,
            font=("Courier", 22, "bold")
        )
        self.etiqueta_total.pack(side=tk.RIGHT, padx=10)

        # Dinero recibido
        marco_dinero = tk.Frame(marco, bg=C_PANEL)
        marco_dinero.pack(fill=tk.X, padx=12, pady=4)

        tk.Label(marco_dinero, text="RECIBIDO ($)", bg=C_PANEL,
                 fg=C_TEXTO_DIM, font=("Courier", 9, "bold")).pack(side=tk.LEFT)

        self.entrada_dinero = tk.Entry(marco_dinero, textvariable=self.var_dinero_recibido,
                           font=("Courier", 16, "bold"), width=12,
                           justify=tk.RIGHT,
                           bg="#0D1425", fg=C_AMARILLO,
                           insertbackground=C_AMARILLO,
                           relief=tk.FLAT,
                           highlightthickness=1,
                           highlightbackground=C_ACENTO)
        self.entrada_dinero.pack(side=tk.RIGHT)

        # Vueltas
        marco_vueltas = tk.Frame(marco, bg="#0A0E1A",
                                  highlightthickness=1,
                                  highlightbackground=C_VERDE_SENA)
        marco_vueltas.pack(fill=tk.X, padx=12, pady=4)

        tk.Label(marco_vueltas, text="VUELTAS", bg="#0A0E1A",
                 fg=C_TEXTO_DIM, font=("Courier", 9, "bold")).pack(side=tk.LEFT, padx=10, pady=8)

        self.etiqueta_vueltas = tk.Label(
            marco_vueltas, text="$ 0",
            bg="#0A0E1A", fg=C_AMARILLO,
            font=("Courier", 22, "bold")
        )
        self.etiqueta_vueltas.pack(side=tk.RIGHT, padx=10)

        # Botones de acción
        marco_acc = tk.Frame(marco, bg=C_PANEL)
        marco_acc.pack(fill=tk.X, padx=12, pady=(6, 12))

        tk.Button(
            marco_acc, text="✓  COBRAR",
            command=self._cobrar,
            bg=C_VERDE_SENA, fg=C_TEXTO,
            font=("Courier", 11, "bold"),
            relief=tk.FLAT, cursor="hand2",
            padx=14, pady=8,
            activebackground=C_VERDE
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))

        tk.Button(
            marco_acc, text="↺  NUEVA VENTA",
            command=self._nueva_venta,
            bg="#1A0808", fg=C_NARANJA,
            font=("Courier", 10, "bold"),
            relief=tk.FLAT, cursor="hand2",
            padx=10, pady=8,
            activebackground="#2A1010"
        ).pack(side=tk.RIGHT, fill=tk.X, expand=True)

    # Barra de estado inferior
    def _barra_inferior(self):
        barra = tk.Frame(self.ventana, bg="#070B14", height=28)
        barra.pack(fill=tk.X, side=tk.BOTTOM)
        barra.pack_propagate(False)

        tk.Frame(barra, bg=C_ACENTO, height=1).pack(fill=tk.X, side=tk.TOP)

        self.etiqueta_estado = tk.Label(
            barra, text="⬤  Inicializando sistema...",
            bg="#070B14", fg=C_TEXTO_DIM,
            font=("Courier", 9)
        )
        self.etiqueta_estado.pack(side=tk.LEFT, padx=12, pady=4)

        tk.Label(barra, text="YOLOv8n · CPU · SENA CME 2025",
                 bg="#070B14", fg="#1A3050",
                 font=("Courier", 9)).pack(side=tk.RIGHT, padx=12)



    # CÁMARA Y LOOP DE DETECCIÓN

    def _toggle_camara(self):
        if self.camara_activa:
            self._detener_camara()
        else:
            self._iniciar_camara()

    def _iniciar_camara(self):
        self.camara = cv2.VideoCapture(0)
        if not self.camara.isOpened():
            messagebox.showerror("Error de cámara",
                "No se encontró cámara.\nVerifica la conexión.")
            return

        self.camara.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
        self.camara.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)

        self.camara_activa = True
        self.boton_camara.config(text="⏹  DETENER CÁMARA", bg=C_ROJO)
        self.boton_agregar.config(state=tk.NORMAL)
        self._set_estado("⬤  Cámara activa · Detección YOLOv8 en curso", C_VERDE)

        self.hilo_deteccion = threading.Thread(
            target=self._loop_deteccion, daemon=True)
        self.hilo_deteccion.start()

    def _detener_camara(self):
        self.camara_activa = False
        time.sleep(0.15)
        if self.camara:
            self.camara.release()
        self.frame_anotado = None
        self.frame_actual  = None
        self.clase_detectada = None
        self.progreso_carga  = 0.0
        self.boton_camara.config(text="▶  INICIAR CÁMARA", bg=C_VERDE_SENA)
        self.boton_agregar.config(state=tk.DISABLED)
        self.etiqueta_objeto.config(text="◌  Sin objeto detectado", fg=C_TEXTO_DIM)
        self._set_estado("⬤  Cámara detenida", C_TEXTO_DIM)
        self._actualizar_barra_ui(0.0, "")

    def _loop_deteccion(self):
        """
        Hilo: captura frames y aplica YOLO continuamente
        """
        tiempos_fps = []
        while self.camara_activa:
            t_ini = time.time()
            ret, frame = self.camara.read()
            if not ret:
                continue

            self.frame_actual = frame.copy()

            if self.modelo_yolo is None:
                self.frame_anotado = frame
                continue

            # Inferencia YOLO
            resultados = self.modelo_yolo(
                frame,
                conf=UMBRAL_CONFIANZA,
                verbose=False
            )

            frame_dibujado, clase_principal, confianza, todas_clases = \
                self._dibujar_detecciones(frame.copy(), resultados)

            self.frame_anotado   = frame_dibujado
            self.clase_detectada = clase_principal
            self.confianza_actual = confianza

            self._actualizar_confirmacion(todas_clases)

            # Cálculo de FPS
            t_fin = time.time()
            tiempos_fps.append(t_fin - t_ini)
            if len(tiempos_fps) > 20:
                tiempos_fps.pop(0)
            fps = 1.0 / (sum(tiempos_fps) / len(tiempos_fps))
            self.ventana.after(0, lambda f=fps:
                self.etiqueta_fps.config(text=f"{f:.1f} fps"))

    def _dibujar_detecciones(self, frame, resultados):
        clase_principal = None
        confianza_max = 0.0
        nombres_clases = resultados[0].names
        clases_detectadas_frame = []
        ahora = time.time()

        for caja in resultados[0].boxes:
            x1, y1, x2, y2 = map(int, caja.xyxy[0])
            conf = float(caja.conf[0])
            idx_cl = int(caja.cls[0])
            nombre = nombres_clases[idx_cl]
            clases_detectadas_frame.append(nombre)

            if conf > confianza_max:
                confianza_max = conf
                clase_principal = nombre

            # IDENTIFICACIÓN DE TIPO (PRODUCTO O DINERO)
            es_producto = nombre in CATALOGO_PRECIOS
            es_dinero = nombre in CATALOGO_DINERO
            
            bloqueado = nombre in self.bloqueos_temporales
            if es_producto:
                contador = self.contadores_productos.get(nombre, 0)
            elif es_dinero:
                contador = self.contadores_dinero.get(nombre, 0)
            else:
                contador = 0
            
            # Centro para el círculo de carga
            centro_x = x1 + (x2 - x1) // 2
            centro_y = y1 - 25

            if es_producto or es_dinero:
                # Obtener nombre y precio/valor
                if es_producto:
                    nom_disp, precio = CATALOGO_PRECIOS[nombre]
                    txt_escanenado = f"Escaneando {nom_disp}..."
                    txt_listo = f"{nom_disp} escaneado - ${precio:,}"
                else:
                    valor = CATALOGO_DINERO[nombre]
                    txt_escanenado = f"Escaneando billete ${valor:,}..."
                    txt_listo = f"Billete ${valor:,} escaneado"

                if bloqueado:
                    # ESTADO: YA REGISTRADO
                    color = (0, 255, 136)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    (w, h), _ = cv2.getTextSize(txt_listo, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
                    cv2.rectangle(frame, (x1, y1-25), (x1+w+10, y1), color, -1)
                    cv2.putText(frame, txt_listo, (x1+5, y1-8), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (10, 14, 26), 2)
                
                elif contador > 0:
                    # ESTADO: CARGANDO ANIMACIÓN
                    color_carga = (0, 229, 255)
                    progreso = contador / FRAMES_CONFIRMACION
                    cv2.ellipse(frame, (centro_x, centro_y), (12, 12), 
                                0, -90, int(progreso * 360) - 90, color_carga, 3)
                    cv2.putText(frame, txt_escanenado, (centro_x + 20, centro_y + 5), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.4, color_carga, 1, cv2.LINE_AA)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color_carga, 1, cv2.LINE_4)
            else:
                # Objeto desconocido
                cv2.rectangle(frame, (x1, y1), (x2, y2), (100, 100, 100), 1)

        return frame, clase_principal, confianza_max, clases_detectadas_frame

    def _actualizar_confirmacion(self, clases_detectadas: list):
        """
        Lógica multiobjeto con bloqueo de tiempo estricto.
        Respeta el cooldown exacto de 5s y permite registrar múltiples 
        objetos de la misma clase simultáneamente
        """
        ahora = time.time()
        COOLDOWN = 5

        # Diccionario para saber cuántos objetos de una misma clase hemos registrado
        if not hasattr(self, 'instancias_bloqueadas'):
            self.instancias_bloqueadas = {}

        # PROCESAR PRODUCTOS
        for clase in CATALOGO_PRECIOS:
            cantidad_en_pantalla = clases_detectadas.count(clase)

            # Si la clase está en periodo de bloqueo (ya fue registrada)
            if clase in self.bloqueos_temporales:
                if cantidad_en_pantalla > 0:
                    self.bloqueos_temporales[clase] = ahora

                    instancias_previas = self.instancias_bloqueadas.get(clase, 1)
                    if cantidad_en_pantalla > instancias_previas:
                        nuevos_objetos = cantidad_en_pantalla - instancias_previas
                        for _ in range(nuevos_objetos):
                            self.ventana.after(0, lambda c=clase: self._agregar_producto(c))
                        self.instancias_bloqueadas[clase] = cantidad_en_pantalla
                
                else:
                    if ahora - self.bloqueos_temporales[clase] > COOLDOWN:
                        # Cooldown completado se libera el bloqueo
                        del self.bloqueos_temporales[clase]
                        self.contadores_productos[clase] = 0
                        self.instancias_bloqueadas[clase] = 0

            # Si la clase NO está bloqueada (es una venta nueva)
            else:
                if cantidad_en_pantalla > 0:
                    self.contadores_productos[clase] = self.contadores_productos.get(clase, 0) + 1
                    
                    if self.contadores_productos[clase] >= FRAMES_CONFIRMACION:
                        for _ in range(cantidad_en_pantalla):
                            self.ventana.after(0, lambda c=clase: self._agregar_producto(c))
                        
                        # Iniciamos el bloqueo
                        self.bloqueos_temporales[clase] = ahora
                        self.instancias_bloqueadas[clase] = cantidad_en_pantalla
                        self.contadores_productos[clase] = 0
                else:
                    if clase in self.contadores_productos:
                        self.contadores_productos[clase] = max(0, self.contadores_productos[clase] - 2)

        # PROCESAR DINERO
        for clase in CATALOGO_DINERO:
            cantidad_en_pantalla = clases_detectadas.count(clase)

            if clase in self.bloqueos_temporales:
                if cantidad_en_pantalla > 0:
                    self.bloqueos_temporales[clase] = ahora

                    instancias_previas = self.instancias_bloqueadas.get(clase, 1)
                    if cantidad_en_pantalla > instancias_previas:
                        nuevos_billetes = cantidad_en_pantalla - instancias_previas
                        for _ in range(nuevos_billetes):
                            self.ventana.after(0, lambda c=clase: self._agregar_dinero(c))
                        self.instancias_bloqueadas[clase] = cantidad_en_pantalla
                else:
                    if ahora - self.bloqueos_temporales[clase] > COOLDOWN:
                        del self.bloqueos_temporales[clase]
                        self.contadores_dinero[clase] = 0
                        self.instancias_bloqueadas[clase] = 0
            else:
                if cantidad_en_pantalla > 0:
                    self.contadores_dinero[clase] = self.contadores_dinero.get(clase, 0) + 1
                    if self.contadores_dinero[clase] >= FRAMES_CONFIRMACION:
                        for _ in range(cantidad_en_pantalla):
                            self.ventana.after(0, lambda c=clase: self._agregar_dinero(c))
                        self.bloqueos_temporales[clase] = ahora
                        self.instancias_bloqueadas[clase] = cantidad_en_pantalla
                        self.contadores_dinero[clase] = 0
                else:
                    if clase in self.contadores_dinero:
                        self.contadores_dinero[clase] = max(0, self.contadores_dinero[clase] - 2)

        # ACTUALIZAR LA BARRA VISUAL
        max_progreso = 0
        clase_principal = ""
        
        for c, v in self.contadores_productos.items():
            prog = v / FRAMES_CONFIRMACION
            if prog > max_progreso:
                max_progreso = prog
                clase_principal = c
        
        for c, v in self.contadores_dinero.items():
            prog = v / 10
            if prog > max_progreso:
                max_progreso = prog
                clase_principal = c

        self.ventana.after(0, lambda: self._actualizar_barra_ui(max_progreso, clase_principal))

    def _actualizar_barra_ui(self, progreso: float, clase: str):
        """Actualiza únicamente la etiqueta de texto en el hilo de UI."""
        try:
            # Determinamos el color del texto según el progreso
            color_texto = C_ACENTO if progreso < 1.0 else C_VERDE

            if clase and clase in CATALOGO_PRECIOS:
                nombre_disp, precio = CATALOGO_PRECIOS[clase]
                self.etiqueta_objeto.config(
                    text=f"{nombre_disp}  ·  ${precio:,}",
                    fg=color_texto
                )
            elif clase and clase in CATALOGO_DINERO:
                valor = CATALOGO_DINERO[clase]
                self.etiqueta_objeto.config(
                    text=f"Billete detectado  ·  ${valor:,}",
                    fg=color_texto
                )
            elif not clase:
                self.etiqueta_objeto.config(
                    text=" Sin objeto detectado", fg=C_TEXTO_DIM)
        except tk.TclError:
            pass

    # LOOP CANVAS (actualiza el lienzo de video en el hilo UI)

    def _loop_canvas(self):
        try:
            if self.frame_anotado is not None:
                self._mostrar_frame(self.frame_anotado)
            elif not self.camara_activa:
                self._dibujar_pantalla_inactiva()
        except Exception:
            pass
        self.ventana.after(INTERVALO_MS, self._loop_canvas)

    def _mostrar_frame(self, frame):
        ancho = self.lienzo.winfo_width()
        alto  = self.lienzo.winfo_height()
        if ancho < 2 or alto < 2:
            return

        frame_rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        imagen_pil  = Image.fromarray(frame_rgb).resize(
            (ancho, alto), Image.LANCZOS)
        imagen_tk   = ImageTk.PhotoImage(imagen_pil)
        self.lienzo.create_image(0, 0, anchor=tk.NW, image=imagen_tk)
        self.imagen_canvas_ref = imagen_tk

    def _dibujar_pantalla_inactiva(self):
        """Dibuja una pantalla de standby animada cuando la cámara está apagada."""
        ancho = self.lienzo.winfo_width()
        alto  = self.lienzo.winfo_height()
        if ancho < 2 or alto < 2:
            return

        img = Image.new("RGB", (ancho, alto), "#050810")
        draw = ImageDraw.Draw(img)

        # Grid de puntos
        paso = 30
        t = time.time()
        for x in range(0, ancho, paso):
            for y in range(0, alto, paso):
                brillo = int(20 + 15 * math.sin(
                    (x + y) * 0.05 + t * 1.5))
                draw.ellipse([x-1, y-1, x+1, y+1],
                             fill=(0, brillo, int(brillo * 1.5)))

        # Texto central
        msg = "CÁMARA INACTIVA"
        draw.text((ancho // 2, alto // 2 - 20), msg,
                  fill=(0, 80, 120),
                  anchor="mm")
        draw.text((ancho // 2, alto // 2 + 20),
                  "Presiona  ▶  INICIAR CÁMARA",
                  fill=(0, 50, 80), anchor="mm")

        imagen_tk = ImageTk.PhotoImage(img)
        self.lienzo.create_image(0, 0, anchor=tk.NW, image=imagen_tk)
        self.imagen_canvas_ref = imagen_tk

    # LÓGICA DE VENTA

    def _agregar_producto(self, nombre_clase: str):
        """Agrega el producto al carrito y actualiza la UI."""
        if nombre_clase not in CATALOGO_PRECIOS:
            return

        self.productos_venta[nombre_clase] = \
            self.productos_venta.get(nombre_clase, 0) + 1

        self._actualizar_tabla()
        self._actualizar_total()
        self._set_estado(
            f"⊕  Producto agregado: {CATALOGO_PRECIOS[nombre_clase][0]}", C_VERDE)
        self._flash_total()
    
    def _agregar_dinero(self, clase):
        total_pagar = self._calcular_total()

        # Validar que haya al menos un producto registrado
        if total_pagar == 0:
            self._set_estado("⚠ No se puede recibir dinero: carrito vacío", C_NARANJA)
            return

        valor = CATALOGO_DINERO[clase]
        
        # Limpiamos el string actual para poder sumarlo
        actual_str = self.var_dinero_recibido.get().replace("$", "").replace(",", "").replace(".", "").strip()
        try:
            actual = int(actual_str)
        except ValueError:
            actual = 0

        nuevo_total = actual + valor
        self.var_dinero_recibido.set(f"$ {nuevo_total:,}")

        self._set_estado(f"💵 Dinero agregado: ${valor:,}", C_VERDE)
        self._flash_recibido()

        # Verificar si el dinero recibido cubre o excede el total
        if nuevo_total >= total_pagar:
            self._set_estado("✅ Pago completado, procesando cobro...", C_VERDE)
            self.ventana.after(500, self._cobrar)


    def _forzar_registro(self):
        """Agrega manualmente el objeto visible ahora usando la nueva lógica."""
        clase = self.clase_detectada
        if clase and clase in CATALOGO_PRECIOS:
            self._agregar_producto(clase)
            ahora = time.time()
            self.bloqueos_temporales[clase] = ahora
            self.contadores_productos[clase] = 0
            self._actualizar_barra_ui(0.0, "")
        else:
            self._set_estado("⚠  Objeto no identificado en catálogo", C_NARANJA)

    def _quitar_seleccionado(self):
        selec = self.tabla.selection()
        if not selec:
            return
        valores = self.tabla.item(selec[0], "values")
        nombre_disp = valores[0]
        for clase, (disp, _) in CATALOGO_PRECIOS.items():
            if disp == nombre_disp:
                if clase in self.productos_venta:
                    self.productos_venta[clase] -= 1
                    if self.productos_venta[clase] <= 0:
                        del self.productos_venta[clase]
                self._actualizar_tabla()
                self._actualizar_total()
                return

    def _actualizar_tabla(self):
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)
        for clase, cantidad in self.productos_venta.items():
            nombre_disp, precio = CATALOGO_PRECIOS[clase]
            subtotal = precio * cantidad
            self.tabla.insert("", tk.END, values=(
                nombre_disp,
                cantidad,
                f"${precio:,}",
                f"${subtotal:,}"
            ))

    def _calcular_total(self):
        total = 0
        for clase, cantidad in self.productos_venta.items():
            _, precio = CATALOGO_PRECIOS[clase]
            total += precio * cantidad
        return total

    def _actualizar_total(self):
        total = self._calcular_total()
        self.etiqueta_total.config(text=f"${total:,}")

    def _flash_total(self):
        """Efecto visual de parpadeo en el total al agregar un producto."""
        def _paso(n):
            if n <= 0:
                self.etiqueta_total.config(fg=C_VERDE)
                return
            color = C_ACENTO if n % 2 == 0 else C_VERDE
            self.etiqueta_total.config(fg=color)
            self.ventana.after(120, lambda: _paso(n - 1))
        _paso(4)
    
    def _flash_recibido(self):
        """Efecto visual de parpadeo en el dinero recibido."""
        def _paso(n):
            if n <= 0:
                self.entrada_dinero.config(fg=C_AMARILLO)
                return
            color = C_ACENTO if n % 2 == 0 else C_VERDE
            self.entrada_dinero.config(fg=color)
            self.ventana.after(120, lambda: _paso(n - 1))
        _paso(4)

    def _cobrar(self):
        total = self._calcular_total()
        if total == 0:
            messagebox.showwarning("Carrito vacío", "No hay productos registrados.")
            return
        try:
            texto_limpio = self.var_dinero_recibido.get().replace("$", "").replace(",", "").replace(".", "").strip()
            recibido = float(texto_limpio)
        except ValueError:
            messagebox.showerror("Valor inválido", "Ingresa el monto numérico válido.")
            return

        if recibido < total:
            faltante = total - recibido
            messagebox.showwarning("Pago insuficiente", f"Faltan: ${faltante:,.0f} COP")
            return

        vueltas = recibido - total
        self.etiqueta_vueltas.config(text=f"${vueltas:,.0f}")

        # Recibo
        lineas = [f"  RECIBO DE VENTA  —  SENA CME",
                  f"  {datetime.datetime.now().strftime('%d/%m/%Y  %H:%M:%S')}",
                  "  " + "─" * 38]
        for clase, cant in self.productos_venta.items():
            nd, pu = CATALOGO_PRECIOS[clase]
            lineas.append(f"  {nd:<22} x{cant}  ${pu * cant:>10,}")
        lineas += ["  " + "─" * 38,
                   f"  TOTAL              ${total:>15,}",
                   f"  RECIBIDO           ${recibido:>15,.0f}",
                   f"  VUELTAS            ${vueltas:>15,.0f}",
                   "  " + "─" * 38,
                   "  ¡Gracias por su compra!"]

        # Crear registro
        self._registrar_venta(total, recibido, vueltas)
        # Mostrar recibo
        messagebox.showinfo("Venta completada", "\n".join(lineas))

    def _nueva_venta(self):
        if self.productos_venta:
            if not messagebox.askyesno("Advertencia", "¿Deseas iniciar una nueva venta?"):
                return
                
        self.productos_venta.clear()
        self.var_dinero_recibido.set("$ 0")
        self._actualizar_tabla()
        self._actualizar_total()
        self.etiqueta_vueltas.config(text="$ 0")
        self._set_estado("⬤  Nueva venta iniciada", C_ACENTO)

    # UTILIDADES

    def _set_estado(self, texto: str, color: str = C_TEXTO_DIM):
        try:
            self.etiqueta_estado.config(text=texto, fg=color)
        except tk.TclError:
            pass

    def _actualizar_reloj(self):
        ahora = datetime.datetime.now().strftime("%Y·%m·%d  %H:%M:%S")
        try:
            self.etiqueta_reloj.config(text=ahora)
        except tk.TclError:
            return
        self.ventana.after(1000, self._actualizar_reloj)

    def cerrar(self):
        self.camara_activa = False
        time.sleep(0.2)
        if self.camara:
            self.camara.release()
        self.ventana.destroy()

    def _registrar_venta(self, total, recibido, vueltas):
        carpeta = "Inventario"
        archivo_path = os.path.join(carpeta, "ventas_acumuladas.csv")
        
        # Crear la carpeta si no existe
        if not os.path.exists(carpeta):
            os.makedirs(carpeta)
            
        # Preparar los datos (fecha y hora)
        fecha_hora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Abrir el archivo en modo 'append' (añadir al final)
        file_exists = os.path.isfile(archivo_path)
        
        try:
            with open(archivo_path, mode='a', newline='', encoding='utf-8') as f:
                escritor = csv.writer(f)
                
                # Escribir cabeceras solo si el archivo es nuevo
                if not file_exists:
                    escritor.writerow(["Fecha_Hora", "Producto", "Cantidad", "Precio_Unitario", "Subtotal", "Total", "Recibido", "Vueltas"])
                
                # Extraer datos del Treeview y escribirlos
                for item in self.tabla.get_children():
                    valores = self.tabla.item(item)['values']
                    fila = [fecha_hora] + valores + [total, recibido, vueltas]
                    escritor.writerow(fila)
                    
        except Exception as e:
            print(f"Error al guardar CSV: {e}")

# PUNTO DE ENTRADA

if __name__ == "__main__":
    ventana = tk.Tk()
    ventana.iconbitmap(recurso_path('Icono.ico'))
    app = CajaRegistradoraYOLO(ventana)
    ventana.protocol("WM_DELETE_WINDOW", app.cerrar)
    ventana.mainloop()