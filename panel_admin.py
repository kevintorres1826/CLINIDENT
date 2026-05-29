import sqlite3
import os
import sys  # <-- Importante para detectar el entorno del ejecutable
import customtkinter as ctk
from tkinter import messagebox, ttk

# Configuración estética avanzada
ctk.set_appearance_mode("Dark")  
ctk.set_default_color_theme("blue")

# =========================================================================
# DETECCIÓN DE RUTA PARA ENTORNO PORTABLE (EXE Y DB JUNTOS EN LA MISMA CARPETA)
# =========================================================================
if getattr(sys, 'frozen', False):
    # Si es el ejecutable (.exe), obtiene la carpeta exterior real donde vive el archivo ejecutable
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Si se ejecuta desde VS Code (entorno de desarrollo)
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(BASE_DIR, "clinident.db")
# =========================================================================

class AdminApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("CLINIDENT — Ultra Premium Admin Suite")
        self.geometry("1120x670")
        self.resizable(False, False)
        
        self.usuario_seleccionado_id = None
        self.configure(fg_color="#18181c") # Fondo gris oscuro profundo
        
        self.mostrar_login_cinematico()

    def conectar_db(self):
        return sqlite3.connect(DB_PATH)

    # ==========================================
    # MOTOR DE ANIMACIONES CON CURVA DE ATENUACIÓN (EASE-OUT)
    # ==========================================
    def animar_panel_ease_out(self, widget, destino_x, inicio_x, y_fijo):
        """ Desliza un panel usando desaceleración fluida """
        widget.place(x=inicio_x, y=y_fijo)
        
        def paso():
            if not widget.winfo_exists(): 
                return
            x_actual = widget.winfo_x()
            distancia = destino_x - x_actual
            
            if abs(distancia) < 1:
                widget.place(x=destino_x, y=y_fijo)
                return
                
            siguiente_x = x_actual + (distancia * 0.15) 
            widget.place(x=siguiente_x, y=y_fijo)
            self.after(12, paso)
            
        paso()

    def animar_login_ease_out(self, widget, destino_y, inicio_y):
        """ Desliza verticalmente el login con efecto amortiguado """
        widget.place(relx=0.5, rely=inicio_y, anchor="center")
        
        def paso():
            if not widget.winfo_exists(): 
                return
            y_actual_px = widget.winfo_y() + (widget.winfo_height() / 2)
            destino_y_px = self.winfo_height() * destino_y
            
            distancia = destino_y_px - y_actual_px
            
            if abs(distancia) < 1:
                widget.place(relx=0.5, rely=destino_y, anchor="center")
                return
                
            nueva_y_px = y_actual_px + (distancia * 0.12)
            rely_calculado = nueva_y_px / self.winfo_height()
            
            widget.place(relx=0.5, rely=rely_calculado, anchor="center")
            self.after(12, paso)
            
        self.after(100, paso)

    # ==========================================
    # VISTA 1: LOGIN CINEMÁTICO
    # ==========================================
    def mostrar_login_cinematico(self):
        self.frame_login = ctk.CTkFrame(self, width=460, height=480, corner_radius=24, fg_color="#22222b", border_width=1, border_color="#30303a")
        
        lbl_titulo = ctk.CTkLabel(self.frame_login, text="CLINIDENT", font=("Segoe UI", 38, "bold"), text_color="#00ffff")
        lbl_titulo.pack(pady=(50, 5))
        
        lbl_sub = ctk.CTkLabel(self.frame_login, text="Ecosistema Global de Administración", font=("Segoe UI", 13), text_color="#707080")
        lbl_sub.pack(pady=(0, 40))
        
        self.txt_email = ctk.CTkEntry(self.frame_login, placeholder_text="Correo Electrónico", width=330, height=48, font=("Segoe UI", 14), corner_radius=12, border_color="#30303a", fg_color="#141419", text_color="#ffffff", border_width=2)
        self.txt_email.pack(pady=12)
        
        self.txt_pass = ctk.CTkEntry(self.frame_login, placeholder_text="Contraseña", show="*", width=330, height=48, font=("Segoe UI", 14), corner_radius=12, border_color="#30303a", fg_color="#141419", text_color="#ffffff", border_width=2)
        self.txt_pass.pack(pady=12)
        
        btn_ingresar = ctk.CTkButton(
            self.frame_login, 
            text="Acceder al Panel", 
            command=self.procesar_login, 
            width=330, 
            height=48, 
            font=("Segoe UI", 15, "bold"), 
            corner_radius=12,
            fg_color="#00ffff", 
            hover_color="#00b3b3",
            text_color="#141419"
        )
        btn_ingresar.pack(pady=40)

        self.animar_login_ease_out(self.frame_login, destino_y=0.5, inicio_y=1.2)

    def procesar_login(self):
        email = self.txt_email.get().strip()
        password = self.txt_pass.get()
        
        if not email or not password:
            messagebox.showwarning("Campos Vacíos", "Introduzca sus credenciales.")
            return
            
        try:
            conn = self.conectar_db()
            cursor = conn.cursor()
            cursor.execute("SELECT nombre, apellido FROM tblusuario WHERE correo=? AND contrasena=? AND id_rol=1", (email, password))
            admin = cursor.fetchone()
            conn.close()
            
            if admin:
                self.frame_login.destroy()
                self.mostrar_dashboard_premium()
            else:
                messagebox.showerror("Denegado", "Usuario no válido o sin permisos de Administrador.")
        except sqlite3.Error as e:
            messagebox.showerror("Error de Base de Datos", f"Fallo al buscar base de datos en: {DB_PATH}\nError: {e}")

    # ==========================================
    # VISTA 2: DASHBOARD AVANZADO (EDICIÓN TOTAL)
    # ==========================================
    def mostrar_dashboard_premium(self):
        # Panel izquierdo (Tabla)
        self.frame_tabla = ctk.CTkFrame(self, width=740, height=620, corner_radius=20, fg_color="#1d1d24", border_width=1, border_color="#2a2a35")
        
        lbl_tabla = ctk.CTkLabel(self.frame_tabla, text="Consola de Control de Usuarios", font=("Segoe UI", 18, "bold"), text_color="#ffffff")
        lbl_tabla.pack(pady=(20, 10))
        
        # Preloader animado
        self.progreso_carga = ctk.CTkProgressBar(self.frame_tabla, width=700, height=3, fg_color="#141419", progress_color="#00ffff")
        self.progreso_carga.pack(padx=20, pady=(0, 10))
        self.progreso_carga.set(0)

        estilo = ttk.Style()
        estilo.theme_use("clam")
        estilo.configure(
            "Treeview", 
            background="#141419", 
            foreground="#d0d0d5", 
            fieldbackground="#141419", 
            rowheight=34, 
            font=("Segoe UI", 12),
            borderwidth=0
        )
        estilo.configure("Treeview.Heading", font=("Segoe UI", 12, "bold"), background="#252530", foreground="#ffffff", relief="flat")
        estilo.map('Treeview', background=[('selected', '#303045')], foreground=[('selected', '#00ffff')])
        
        self.tabla = ttk.Treeview(self.frame_tabla, columns=("ID", "Nombre", "Email", "Rol"), show='headings', height=14)
        self.tabla.heading("ID", text="ID")
        self.tabla.heading("Nombre", text="Nombre Completo")
        self.tabla.heading("Email", text="Dirección de Correo")
        self.tabla.heading("Rol", text="Rol")
        
        self.tabla.column("ID", width=60, anchor="center")
        self.tabla.column("Nombre", width=230)
        self.tabla.column("Email", width=330)
        self.tabla.column("Rol", width=80, anchor="center")
        
        self.tabla.pack(padx=20, pady=5, fill="both", expand=True)
        self.tabla.bind("<<TreeviewSelect>>", self.cargar_usuario_formulario)
        
        # Panel Derecho (Formulario de Ficha)
        self.frame_form = ctk.CTkFrame(self, width=320, height=620, corner_radius=20, fg_color="#1d1d24", border_width=1, border_color="#2a2a35")
        
        lbl_form = ctk.CTkLabel(self.frame_form, text="Ficha de Edición Total", font=("Segoe UI", 18, "bold"), text_color="#00ffff")
        lbl_form.pack(pady=(20, 5))
        
        # Campos de Texto Inteligentes
        self.edit_nombre = ctk.CTkEntry(self.frame_form, placeholder_text="Nombre", width=280, height=42, font=("Segoe UI", 13), corner_radius=10, border_color="#2a2a35", fg_color="#141419")
        self.edit_nombre.pack(pady=8)
        
        self.edit_apellido = ctk.CTkEntry(self.frame_form, placeholder_text="Apellido", width=280, height=42, font=("Segoe UI", 13), corner_radius=10, border_color="#2a2a35", fg_color="#141419")
        self.edit_apellido.pack(pady=8)
        
        self.edit_email = ctk.CTkEntry(self.frame_form, placeholder_text="Correo Electrónico", width=280, height=42, font=("Segoe UI", 13), corner_radius=10, border_color="#2a2a35", fg_color="#141419")
        self.edit_email.pack(pady=8)
        
        self.edit_telefono = ctk.CTkEntry(self.frame_form, placeholder_text="Teléfono Celular", width=280, height=42, font=("Segoe UI", 13), corner_radius=10, border_color="#2a2a35", fg_color="#141419")
        self.edit_telefono.pack(pady=8)
        
        lbl_rol = ctk.CTkLabel(self.frame_form, text="Privilegios asignados:", font=("Segoe UI", 13, "bold"), text_color="#a0a0b0")
        lbl_rol.pack(pady=(15, 5))
        
        self.opciones_roles = ["1 - Administrador", "2 - Odontólogo", "3 - Recepcionista", "4 - Paciente"]
        self.edit_rol = ctk.CTkOptionMenu(self.frame_form, values=self.opciones_roles, width=280, height=40, font=("Segoe UI", 13), corner_radius=10, fg_color="#252530", button_color="#303040")
        self.edit_rol.pack(pady=5)
        
        self.btn_guardar = ctk.CTkButton(self.frame_form, text="Guardar Todo en DB", command=self.actualizar_usuario, fg_color="#00ffff", hover_color="#00b3b3", text_color="#141419", width=280, height=46, font=("Segoe UI", 14, "bold"), corner_radius=10)
        self.btn_guardar.pack(pady=35)
        
        # Ejecutar animaciones de entrada amortiguada
        self.animar_panel_ease_out(self.frame_tabla, destino_x=20, inicio_x=-800, y_fijo=25)
        self.animar_panel_ease_out(self.frame_form, destino_x=780, inicio_x=1400, y_fijo=25)
        
        self.animar_barra_y_cargar()

    # ==========================================
    # ANIMACIÓN DE PRECARGA E INYECCIÓN DE DATOS
    # ==========================================
    def animar_barra_y_cargar(self):
        def paso(progreso):
            if not self.progreso_carga.winfo_exists():
                return
            if progreso <= 1.0:
                self.progreso_carga.set(progreso)
                self.after(10, lambda: paso(progreso + 0.05))
            else:
                self.progreso_carga.configure(progress_color="#1d1d24")
                self.cargar_usuarios_db()
        paso(0.0)

    def cargar_usuarios_db(self):
        for i in self.tabla.get_children():
            self.tabla.delete(i)
        try:
            conn = self.conectar_db()
            cursor = conn.cursor()
            cursor.execute("SELECT id_usuario, nombre, apellido, correo, id_rol FROM tblusuario")
            for row in cursor.fetchall():
                nombre_completo = f"{row[1]} {row[2]}"
                self.tabla.insert("", "end", values=(row[0], nombre_completo, row[3], row[4]))
            conn.close()
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Fallo al conectar: {e}")

    def cargar_usuario_formulario(self, event):
        seleccion = self.tabla.selection()
        if not seleccion:
            return
            
        item = self.tabla.item(seleccion[0])
        self.usuario_seleccionado_id = item['values'][0]
        
        try:
            conn = self.conectar_db()
            cursor = conn.cursor()
            cursor.execute("SELECT nombre, apellido, correo, telefono, id_rol FROM tblusuario WHERE id_usuario=?", (self.usuario_seleccionado_id,))
            usuario = cursor.fetchone()
            conn.close()
            
            if usuario:
                self.edit_nombre.delete(0, "end")
                self.edit_nombre.insert(0, usuario[0] if usuario[0] else "")
                
                self.edit_apellido.delete(0, "end")
                self.edit_apellido.insert(0, usuario[1] if usuario[1] else "")
                
                self.edit_email.delete(0, "end")
                self.edit_email.insert(0, usuario[2] if usuario[2] else "")
                
                self.edit_telefono.delete(0, "end")
                self.edit_telefono.insert(0, usuario[3] if usuario[3] else "")
                
                rol_actual = usuario[4]
                for opcion in self.opciones_roles:
                    if opcion.startswith(str(rol_actual)):
                        self.edit_rol.set(opcion)
                        break
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error al recuperar detalles: {e}")

    # ==========================================
    # SOLUCIÓN CRÍTICA: ACTUALIZACIÓN MULTI-CAMPO CORREGIDA
    # ==========================================
    def actualizar_usuario(self):
        if not self.usuario_seleccionado_id:
            messagebox.showwarning("Atención", "Seleccione primero un usuario de la lista de la izquierda.")
            return
            
        nom = self.edit_nombre.get().strip()
        ape = self.edit_apellido.get().strip()
        email = self.edit_email.get().strip()
        tel = self.edit_telefono.get().strip()
        
        try:
            rol_seleccionado = int(self.edit_rol.get().split("-")[0].strip())
        except ValueError:
            messagebox.showerror("Error", "Rol no seleccionado o inválido.")
            return

        if not nom or not ape or not email:
            messagebox.showwarning("Requerido", "Los campos Nombre, Apellido y Correo electrónico no pueden estar vacíos.")
            return

        try:
            conn = self.conectar_db()
            cursor = conn.cursor()
            
            cursor.execute("PRAGMA foreign_keys = ON;")
            
            cursor.execute("""
                UPDATE tblusuario 
                SET nombre = ?, 
                    apellido = ?, 
                    correo = ?, 
                    telefono = ?, 
                    id_rol = ? 
                WHERE id_usuario = ?
            """, (nom, ape, email, tel, rol_seleccionado, self.usuario_seleccionado_id))
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Éxito Completo", "¡Todos los campos del usuario se han actualizado correctamente en la base de datos!")
            
            self.progreso_carga.configure(progress_color="#00ffff")
            self.animar_barra_y_cargar()
            
        except sqlite3.Error as e:
            messagebox.showerror("Error de persistencia", f"La base de datos rechazó los cambios: {e}")

if __name__ == "__main__":
    app = AdminApp()
    app.mainloop()