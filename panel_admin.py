import sqlite3
import os
import customtkinter as ctk
from tkinter import messagebox, ttk, Canvas, Scrollbar

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

import sys

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(BASE_DIR, "clinident.db")

ROLES = {1: "Administrador", 2: "Odontólogo", 3: "Recepcionista", 4: "Paciente"}

# id_tipo (tbltipotratamiento) -> nombre del servicio
TRATAMIENTOS_ODONTOLOGO = {
    1: "Limpieza dental",
    2: "Ortodoncia",
    3: "Endodoncia",
    4: "Cirugía oral",
    5: "Revisión general",
}

ID_ROL_ODONTOLOGO = 2


class AdminApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("CLINIDENT — Ultra Premium Admin Suite")
        self.geometry("1280x720")
        self.resizable(False, False)
        self.usuario_seleccionado_id = None
        self.configure(fg_color="#18181c")
        self.mostrar_login_cinematico()

    def conectar_db(self):
        # timeout=15 -> si la BD está ocupada (locked) por otro proceso/conexión,
        # espera hasta 15s reintentando en vez de fallar al instante (default: 5s).
        conn = sqlite3.connect(DB_PATH, timeout=15)
        # WAL permite que lecturas y escrituras convivan mejor entre procesos
        # (ej. este panel y el servidor Flask de main.py) reduciendo los locks.
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout=15000;")
        return conn

    def asegurar_consultorio_para_doctor(self, cursor, id_odontologo):
        """
        Garantiza que el odontólogo tenga su propio consultorio asignado
        en tblodontologo_sala. Si no lo tiene, crea un nuevo registro en
        tblsala llamado "Consultorio N" (siguiente número disponible) y
        lo vincula. Se llama justo al guardar, para no depender de un
        reinicio del servidor Flask.
        """
        cursor.execute(
            "SELECT id_sala FROM tblodontologo_sala WHERE id_odontologo = ?",
            (id_odontologo,)
        )
        if cursor.fetchone():
            return  # Ya tiene consultorio, no hacer nada

        cursor.execute(
            "SELECT nombre_sala FROM tblsala WHERE nombre_sala LIKE 'Consultorio %'"
        )
        existentes = [r[0] for r in cursor.fetchall()]
        numeros_usados = []
        for nombre in existentes:
            try:
                numeros_usados.append(int(nombre.replace("Consultorio ", "").strip()))
            except ValueError:
                pass
        siguiente_numero = (max(numeros_usados) + 1) if numeros_usados else 1

        nombre_sala = f"Consultorio {siguiente_numero}"
        cursor.execute(
            "INSERT INTO tblsala (nombre_sala, disponibilidad) VALUES (?, 1)",
            (nombre_sala,)
        )
        id_sala_nueva = cursor.lastrowid
        cursor.execute(
            "INSERT INTO tblodontologo_sala (id_odontologo, id_sala) VALUES (?, ?)",
            (id_odontologo, id_sala_nueva)
        )
        print(f"✅ Odontólogo {id_odontologo} → {nombre_sala} (id_sala {id_sala_nueva}) creado al guardar.")

    # ── ANIMACIONES ──────────────────────────────────────────────────────────
    def animar_panel_ease_out(self, widget, destino_x, inicio_x, y_fijo):
        widget.place(x=inicio_x, y=y_fijo)
        def paso():
            if not widget.winfo_exists(): return
            x_actual  = widget.winfo_x()
            distancia = destino_x - x_actual
            if abs(distancia) < 1:
                widget.place(x=destino_x, y=y_fijo); return
            widget.place(x=x_actual + distancia * 0.15, y=y_fijo)
            self.after(12, paso)
        paso()

    def animar_login_ease_out(self, widget, destino_y, inicio_y):
        widget.place(relx=0.5, rely=inicio_y, anchor="center")
        def paso():
            if not widget.winfo_exists(): return
            y_px      = widget.winfo_y() + widget.winfo_height() / 2
            dest_px   = self.winfo_height() * destino_y
            distancia = dest_px - y_px
            if abs(distancia) < 1:
                widget.place(relx=0.5, rely=destino_y, anchor="center"); return
            widget.place(relx=0.5,
                         rely=(y_px + distancia * 0.12) / self.winfo_height(),
                         anchor="center")
            self.after(12, paso)
        self.after(100, paso)

    # ── LOGIN ────────────────────────────────────────────────────────────────
    def mostrar_login_cinematico(self):
        self.frame_login = ctk.CTkFrame(self, width=460, height=480, corner_radius=24,
                                        fg_color="#22222b", border_width=1, border_color="#30303a")
        ctk.CTkLabel(self.frame_login, text="CLINIDENT",
                     font=("Segoe UI", 38, "bold"), text_color="#00ffff").pack(pady=(50, 5))
        ctk.CTkLabel(self.frame_login, text="Ecosistema Global de Administración",
                     font=("Segoe UI", 13), text_color="#707080").pack(pady=(0, 40))
        self.txt_email = ctk.CTkEntry(self.frame_login, placeholder_text="Correo Electrónico",
                                      width=330, height=48, font=("Segoe UI", 14), corner_radius=12,
                                      border_color="#30303a", fg_color="#141419",
                                      text_color="#ffffff", border_width=2)
        self.txt_email.pack(pady=12)
        self.txt_pass = ctk.CTkEntry(self.frame_login, placeholder_text="Contraseña", show="*",
                                     width=330, height=48, font=("Segoe UI", 14), corner_radius=12,
                                     border_color="#30303a", fg_color="#141419",
                                     text_color="#ffffff", border_width=2)
        self.txt_pass.pack(pady=12)
        ctk.CTkButton(self.frame_login, text="Acceder al Panel", command=self.procesar_login,
                      width=330, height=48, font=("Segoe UI", 15, "bold"), corner_radius=12,
                      fg_color="#00ffff", hover_color="#00b3b3", text_color="#141419").pack(pady=40)
        self.animar_login_ease_out(self.frame_login, destino_y=0.5, inicio_y=1.2)

    def procesar_login(self):
        email    = self.txt_email.get().strip()
        password = self.txt_pass.get()
        if not email or not password:
            messagebox.showwarning("Campos Vacíos", "Introduzca sus credenciales."); return
        try:
            conn = self.conectar_db(); cursor = conn.cursor()
            # Admin: acepta quien tenga rol 1 en tblusuario_rol O en id_rol legacy
            cursor.execute("""
                SELECT u.id_usuario, u.nombre
                FROM tblusuario u
                WHERE u.correo = ? AND u.contrasena = ?
                  AND u.estado = 'Activo'
                  AND (
                      u.id_rol = 1
                      OR EXISTS (
                          SELECT 1 FROM tblusuario_rol ur
                          WHERE ur.id_usuario = u.id_usuario AND ur.id_rol = 1
                      )
                  )
            """, (email, password))
            admin = cursor.fetchone(); conn.close()
            if admin:
                self.frame_login.destroy()
                self.mostrar_dashboard_premium()
            else:
                messagebox.showerror("Denegado", "Usuario no válido o sin permisos de Administrador.")
        except sqlite3.Error as e:
            messagebox.showerror("Error de Base de Datos", f"Fallo: {e}")

    # ── DASHBOARD ────────────────────────────────────────────────────────────
    def mostrar_dashboard_premium(self):
        # Panel izquierdo — tabla
        self.frame_tabla = ctk.CTkFrame(self, width=700, height=670, corner_radius=20,
                                        fg_color="#1d1d24", border_width=1, border_color="#2a2a35")
        ctk.CTkLabel(self.frame_tabla, text="Consola de Control de Usuarios",
                     font=("Segoe UI", 18, "bold"), text_color="#ffffff").pack(pady=(20, 10))

        self.progreso_carga = ctk.CTkProgressBar(self.frame_tabla, width=660, height=3,
                                                 fg_color="#141419", progress_color="#00ffff")
        self.progreso_carga.pack(padx=20, pady=(0, 10))
        self.progreso_carga.set(0)

        estilo = ttk.Style(); estilo.theme_use("clam")
        estilo.configure("Treeview", background="#141419", foreground="#d0d0d5",
                         fieldbackground="#141419", rowheight=34, font=("Segoe UI", 12), borderwidth=0)
        estilo.configure("Treeview.Heading", font=("Segoe UI", 12, "bold"),
                         background="#252530", foreground="#ffffff", relief="flat")
        estilo.map("Treeview", background=[("selected", "#303045")], foreground=[("selected", "#00ffff")])

        cols = ("ID", "Nombre", "Email", "Tel", "Roles", "Estado")
        self.tabla = ttk.Treeview(self.frame_tabla, columns=cols, show="headings", height=14)
        for col, w in zip(cols, [45, 185, 205, 105, 115, 65]):
            self.tabla.heading(col, text=col)
            self.tabla.column(col, width=w,
                              anchor="center" if col in ("ID", "Estado") else "w")
        self.tabla.pack(padx=20, pady=5, fill="both", expand=True)
        self.tabla.bind("<<TreeviewSelect>>", self.cargar_usuario_formulario)

        # Panel derecho — formulario con canvas+scrollbar
        self.frame_form_outer = ctk.CTkFrame(self, width=530, height=670, corner_radius=20,
                                             fg_color="#1d1d24", border_width=1, border_color="#2a2a35")
        self._canvas = Canvas(self.frame_form_outer, bg="#1d1d24", highlightthickness=0,
                              width=510, height=630)
        self._scrollbar = Scrollbar(self.frame_form_outer, orient="vertical",
                                    command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=self._scrollbar.set)
        self._scrollbar.pack(side="right", fill="y", pady=10)
        self._canvas.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)

        self.frame_form = ctk.CTkFrame(self._canvas, fg_color="#1d1d24")
        self._canvas_window = self._canvas.create_window((0, 0), window=self.frame_form, anchor="nw")
        self.frame_form.bind("<Configure>", lambda e: self._canvas.configure(
            scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Enter>",
            lambda e: self._canvas.bind_all("<MouseWheel>", self._on_mousewheel))
        self._canvas.bind("<Leave>",
            lambda e: self._canvas.unbind_all("<MouseWheel>"))

        # ── Widgets del formulario ────────────────────────────────────────
        def seccion(texto, parent=None):
            ctk.CTkLabel(parent or self.frame_form, text=texto, font=("Segoe UI", 12, "bold"),
                         text_color="#00cccc").pack(anchor="w", padx=16, pady=(14, 2))

        def campo(placeholder, show=""):
            e = ctk.CTkEntry(self.frame_form, placeholder_text=placeholder,
                             width=460, height=42, font=("Segoe UI", 13), corner_radius=10,
                             border_color="#2a2a35", fg_color="#141419",
                             text_color="#ffffff", show=show)
            e.pack(pady=4, padx=16)
            return e

        ctk.CTkLabel(self.frame_form, text="Ficha de Edición Total",
                     font=("Segoe UI", 18, "bold"), text_color="#00ffff").pack(pady=(20, 4))
        ctk.CTkLabel(self.frame_form, text="Deja vacío un campo para guardarlo como NULL",
                     font=("Segoe UI", 11), text_color="#505060").pack(pady=(0, 14))

        seccion("▸ Datos Personales")
        self.edit_nombre   = campo("Nombre")
        self.edit_apellido = campo("Apellido")
        self.edit_email    = campo("Correo Electrónico")
        self.edit_telefono = campo("Teléfono Celular")

        seccion("▸ Seguridad")
        ctk.CTkLabel(self.frame_form, text="Nueva contraseña  (vacío = no cambiar)",
                     font=("Segoe UI", 11), text_color="#505060").pack(anchor="w", padx=20)
        self.edit_pass1 = campo("Nueva Contraseña", show="*")
        self.edit_pass2 = campo("Confirmar Contraseña", show="*")
        self.lbl_pass_hint = ctk.CTkLabel(self.frame_form, text="",
                                          font=("Segoe UI", 11), text_color="#ef4444")
        self.lbl_pass_hint.pack(pady=(0, 4))
        self.edit_pass1.bind("<KeyRelease>", self._check_pass_match)
        self.edit_pass2.bind("<KeyRelease>", self._check_pass_match)

        # ── Roles: checkboxes múltiples ───────────────────────────────────
        seccion("▸ Roles Asignados  (puede marcar varios)")
        self.check_roles = {}
        for id_rol, nombre_rol in ROLES.items():
            var = ctk.BooleanVar(value=False)
            # El checkbox de Odontólogo necesita disparar el panel de servicios
            if id_rol == ID_ROL_ODONTOLOGO:
                cb = ctk.CTkCheckBox(self.frame_form, text=nombre_rol, variable=var,
                                     font=("Segoe UI", 13), text_color="#d0d0d5",
                                     fg_color="#00ffff", hover_color="#00b3b3",
                                     checkmark_color="#141419", width=460,
                                     command=self._toggle_panel_servicios)
            else:
                cb = ctk.CTkCheckBox(self.frame_form, text=nombre_rol, variable=var,
                                     font=("Segoe UI", 13), text_color="#d0d0d5",
                                     fg_color="#00ffff", hover_color="#00b3b3",
                                     checkmark_color="#141419", width=460)
            cb.pack(anchor="w", padx=28, pady=3)
            self.check_roles[id_rol] = var

        # ── NUEVO: panel de servicios para Odontólogo (oculto por defecto) ──
        # Se muestra/oculta dinámicamente al marcar/desmarcar "Odontólogo".
        self.frame_servicios = ctk.CTkFrame(self.frame_form, fg_color="#141419",
                                            corner_radius=12, border_width=1,
                                            border_color="#2a2a35")
        seccion("🦷  Servicios que atiende este Odontólogo", parent=self.frame_servicios)
        ctk.CTkLabel(self.frame_servicios,
                     text="Marca los tratamientos que este especialista puede atender",
                     font=("Segoe UI", 11), text_color="#505060").pack(anchor="w", padx=16, pady=(0, 8))

        self.check_servicios = {}
        for id_tipo, nombre_servicio in TRATAMIENTOS_ODONTOLOGO.items():
            var = ctk.BooleanVar(value=False)
            cb = ctk.CTkCheckBox(self.frame_servicios, text=nombre_servicio, variable=var,
                                 font=("Segoe UI", 13), text_color="#d0d0d5",
                                 fg_color="#00cccc", hover_color="#009999",
                                 checkmark_color="#141419", width=420)
            cb.pack(anchor="w", padx=32, pady=3)
            self.check_servicios[id_tipo] = var
        # NOTA: self.frame_servicios todavía no se ha "packeado" — eso lo
        # decide _toggle_panel_servicios() según el estado del checkbox.

        seccion("▸ Estado de la Cuenta")
        self.edit_estado = ctk.CTkOptionMenu(self.frame_form, values=["Activo", "Inactivo"],
                                             width=460, height=40, font=("Segoe UI", 13),
                                             corner_radius=10, fg_color="#252530",
                                             button_color="#303040")
        self.edit_estado.pack(pady=4, padx=16)

        ctk.CTkButton(self.frame_form, text="💾  Guardar Todo en DB",
                      command=self.actualizar_usuario,
                      fg_color="#00ffff", hover_color="#00b3b3", text_color="#141419",
                      width=460, height=48, font=("Segoe UI", 14, "bold"),
                      corner_radius=10).pack(pady=(20, 6), padx=16)

        ctk.CTkButton(self.frame_form, text="🗑  Eliminar Usuario",
                      command=self.eliminar_usuario,
                      fg_color="#3a1a1a", hover_color="#5a1a1a", text_color="#ff6060",
                      width=460, height=42, font=("Segoe UI", 13, "bold"), corner_radius=10,
                      border_width=1, border_color="#6a2a2a").pack(pady=(0, 30), padx=16)

        self.animar_panel_ease_out(self.frame_tabla,      destino_x=20,  inicio_x=-800, y_fijo=25)
        self.animar_panel_ease_out(self.frame_form_outer, destino_x=735, inicio_x=1400, y_fijo=25)
        self.animar_barra_y_cargar()

    # ── NUEVO: mostrar / ocultar el panel de servicios ───────────────────────
    def _toggle_panel_servicios(self):
        """
        Muestra el bloque de checkboxes de servicios justo debajo de los
        roles cuando se marca 'Odontólogo'; lo oculta (sin perder las
        marcas internas) cuando se desmarca.
        """
        if self.check_roles[ID_ROL_ODONTOLOGO].get():
            # pack_forget() previo evita duplicar si ya estaba visible
            self.frame_servicios.pack_forget()
            self.frame_servicios.pack(fill="x", padx=16, pady=(6, 4), after=self._ultimo_widget_roles())
        else:
            self.frame_servicios.pack_forget()

    def _ultimo_widget_roles(self):
        """Devuelve el último checkbox de rol en el formulario, para anclar
        el panel de servicios justo debajo de la lista de roles."""
        ids_ordenados = list(ROLES.keys())
        ultimo_id = ids_ordenados[-1]
        # Buscamos el widget CTkCheckBox correspondiente recorriendo los hijos
        for widget in self.frame_form.winfo_children():
            if isinstance(widget, ctk.CTkCheckBox) and widget.cget("text") == ROLES[ultimo_id]:
                return widget
        return None

    def _on_mousewheel(self, event):
        self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _check_pass_match(self, _=None):
        p1, p2 = self.edit_pass1.get(), self.edit_pass2.get()
        if not p1 and not p2:
            self.lbl_pass_hint.configure(text=""); return
        if p1 == p2:
            self.lbl_pass_hint.configure(text="✔ Coinciden", text_color="#10b981")
        else:
            self.lbl_pass_hint.configure(text="✖ No coinciden", text_color="#ef4444")

    # ── CARGA ────────────────────────────────────────────────────────────────
    def animar_barra_y_cargar(self):
        def paso(p):
            if not self.progreso_carga.winfo_exists(): return
            if p <= 1.0:
                self.progreso_carga.set(p); self.after(10, lambda: paso(p + 0.05))
            else:
                self.progreso_carga.configure(progress_color="#1d1d24")
                self.cargar_usuarios_db()
        paso(0.0)

    def _roles_str(self, id_usuario, cursor):
        """Devuelve string legible con los roles del usuario."""
        cursor.execute("""
            SELECT id_rol FROM tblusuario_rol WHERE id_usuario = ?
            UNION
            SELECT id_rol FROM tblusuario WHERE id_usuario = ? AND id_rol IS NOT NULL
            ORDER BY id_rol
        """, (id_usuario, id_usuario))
        ids = list({r[0] for r in cursor.fetchall()})
        return ", ".join(ROLES.get(i, str(i)) for i in sorted(ids)) or "—"

    def cargar_usuarios_db(self):
        for i in self.tabla.get_children(): self.tabla.delete(i)
        try:
            conn = self.conectar_db(); cursor = conn.cursor()
            cursor.execute("""
                SELECT id_usuario, nombre, apellido, correo, telefono, estado
                FROM tblusuario ORDER BY id_usuario
            """)
            filas = cursor.fetchall()
            for row in filas:
                roles_txt = self._roles_str(row[0], cursor)
                self.tabla.insert("", "end", values=(
                    row[0],
                    f"{row[1] or ''} {row[2] or ''}".strip(),
                    row[3] or "—",
                    row[4] or "—",
                    roles_txt,
                    row[5] or "—"
                ))
            conn.close()
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Fallo al conectar: {e}")

    def cargar_usuario_formulario(self, event):
        sel = self.tabla.selection()
        if not sel: return
        self.usuario_seleccionado_id = self.tabla.item(sel[0])["values"][0]
        try:
            conn = self.conectar_db(); cursor = conn.cursor()
            cursor.execute("""
                SELECT nombre, apellido, correo, telefono, estado
                FROM tblusuario WHERE id_usuario = ?
            """, (self.usuario_seleccionado_id,))
            u = cursor.fetchone()
            if not u: conn.close(); return

            # Obtener roles actuales
            cursor.execute("""
                SELECT id_rol FROM tblusuario_rol WHERE id_usuario = ?
                UNION
                SELECT id_rol FROM tblusuario
                WHERE id_usuario = ? AND id_rol IS NOT NULL
            """, (self.usuario_seleccionado_id, self.usuario_seleccionado_id))
            roles_actuales = {r[0] for r in cursor.fetchall()}

            # ── NUEVO: obtener servicios actuales si es odontólogo ──────────
            cursor.execute("""
                SELECT id_tipo FROM tblodontologo_servicio WHERE id_odontologo = ?
            """, (self.usuario_seleccionado_id,))
            servicios_actuales = {r[0] for r in cursor.fetchall()}
            conn.close()

            def set_f(w, v):
                w.delete(0, "end")
                if v: w.insert(0, v)

            set_f(self.edit_nombre,   u[0])
            set_f(self.edit_apellido, u[1])
            set_f(self.edit_email,    u[2])
            set_f(self.edit_telefono, u[3])
            self.edit_pass1.delete(0, "end")
            self.edit_pass2.delete(0, "end")
            self.lbl_pass_hint.configure(text="")

            # Marcar checkboxes según roles del usuario
            for id_rol, var in self.check_roles.items():
                var.set(id_rol in roles_actuales)

            # ── NUEVO: marcar checkboxes de servicios y mostrar/ocultar panel ──
            for id_tipo, var in self.check_servicios.items():
                var.set(id_tipo in servicios_actuales)
            self._toggle_panel_servicios()

            self.edit_estado.set(u[4] if u[4] in ("Activo", "Inactivo") else "Activo")
            self._canvas.yview_moveto(0)

        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error al recuperar detalles: {e}")

    # ── GUARDAR ──────────────────────────────────────────────────────────────
    def actualizar_usuario(self):
        if not self.usuario_seleccionado_id:
            messagebox.showwarning("Atención", "Seleccione primero un usuario."); return

        nom    = self.edit_nombre.get().strip()   or None
        ape    = self.edit_apellido.get().strip()  or None
        email  = self.edit_email.get().strip()     or None
        tel    = self.edit_telefono.get().strip()  or None
        estado = self.edit_estado.get().strip()    or None

        if not nom or not ape or not email:
            messagebox.showwarning("Requerido", "Nombre, Apellido y Correo son obligatorios."); return

        # Roles seleccionados
        roles_nuevos = [id_rol for id_rol, var in self.check_roles.items() if var.get()]
        if not roles_nuevos:
            messagebox.showwarning("Roles", "El usuario debe tener al menos un rol asignado."); return
        # rol_principal = el más privilegiado (número más bajo: 1>2>3>4)
        rol_principal = min(roles_nuevos)

        # ── NUEVO: validar servicios si el usuario es Odontólogo ────────────
        es_odontologo = ID_ROL_ODONTOLOGO in roles_nuevos
        servicios_nuevos = []
        if es_odontologo:
            servicios_nuevos = [id_tipo for id_tipo, var in self.check_servicios.items() if var.get()]
            if not servicios_nuevos:
                messagebox.showwarning(
                    "Servicios",
                    "Marca al menos un servicio que este Odontólogo pueda atender."
                )
                return

        # Contraseña
        p1, p2 = self.edit_pass1.get(), self.edit_pass2.get()
        nueva_pass = None
        if p1 or p2:
            if p1 != p2:
                messagebox.showerror("Error", "Las contraseñas no coinciden."); return
            if len(p1) < 6:
                messagebox.showerror("Error", "Mínimo 6 caracteres."); return
            nueva_pass = p1

        try:
            conn = self.conectar_db(); cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = ON;")

            # Asegurar que la tabla exista (por si el panel admin se usa
            # antes de que app.py haya corrido sus migraciones alguna vez)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tblodontologo_sala (
                    id_odontologo INTEGER NOT NULL PRIMARY KEY,
                    id_sala       INTEGER NOT NULL UNIQUE,
                    FOREIGN KEY (id_odontologo) REFERENCES tblusuario (id_usuario) ON DELETE CASCADE ON UPDATE CASCADE,
                    FOREIGN KEY (id_sala)       REFERENCES tblsala    (id_sala)    ON UPDATE CASCADE
                );
            """)

            # Actualizar datos básicos
            if nueva_pass:
                cursor.execute("""
                    UPDATE tblusuario
                       SET nombre=?, apellido=?, correo=?, telefono=?, estado=?, contrasena=?,
                           id_rol=?
                     WHERE id_usuario=?
                """, (nom, ape, email, tel, estado, nueva_pass,
                      rol_principal, self.usuario_seleccionado_id))
            else:
                cursor.execute("""
                    UPDATE tblusuario
                       SET nombre=?, apellido=?, correo=?, telefono=?, estado=?,
                           id_rol=?
                     WHERE id_usuario=?
                """, (nom, ape, email, tel, estado,
                      rol_principal, self.usuario_seleccionado_id))

            # Reemplazar roles en tblusuario_rol
            cursor.execute("DELETE FROM tblusuario_rol WHERE id_usuario=?",
                           (self.usuario_seleccionado_id,))
            for id_rol in roles_nuevos:
                cursor.execute("INSERT INTO tblusuario_rol (id_usuario, id_rol) VALUES (?,?)",
                               (self.usuario_seleccionado_id, id_rol))

            # ── NUEVO: reemplazar servicios en tblodontologo_servicio ───────
            # Siempre se limpia primero: si el usuario deja de ser odontólogo,
            # sus asignaciones de servicio quedan eliminadas correctamente.
            cursor.execute("DELETE FROM tblodontologo_servicio WHERE id_odontologo=?",
                           (self.usuario_seleccionado_id,))
            if es_odontologo:
                for id_tipo in servicios_nuevos:
                    cursor.execute(
                        "INSERT OR IGNORE INTO tblodontologo_servicio (id_odontologo, id_tipo) VALUES (?,?)",
                        (self.usuario_seleccionado_id, id_tipo)
                    )

                # ── NUEVO: crear su consultorio propio inmediatamente,
                # sin esperar a que se reinicie app.py ────────────────────
                self.asegurar_consultorio_para_doctor(cursor, self.usuario_seleccionado_id)

            conn.commit(); conn.close()
            messagebox.showinfo("Éxito", "¡Usuario actualizado correctamente!")
            self.progreso_carga.configure(progress_color="#00ffff")
            self.animar_barra_y_cargar()

        except sqlite3.IntegrityError as e:
            messagebox.showerror("Conflicto", f"Correo o teléfono ya en uso:\n{e}")
        except sqlite3.Error as e:
            messagebox.showerror("Error de BD", str(e))

    # ── ELIMINAR ─────────────────────────────────────────────────────────────
    def eliminar_usuario(self):
        if not self.usuario_seleccionado_id:
            messagebox.showwarning("Atención", "Seleccione un usuario primero."); return
        if not messagebox.askyesno("Confirmar",
                f"¿Eliminar usuario ID {self.usuario_seleccionado_id} y TODOS sus registros "
                "relacionados (citas, tratamientos, facturas, pagos, historial clínico, etc.)?\n"
                "Esta acción no se puede deshacer."):
            return
        try:
            conn = self.conectar_db(); cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = ON;")
            uid = self.usuario_seleccionado_id

            # Borrado en cascada manual respetando foreign keys.
            # Cubre ambos roles posibles del usuario: paciente (id_usuario)
            # y odontólogo (id_odontologo), ya que tblusuario no distingue
            # el rol a nivel de esquema.

            # 1. Registros clínicos (dependen de historial clínico y odontólogo)
            cursor.execute("""
                DELETE FROM tblregistroclinico
                WHERE id_odontologo = ?
                   OR id_historial_clinico IN (
                        SELECT hc.id_historial_clinico FROM tblhistorialclinico hc
                        JOIN tblcita c ON hc.id_cita = c.id_cita
                        WHERE c.id_usuario = ? OR c.id_odontologo = ?
                   )
            """, (uid, uid, uid))

            # 2. Pagos (dependen de factura → tratamiento)
            cursor.execute("""
                DELETE FROM tblpago
                WHERE id_factura IN (
                    SELECT f.id_factura FROM tblfactura f
                    JOIN tbltratamiento t ON f.id_tratamiento = t.id_tratamiento
                    WHERE t.id_usuario = ? OR t.id_odontologo = ?
                )
            """, (uid, uid))

            # 3. Historial de facturación (depende de factura)
            cursor.execute("""
                DELETE FROM tblhistorialfacturacion
                WHERE id_factura IN (
                    SELECT f.id_factura FROM tblfactura f
                    JOIN tbltratamiento t ON f.id_tratamiento = t.id_tratamiento
                    WHERE t.id_usuario = ? OR t.id_odontologo = ?
                )
            """, (uid, uid))

            # 4. Facturas (dependen de tratamiento)
            cursor.execute("""
                DELETE FROM tblfactura
                WHERE id_tratamiento IN (
                    SELECT id_tratamiento FROM tbltratamiento
                    WHERE id_usuario = ? OR id_odontologo = ?
                )
            """, (uid, uid))

            # 5. Historial clínico (depende de tratamiento y cita)
            cursor.execute("""
                DELETE FROM tblhistorialclinico
                WHERE id_tratamiento IN (
                        SELECT id_tratamiento FROM tbltratamiento
                        WHERE id_usuario = ? OR id_odontologo = ?
                     )
                   OR id_cita IN (
                        SELECT id_cita FROM tblcita
                        WHERE id_usuario = ? OR id_odontologo = ?
                     )
            """, (uid, uid, uid, uid))

            # 6. Tratamientos (paciente u odontólogo)
            cursor.execute("""
                DELETE FROM tbltratamiento
                WHERE id_usuario = ? OR id_odontologo = ?
            """, (uid, uid))

            # 7. Historial de modificaciones (depende de cita)
            cursor.execute("""
                DELETE FROM tblhistorialmodificaciones
                WHERE id_cita IN (
                    SELECT id_cita FROM tblcita
                    WHERE id_usuario = ? OR id_odontologo = ?
                )
            """, (uid, uid))

            # 8. Agenda (depende de cita)
            cursor.execute("""
                DELETE FROM tblagenda
                WHERE id_cita IN (
                    SELECT id_cita FROM tblcita
                    WHERE id_usuario = ? OR id_odontologo = ?
                )
            """, (uid, uid))

            # 9. Citas (paciente u odontólogo)
            cursor.execute("""
                DELETE FROM tblcita
                WHERE id_usuario = ? OR id_odontologo = ?
            """, (uid, uid))

            # 10. Consultorio propio asignado (si era odontólogo)
            cursor.execute("DELETE FROM tblodontologo_sala WHERE id_odontologo = ?", (uid,))

            # 11. Asignaciones de servicio (si era odontólogo)
            cursor.execute("DELETE FROM tblodontologo_servicio WHERE id_odontologo = ?", (uid,))

            # 12. Consentimientos del usuario
            cursor.execute("DELETE FROM tblconsentimiento WHERE id_usuario = ?", (uid,))

            # 13. Roles adicionales del usuario
            cursor.execute("DELETE FROM tblusuario_rol WHERE id_usuario = ?", (uid,))

            # 14. El usuario, al final
            cursor.execute("DELETE FROM tblusuario WHERE id_usuario = ?", (uid,))

            conn.commit(); conn.close()
            self.usuario_seleccionado_id = None
            messagebox.showinfo("Eliminado", "Usuario y todos sus registros relacionados eliminados correctamente.")
            self.progreso_carga.configure(progress_color="#00ffff")
            self.animar_barra_y_cargar()

        except sqlite3.Error as e:
            messagebox.showerror("Error", f"No se pudo eliminar:\n{e}")


if __name__ == "__main__":
    app = AdminApp()
    app.mainloop()