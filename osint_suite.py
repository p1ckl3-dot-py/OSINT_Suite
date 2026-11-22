import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import requests
import urllib3
from PIL import Image, ImageTk
from PIL.ExifTags import TAGS, GPSTAGS

# Parche obligatorio para solucionar el error de PyInstaller/Linux al cargar imágenes
try:
    import PIL._tkinter_finder
except ImportError:
    pass

import webbrowser
import time
import os
import threading
import socket
import sys
import subprocess
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor

# Silenciamos las advertencias de SSL inseguro
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==============================================================================
# PROYECTO: SUITE OSINT
# Autor: p1ckl3-dot-py
# ==============================================================================

class SuiteOSINT:
    def __init__(self, ventana):
        """Inicializa la aplicacion, configura la red y prepara la interfaz."""
        self.ventana = ventana
        self.ventana.title("Suite OSINT - Nahuel Fernandez Gorgojo - ASIR 2026")
        self.ventana.geometry("1450x900")
        self.ventana.configure(bg="#f0f2f5")

        # Variables globales
        self.lista_resultados = [] 
        self.gps_temporal = None
        self.ruta_foto_actual = None
        
        # --- CONFIGURACION DEL MOTOR DE RED ---
        self.executor = ThreadPoolExecutor(max_workers=30)
        self.sesion = requests.Session()
        
        self.sesion.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # --- BASE DE DATOS DE INTELIGENCIA ---
        self.redes_sociales = {
            "Principales": {
                "Instagram": "https://www.instagram.com/{}", 
                "X (Twitter)": "https://twitter.com/{}", 
                "TikTok": "https://www.tiktok.com/@{}",
                "Facebook": "https://www.facebook.com/{}",
                "Reddit": "https://www.reddit.com/user/{}",
                "Pinterest": "https://www.pinterest.es/{}/"
            },
            "Profesional & IT": {
                "LinkedIn": "https://www.linkedin.com/in/{}", 
                "GitHub": "https://github.com/{}", 
                "GitLab": "https://gitlab.com/{}",
                "StackOverflow": "https://stackoverflow.com/users/{}",
                "HackerRank": "https://www.hackerrank.com/{}",
                "Linktree": "https://linktr.ee/{}"
            },
            "Multimedia & Diseno": {
                "YouTube": "https://www.youtube.com/@{}", 
                "Twitch": "https://www.twitch.tv/{}",
                "Vimeo": "https://vimeo.com/{}",
                "SoundCloud": "https://soundcloud.com/{}",
                "Flickr": "https://www.flickr.com/people/{}/",
                "Behance": "https://www.behance.net/{}",
                "Domestika": "https://www.domestika.org/es/{}"
            },
            "Comunidades & Gaming": {
                "Steam": "https://steamcommunity.com/id/{}",
                "Chess.com": "https://www.chess.com/member/{}",
                "Quora": "https://es.quora.com/profile/{}",
                "Medium": "https://medium.com/@{}",
                "Rankia": "https://www.rankia.com/usuarios/{}"
            }
        }
        
        self.firmas_negativas = [
            "page not found", "doesn't exist", "pagina no encontrada", 
            "couldn't find", "no se encontro", "user not found", 
            "this account doesn't exist", "nobody on reddit goes by that name"
        ]

        self.preparar_estilos()
        self.dibujar_interfaz()

    def preparar_estilos(self):
        estilo = ttk.Style()
        estilo.theme_use('clam')
        estilo.configure("TNotebook", background="#f0f2f5", borderwidth=0)
        estilo.configure("TNotebook.Tab", font=("Segoe UI", 10, "bold"), padding=[15, 10])
        estilo.configure("Treeview", rowheight=30, font=("Segoe UI", 9))
        estilo.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#e0e6ed")
        estilo.map('Treeview', background=[('selected', '#347083')], foreground=[('selected', 'white')])

    def abrir_enlace(self, enlace):
        try:
            if sys.platform.startswith('linux'):
                subprocess.Popen(['xdg-open', enlace], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                webbrowser.open(enlace, new=2)
        except Exception as e:
            print(f"Error al abrir navegador: {e}")

    def escribir_log(self, widget, mensaje, tipo="info"):
        iconos = {"info": "ℹ️ ", "error": "❌ ", "ok": "✅ ", "warn": "⚠️ "}
        texto_formateado = f"[{time.strftime('%H:%M:%S')}] {iconos.get(tipo,'')}{mensaje}\n"
        self.ventana.after(0, lambda: [widget.insert(tk.END, texto_formateado), widget.see(tk.END)])

    # =========================================================================
    # MODULO 1: BUSQUEDA DE PERSONAS
    # =========================================================================
    def UI_busqueda(self):
        cuadro = tk.LabelFrame(self.pestania_google, text=" Rastrear Identidad (Dorks) ", bg="white", padx=20, pady=20)
        cuadro.pack(fill="x", padx=25, pady=10)
        
        tk.Label(cuadro, text="Nombre Completo:", bg="white", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.input_nombre = tk.Entry(cuadro, width=60, font=("Segoe UI", 11), bd=2, relief="groove")
        self.input_nombre.grid(row=0, column=1, padx=15, pady=5)
        
        tk.Button(cuadro, text="Lanzar Busqueda Global", bg="#1a73e8", fg="white", font=("Segoe UI", 10, "bold"), command=self.iniciar_busqueda_personas).grid(row=0, column=2, padx=20)
        
        self.log_google = tk.Text(self.pestania_google, height=18, bg="#ffffff", font=("Consolas", 10), bd=1, relief="solid", padx=15, pady=15)
        self.log_google.pack(fill="both", expand=True, padx=25, pady=10)

    def iniciar_busqueda_personas(self):
        nombre = self.input_nombre.get().strip()
        if not nombre:
            messagebox.showinfo("Datos incompletos", "Introduce un nombre.")
            return
            
        n_quote = quote(f'"{nombre}"')
        consultas = [
            f"?q={n_quote}",                                                                        
            f"?q=site:linkedin.com/in+OR+site:es.linkedin.com/in+{n_quote}",                        
            f"?q=site:boe.es+{n_quote}",                                                            
            f"?q=site:infoempresa.com+OR+site:axesor.es+OR+site:empresia.es+{n_quote}",             
            f"?q=site:instagram.com+OR+site:twitter.com+OR+site:facebook.com+OR+site:tiktok.com+{n_quote}", 
            f"?q={n_quote}+filetype:pdf+OR+filetype:xls+OR+filetype:doc",                           
            f"?q=site:paginasblancas.es+OR+site:telexplorer.es+{n_quote}"                           
        ]

        if messagebox.askyesno("Aviso", f"Se abriran {len(consultas)} pestañas. ¿Continuar?"):
            threading.Thread(target=self.abrir_pestanias_sincronizadas, args=(consultas, nombre), daemon=True).start()

    def abrir_pestanias_sincronizadas(self, consultas, nombre):
        for index, c in enumerate(consultas):
            enlace_final = f"https://www.google.com/search{c}"
            self.escribir_log(self.log_google, f"Consulta {index+1} enviada.", "ok")
            self.abrir_enlace(enlace_final)
            if index == 0: time.sleep(4.0) 
            else: time.sleep(0.8)
            
        # Registramos solo que se lanzó una investigación de identidad, sin saturar de ruido
        self.lista_resultados.append({"Modulo": "Identidad", "Target": nombre, "Info": "Búsqueda de huella digital ejecutada en fuentes abiertas.", "Fecha": time.strftime('%H:%M:%S')})

    # =========================================================================
    # MODULO 2: NOMBRES DE USUARIO
    # =========================================================================
    def UI_social(self):
        cuadro = tk.LabelFrame(self.pestania_social, text=" Escaneo de Nombres de Usuario ", bg="white", padx=20, pady=20)
        cuadro.pack(fill="x", padx=25, pady=20)
        
        self.input_usuario = tk.Entry(cuadro, width=40, font=("Segoe UI", 11))
        self.input_usuario.pack(side="left", padx=15)
        
        tk.Button(cuadro, text="Iniciar Escaneo", bg="#34a853", fg="white", font=("Segoe UI", 10, "bold"), command=self.iniciar_escaneo_social).pack(side="left")
        
        frame_tabla = tk.Frame(self.pestania_social)
        frame_tabla.pack(fill="both", expand=True, padx=25, pady=10)
        
        scroll = ttk.Scrollbar(frame_tabla)
        self.tabla_social = ttk.Treeview(frame_tabla, columns=("red", "estado", "url"), show="headings", yscrollcommand=scroll.set)
        scroll.config(command=self.tabla_social.yview)
        
        self.tabla_social.heading("red", text="PLATAFORMA")
        self.tabla_social.heading("estado", text="ESTADO")
        self.tabla_social.heading("url", text="ENLACE")
        
        scroll.pack(side="right", fill="y")
        self.tabla_social.pack(side="left", fill="both", expand=True)
        
        self.tabla_social.bind("<Double-1>", self.abrir_perfil_social)

    def abrir_perfil_social(self, event):
        item = self.tabla_social.selection()
        if item:
            valores = self.tabla_social.item(item[0], "values")
            if valores and len(valores) >= 3:
                url_destino = valores[2]
                if url_destino.startswith("http"):
                    self.abrir_enlace(url_destino)

    def iniciar_escaneo_social(self):
        usuario = self.input_usuario.get().strip()
        if not usuario: return
        for item in self.tabla_social.get_children(): self.tabla_social.delete(item)
        threading.Thread(target=self.proceso_escaneo_social, args=(usuario,), daemon=True).start()

    def proceso_escaneo_social(self, usuario):
        def comprobar_plataforma(nombre_red, url_formato):
            enlace_destino = url_formato.format(usuario)
            perfil_existe = False
            texto_resultado = "No encontrado"
            
            try:
                res = self.sesion.get(enlace_destino, timeout=10, verify=False)
                if res.status_code == 200:
                    if not any(f in res.text.lower() for f in self.firmas_negativas):
                        perfil_existe = True
                        texto_resultado = "Encontrado"
                elif res.status_code in [401, 403, 429]:
                    perfil_existe = True
                    texto_resultado = "Protegido/Existente"
            except:
                texto_resultado = "Error de conexion"

            # INTELIGENCIA ACCIONABLE: Solo guardamos en el informe si se ha detectado el perfil
            if perfil_existe: 
                self.lista_resultados.append({
                    "Modulo": "Redes Sociales", 
                    "Target": usuario, 
                    "Info": f"Perfil detectado en {nombre_red}: {enlace_destino}", 
                    "Fecha": time.strftime('%H:%M:%S')
                })
                
            self.ventana.after(0, lambda: self.tabla_social.insert("", "end", values=(nombre_red, texto_resultado, enlace_destino)))

        for cat, sitios in self.redes_sociales.items():
            for nombre_red, url_formato in sitios.items():
                self.executor.submit(comprobar_plataforma, nombre_red, url_formato)

    # =========================================================================
    # MODULO 3: ANALISIS FORENSE DE IMAGENES
    # =========================================================================
    def UI_imagenes(self):
        panel = tk.Frame(self.pestania_img, bg="#f0f2f5")
        panel.pack(fill="x", padx=25, pady=15)
        
        tk.Button(panel, text="Cargar Imagen", command=self.analizar_foto, bg="#5f6368", fg="white", font=("Segoe UI", 10, "bold")).pack(side="left", padx=5)
        self.btn_mapa = tk.Button(panel, text="Ver en Mapa", state="disabled", bg="#ea4335", fg="white", font=("Segoe UI", 10, "bold"), command=self.ver_mapa)
        self.btn_mapa.pack(side="left", padx=5)
        
        self.btn_inv_auto = tk.Button(panel, text="🤖 Busqueda Inversa Auto (Facil)", state="disabled", bg="#9b59b6", fg="white", font=("Segoe UI", 10, "bold"), command=self.inversa_automatica)
        self.btn_inv_auto.pack(side="left", padx=5)
        self.btn_inv_man = tk.Button(panel, text="🖐️ Busqueda Inversa Manual (Segura)", state="disabled", bg="#34495e", fg="white", font=("Segoe UI", 10, "bold"), command=self.inversa_manual)
        self.btn_inv_man.pack(side="left", padx=5)
        
        cont = tk.Frame(self.pestania_img, bg="#f0f2f5")
        cont.pack(fill="both", expand=True, padx=25)
        
        self.frame_img = tk.Frame(cont, bg="white", width=400, height=400, bd=1, relief="solid")
        self.frame_img.pack(side="left", pady=10)
        self.frame_img.pack_propagate(False)
        self.visor_img = tk.Label(self.frame_img, bg="white")
        self.visor_img.pack(expand=True, fill="both")
        
        frame_log = tk.Frame(cont)
        frame_log.pack(side="left", fill="both", expand=True, padx=(20,0), pady=10)
        scroll_img = ttk.Scrollbar(frame_log)
        self.log_img = tk.Text(frame_log, bg="white", font=("Consolas", 10), padx=15, pady=15, yscrollcommand=scroll_img.set)
        scroll_img.config(command=self.log_img.yview)
        scroll_img.pack(side="right", fill="y")
        self.log_img.pack(side="left", fill="both", expand=True)

    def analizar_foto(self):
        ruta = filedialog.askopenfilename()
        if not ruta: return
        self.ruta_foto_actual = ruta
        self.log_img.delete('1.0', tk.END)
        
        self.btn_mapa.config(state="disabled")
        self.btn_inv_auto.config(state="normal")
        self.btn_inv_man.config(state="normal")
        
        try:
            img = Image.open(ruta)
            nombre_archivo = os.path.basename(ruta)
            self.escribir_log(self.log_img, f"Archivo: {nombre_archivo}", "info")
            img.thumbnail((380, 380))
            self.img_tk = ImageTk.PhotoImage(img)
            self.visor_img.config(image=self.img_tk)
            
            exif = img._getexif()
            if exif:
                for t, valor in exif.items():
                    n = TAGS.get(t, t)
                    
                    if n == "GPSInfo":
                        datos_gps = {GPSTAGS.get(t, t): valor[t] for t in valor if isinstance(t, int)}
                        
                        if 'GPSLatitude' in datos_gps and 'GPSLongitude' in datos_gps:
                            try:
                                lat = self.convertir_coordenadas_gps(datos_gps['GPSLatitude'])
                                lon = self.convertir_coordenadas_gps(datos_gps['GPSLongitude'])
                                
                                if datos_gps.get('GPSLatitudeRef') == 'S': lat = -lat
                                if datos_gps.get('GPSLongitudeRef') == 'W': lon = -lon
                                
                                self.gps_temporal = (lat, lon)
                                self.btn_mapa.config(state="normal")
                                self.escribir_log(self.log_img, f"📍 Coordenadas GPS: {lat}, {lon}", "ok")
                                
                                # INTELIGENCIA ACCIONABLE: Solo guardamos en el informe si extraemos coordenadas reales
                                enlace_maps = f"https://www.google.com/maps?q={lat},{lon}"
                                self.lista_resultados.append({
                                    "Modulo": "Forense de Imagen", 
                                    "Target": nombre_archivo, 
                                    "Info": f"Localización GPS detectada: Lat {lat}, Lon {lon} (Ver en: {enlace_maps})", 
                                    "Fecha": time.strftime('%H:%M:%S')
                                })
                            except Exception as e:
                                pass
                                
                    elif isinstance(valor, (str, int, float)) and len(str(valor)) < 100:
                        self.escribir_log(self.log_img, f"{n}: {valor}")
            else:
                self.escribir_log(self.log_img, "Sin metadatos EXIF", "warn")
        except Exception as e:
            self.escribir_log(self.log_img, f"Error: {e}", "error")

    def convertir_coordenadas_gps(self, datos):
        """Convierte coordenadas del formato RAW EXIF a formato decimal"""
        return float(datos[0]) + (float(datos[1]) / 60.0) + (float(datos[2]) / 3600.0)

    def ver_mapa(self):
        if self.gps_temporal:
            self.abrir_enlace(f"https://www.google.com/maps?q={self.gps_temporal[0]},{self.gps_temporal[1]}")

    def inversa_automatica(self):
        if messagebox.askyesno("Privacidad (OPSEC)", "La foto se subira temporalmente a un host publico (tmpfiles.org) para analizarla automaticaente en Lens y Yandex.\n\n¿Seguro que no contiene datos confidenciales?"):
            self.btn_inv_auto.config(state="disabled")
            self.escribir_log(self.log_img, "Subiendo imagen efimeramente...", "info")
            threading.Thread(target=self.proceso_inversa_auto, daemon=True).start()

    def proceso_inversa_auto(self):
        try:
            with open(self.ruta_foto_actual, 'rb') as f:
                res = requests.post('https://tmpfiles.org/api/v1/upload', files={'file': f}, timeout=15)
            if res.status_code == 200:
                url_limpia = res.json()['data']['url'].replace('tmpfiles.org/', 'tmpfiles.org/dl/')
                url_codificada = quote(url_limpia)
                self.escribir_log(self.log_img, "Subida OK. Lanzando reconocimiento facial/objetos...", "ok")
                self.abrir_enlace(f"https://lens.google.com/uploadbyurl?url={url_codificada}")
                time.sleep(4.0) 
                self.abrir_enlace(f"https://yandex.com/images/search?rpt=imageview&url={url_codificada}")
            else:
                self.escribir_log(self.log_img, "Error del servidor temporal.", "error")
        except Exception as e:
            self.escribir_log(self.log_img, f"Fallo de conexion: {e}", "error")
        finally:
            self.ventana.after(0, lambda: self.btn_inv_auto.config(state="normal"))

    def inversa_manual(self):
        self.escribir_log(self.log_img, "Iniciando busqueda segura. No se subiran datos desde la app.", "ok")
        motores = ["https://lens.google.com/", "https://yandex.com/images/", "https://tineye.com/"]
        
        for idx, url in enumerate(motores):
            self.abrir_enlace(url)
            if idx == 0: time.sleep(4.0)
            else: time.sleep(0.8)
            
        try:
            directorio = os.path.dirname(self.ruta_foto_actual)
            if sys.platform.startswith('linux'):
                subprocess.Popen(['xdg-open', directorio], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif sys.platform == 'win32':
                subprocess.Popen(f'explorer /select,"{os.path.normpath(self.ruta_foto_actual)}"')
            self.escribir_log(self.log_img, "Arrastra la foto desde la carpeta recien abierta a tu navegador.", "info")
        except:
            self.escribir_log(self.log_img, "Buscadores abiertos. Sube tu foto manualmente.", "info")

    # =========================================================================
    # MODULO 4: RED E INFRAESTRUCTURA
    # =========================================================================
    def UI_red(self):
        cuadro_ctrl = tk.Frame(self.pestania_red, bg="white", pady=15, padx=20)
        cuadro_ctrl.pack(fill="x", padx=25, pady=(20, 10))
        
        tk.Label(cuadro_ctrl, text="IP o Dominio:", bg="white", font=("Segoe UI", 10, "bold")).pack(side="left", padx=5)
        self.input_red = tk.Entry(cuadro_ctrl, width=40, font=("Segoe UI", 11))
        self.input_red.pack(side="left", padx=15)
        
        self.btn_auditar = tk.Button(cuadro_ctrl, text="🔍 Lanzar Escaneo Completo", bg="#1a73e8", fg="white", font=("Segoe UI", 10, "bold"), command=self.iniciar_auditoria_red)
        self.btn_auditar.pack(side="left")

        self.progreso_red = ttk.Progressbar(self.pestania_red, orient="horizontal", mode="determinate")
        self.progreso_red.pack(fill="x", padx=25, pady=5)

        self.dashboard = tk.LabelFrame(self.pestania_red, text=" Inteligencia de Infraestructura ", bg="white", font=("Segoe UI", 10, "bold"), padx=20, pady=15)
        self.dashboard.pack(fill="x", padx=25, pady=5)
        
        self.lbl_ip = tk.Label(self.dashboard, text="📍 IP: Esperando...", bg="white", font=("Segoe UI", 11))
        self.lbl_ip.grid(row=0, column=0, sticky="w", pady=5, padx=20)
        
        self.lbl_geo = tk.Label(self.dashboard, text="🌍 Geo: Esperando...", bg="white", font=("Segoe UI", 11))
        self.lbl_geo.grid(row=0, column=1, sticky="w", pady=5, padx=20)
        
        self.lbl_isp = tk.Label(self.dashboard, text="🏢 ISP: Esperando...", bg="white", font=("Segoe UI", 11))
        self.lbl_isp.grid(row=1, column=0, columnspan=2, sticky="w", pady=5, padx=20)

        frame_tabla = tk.Frame(self.pestania_red)
        frame_tabla.pack(fill="both", expand=True, padx=25, pady=10)
        scroll = ttk.Scrollbar(frame_tabla)
        self.tabla_red = ttk.Treeview(frame_tabla, columns=("puerto", "servicio", "estado", "banner"), show="headings", yscrollcommand=scroll.set)
        scroll.config(command=self.tabla_red.yview)
        
        self.tabla_red.heading("puerto", text="PUERTO")
        self.tabla_red.heading("servicio", text="SERVICIO")
        self.tabla_red.heading("estado", text="ESTADO")
        self.tabla_red.heading("banner", text="BANNER GRABBING (INFO)")
        
        self.tabla_red.column("puerto", width=80, anchor="center")
        self.tabla_red.column("servicio", width=120, anchor="center")
        self.tabla_red.column("estado", width=120, anchor="center")
        self.tabla_red.column("banner", width=400)
        
        self.tabla_red.tag_configure('abierto', background='#d4edda', foreground='#155724')
        self.tabla_red.tag_configure('cerrado', background='#f8d7da', foreground='#721c24')
        
        scroll.pack(side="right", fill="y")
        self.tabla_red.pack(side="left", fill="both", expand=True)

    def iniciar_auditoria_red(self):
        objetivo = self.input_red.get().strip()
        if not objetivo: return
        
        for item in self.tabla_red.get_children(): self.tabla_red.delete(item)
        self.lbl_ip.config(text="📍 IP: Resolviendo...")
        self.lbl_geo.config(text="🌍 Geo: Buscando...")
        self.lbl_isp.config(text="🏢 ISP: Consultando...")
        self.progreso_red['value'] = 0
        self.btn_auditar.config(state="disabled")
        
        threading.Thread(target=self.proceso_auditoria_red, args=(objetivo,), daemon=True).start()

    def proceso_auditoria_red(self, objetivo):
        try:
            ip_objetivo = socket.gethostbyname(objetivo)
            self.ventana.after(0, lambda: self.lbl_ip.config(text=f"📍 IP: {ip_objetivo}"))
            
            try:
                r_geo = self.sesion.get(f"http://ip-api.com/json/{ip_objetivo}", timeout=5).json()
                if r_geo['status'] == 'success':
                    self.ventana.after(0, lambda: [
                        self.lbl_geo.config(text=f"🌍 Geo: {r_geo.get('city', 'N/A')}, {r_geo.get('country', 'N/A')}"),
                        self.lbl_isp.config(text=f"🏢 ISP: {r_geo.get('isp', 'N/A')} ({r_geo.get('org', 'N/A')})")
                    ])
            except: pass
            
            puertos_clave = {
                21:"FTP", 22:"SSH", 23:"Telnet", 25:"SMTP", 53:"DNS", 
                80:"HTTP", 110:"POP3", 443:"HTTPS", 3306:"MySQL", 3389:"RDP", 8080:"HTTP-Proxy"
            }
            progreso_paso = 100 / len(puertos_clave)
            
            for i, (puerto, servicio) in enumerate(puertos_clave.items()):
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.8) 
                res = s.connect_ex((ip_objetivo, puerto))
                
                estado = "Cerrado / Filtrado"
                tag_color = "cerrado"
                banner = "-"
                
                if res == 0:
                    estado = "Abierto"
                    tag_color = "abierto"
                    
                    try:
                        if puerto in [80, 443, 8080]: 
                            s.sendall(b"HEAD / HTTP/1.1\r\n\r\n")
                        datos = s.recv(1024).decode('utf-8', errors='ignore').strip().split('\n')[0]
                        if datos: banner = datos[:70] 
                    except: 
                        banner = "Servicio Activo (No provee banner)"
                        
                    # INTELIGENCIA ACCIONABLE: Solo guardamos los puertos que están abiertos
                    self.lista_resultados.append({"Modulo": "Infraestructura de Red", "Target": ip_objetivo, "Info": f"Puerto {puerto} ({servicio}) Abierto. Banner detectado: {banner}", "Fecha": time.strftime('%H:%M:%S')})
                
                self.ventana.after(0, lambda pt=puerto, sv=servicio, es=estado, bn=banner, tc=tag_color, pr=(i+1)*progreso_paso: [
                    self.tabla_red.insert("", "end", values=(pt, sv, es, bn), tags=(tc,)),
                    self.progreso_red.config(value=pr)
                ])
                s.close()
                
        except socket.gaierror:
            self.ventana.after(0, lambda: messagebox.showerror("Error DNS", "Dominio invalido o sin conexion."))
        finally:
            self.ventana.after(0, lambda: [self.btn_auditar.config(state="normal"), self.progreso_red.config(value=100)])

    # =========================================================================
    # MODULO 5: INFORME
    # =========================================================================
    def UI_reporte(self):
        panel = tk.Frame(self.pestania_rep, bg="white", padx=50, pady=50)
        panel.pack(expand=True)
        tk.Label(panel, text="📁 Generador de Informes OSINT", font=("Segoe UI", 18, "bold"), bg="white").pack(pady=20)
        tk.Label(panel, text="Extrae únicamente los hallazgos positivos y evidencias clave.", font=("Segoe UI", 10), bg="white", fg="gray").pack(pady=(0,20))
        tk.Button(panel, text="📄 Exportar Informe Final (TXT)", bg="#34495e", fg="white", font=("Segoe UI", 11, "bold"), width=40, height=2, command=self.generar_informe_txt).pack(pady=10)

    def generar_informe_txt(self):
        if not self.lista_resultados:
            messagebox.showwarning("Informe Vacío", "No se han encontrado evidencias relevantes para exportar aún.")
            return
            
        ruta = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Archivo de Texto", "*.txt")], title="Guardar Informe OSINT")
        if ruta:
            try:
                with open(ruta, 'w', encoding='utf-8') as f:
                    f.write("====================================================================\n")
                    f.write("          INFORME DE INTELIGENCIA - INVESTIGADOR DIGITAL \n")
                    f.write("====================================================================\n")
                    f.write(f"Fecha y Hora de Auditoría: {time.strftime('%d/%m/%Y %H:%M:%S')}\n\n")

                    # Agrupamos la inteligencia recolectada por módulos para facilitar la lectura
                    modulos_ordenados = {}
                    for item in self.lista_resultados:
                        mod = item["Modulo"]
                        if mod not in modulos_ordenados:
                            modulos_ordenados[mod] = []
                        modulos_ordenados[mod].append(item)

                    for mod, items in modulos_ordenados.items():
                        f.write(f"--- [ {mod.upper()} ] ---\n")
                        for item in items:
                            f.write(f"  > [{item['Fecha']}] OBJETIVO: {item['Target']}\n")
                            f.write(f"    EVIDENCIA: {item['Info']}\n\n")

                    f.write("====================================================================\n")
                    f.write("FIN DEL INFORME\n")
                    
                messagebox.showinfo("Éxito", "El informe TXT se ha guardado con los hallazgos positivos.")
            except Exception as e:
                messagebox.showerror("Error al guardar", f"No se pudo escribir el archivo: {e}")

    def dibujar_interfaz(self):
        header = tk.Frame(self.ventana, bg="#1a73e8", height=60)
        header.pack(fill="x")
        tk.Label(header, text="SUITE OSINT 2026", fg="white", bg="#1a73e8", font=("Segoe UI", 14, "bold")).pack(pady=15)
        
        self.tabs = ttk.Notebook(self.ventana)
        self.pestania_google = tk.Frame(self.tabs, bg="#f0f2f5")
        self.pestania_social = tk.Frame(self.tabs, bg="#f0f2f5")
        self.pestania_img = tk.Frame(self.tabs, bg="#f0f2f5")
        self.pestania_red = tk.Frame(self.tabs, bg="#f0f2f5")
        self.pestania_rep = tk.Frame(self.tabs, bg="#f0f2f5")
        
        self.tabs.add(self.pestania_google, text=" Identidad ")
        self.tabs.add(self.pestania_social, text=" Redes ")
        self.tabs.add(self.pestania_img, text=" Imagen ")
        self.tabs.add(self.pestania_red, text=" Red/IP ")
        self.tabs.add(self.pestania_rep, text=" Informe ")
        
        self.tabs.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.UI_busqueda()
        self.UI_social()
        self.UI_imagenes()
        self.UI_red()
        self.UI_reporte()

if __name__ == "__main__":
    root = tk.Tk()
    app = SuiteOSINT(root)
    root.mainloop()
