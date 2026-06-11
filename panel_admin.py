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
        return sqlite3.connect(DB_PATH)
 
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
        def seccion(texto):
            ctk.CTkLabel(self.frame_form, text=texto, font=("Segoe UI", 12, "bold"),
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
            cb  = ctk.CTkCheckBox(self.frame_form, text=nombre_rol, variable=var,
                                  font=("Segoe UI", 13), text_color="#d0d0d5",
                                  fg_color="#00ffff", hover_color="#00b3b3",
                                  checkmark_color="#141419", width=460)
            cb.pack(anchor="w", padx=28, pady=3)
            self.check_roles[id_rol] = var
 
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
                f"¿Eliminar usuario ID {self.usuario_seleccionado_id} y todas sus citas?\n"
                "Esta acción no se puede deshacer."):
            return
        try:
            conn = self.conectar_db(); cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = ON;")
            uid = self.usuario_seleccionado_id
 
            # Borrar en cascada manual respetando foreign keys
            cursor.execute("""
                DELETE FROM tblregistroclinico
                WHERE id_historial_clinico IN (
                    SELECT hc.id_historial_clinico FROM tblhistorialclinico hc
                    JOIN tblcita c ON hc.id_cita = c.id_cita
                    WHERE c.id_usuario = ?
                )
            """, (uid,))
            cursor.execute("""
                DELETE FROM tblhistorialclinico
                WHERE id_cita IN (SELECT id_cita FROM tblcita WHERE id_usuario = ?)
            """, (uid,))
            cursor.execute("""
                DELETE FROM tblagenda
                WHERE id_cita IN (SELECT id_cita FROM tblcita WHERE id_usuario = ?)
            """, (uid,))
            cursor.execute("DELETE FROM tblcita         WHERE id_usuario = ?", (uid,))
            cursor.execute("DELETE FROM tblusuario_rol  WHERE id_usuario = ?", (uid,))
            cursor.execute("DELETE FROM tblusuario      WHERE id_usuario = ?", (uid,))
 
            conn.commit(); conn.close()
            self.usuario_seleccionado_id = None
            messagebox.showinfo("Eliminado", "Usuario y sus registros eliminados correctamente.")
            self.progreso_carga.configure(progress_color="#00ffff")
            self.animar_barra_y_cargar()
 
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"No se pudo eliminar:\n{e}")
 
 
if __name__ == "__main__":
    app = AdminApp()
    app.mainloop()
 