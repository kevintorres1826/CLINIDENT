"""
CLINIDENT — Gestor de Pacientes (Borrado en Cascada)
-----------------------------------------------------
Herramienta de escritorio para listar pacientes y eliminarlos junto con
TODA su información relacionada: citas, agenda, historial clínico,
registro clínico, tratamientos, facturas, pagos, historial de
facturación, modificaciones de citas y consentimientos.

Solo afecta usuarios con id_rol = 4 (paciente). Administradores,
odontólogos y recepcionistas NO aparecen en la lista ni pueden borrarse
desde aquí, para evitar accidentes graves.
"""

import os
import sys
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog


# ──────────────────────────────────────────────────────────────────────
# UBICACIÓN DE LA BASE DE DATOS
# ──────────────────────────────────────────────────────────────────────
def ruta_base_predeterminada():
    """Misma lógica que usa el servidor Flask: junto al .exe/script."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


NOMBRE_BD = "clinident.db"
ID_ROL_PACIENTE = 4


class GestorPacientes(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CLINIDENT — Gestor de Pacientes")
        self.geometry("780x520")
        self.minsize(680, 460)
        self.configure(bg="#0f1720")

        self.ruta_bd = None
        self.conexion = None

        self._construir_estilos()
        self._construir_interfaz()
        self._intentar_autocargar_bd()

    # ──────────────────────────────────────────────────────────────
    # ESTILOS
    # ──────────────────────────────────────────────────────────────
    def _construir_estilos(self):
        estilo = ttk.Style(self)
        try:
            estilo.theme_use("clam")
        except tk.TclError:
            pass

        fondo = "#0f1720"
        panel = "#16212c"
        acento = "#2dd4bf"
        texto = "#e8eef0"

        estilo.configure("Treeview",
                          background=panel,
                          fieldbackground=panel,
                          foreground=texto,
                          rowheight=28,
                          borderwidth=0,
                          font=("Segoe UI", 10))
        estilo.configure("Treeview.Heading",
                          background="#1f2e3a",
                          foreground=texto,
                          font=("Segoe UI", 10, "bold"),
                          borderwidth=0)
        estilo.map("Treeview", background=[("selected", acento)],
                   foreground=[("selected", "#0f1720")])

        estilo.configure("TButton", font=("Segoe UI", 10), padding=8)
        estilo.configure("Accent.TButton", background=acento, foreground="#0f1720")
        estilo.map("Accent.TButton", background=[("active", "#22a89a")])

        estilo.configure("Danger.TButton", background="#ef4444", foreground="#ffffff")
        estilo.map("Danger.TButton", background=[("active", "#c93535")])

        estilo.configure("TLabel", background=fondo, foreground=texto, font=("Segoe UI", 10))
        estilo.configure("Header.TLabel", background=fondo, foreground=texto,
                          font=("Segoe UI", 15, "bold"))
        estilo.configure("Sub.TLabel", background=fondo, foreground="#8aa1ad",
                          font=("Segoe UI", 9))

    # ──────────────────────────────────────────────────────────────
    # INTERFAZ
    # ──────────────────────────────────────────────────────────────
    def _construir_interfaz(self):
        contenedor = tk.Frame(self, bg="#0f1720")
        contenedor.pack(fill="both", expand=True, padx=18, pady=16)

        # Encabezado
        encabezado = tk.Frame(contenedor, bg="#0f1720")
        encabezado.pack(fill="x", pady=(0, 10))

        ttk.Label(encabezado, text="🦷 Gestor de Pacientes", style="Header.TLabel").pack(anchor="w")
        self.lbl_ruta = ttk.Label(encabezado, text="Buscando clinident.db...", style="Sub.TLabel")
        self.lbl_ruta.pack(anchor="w", pady=(2, 0))

        # Barra de acciones superior
        barra = tk.Frame(contenedor, bg="#0f1720")
        barra.pack(fill="x", pady=(0, 10))

        ttk.Button(barra, text="📂 Elegir base de datos...", command=self.elegir_bd).pack(side="left")
        ttk.Button(barra, text="🔄 Recargar lista", command=self.cargar_pacientes).pack(side="left", padx=(8, 0))

        self.lbl_contador = ttk.Label(barra, text="", style="Sub.TLabel")
        self.lbl_contador.pack(side="right")

        # Tabla de pacientes
        tabla_frame = tk.Frame(contenedor, bg="#16212c")
        tabla_frame.pack(fill="both", expand=True)

        columnas = ("id", "nombre", "apellido", "correo", "telefono", "estado")
        self.tabla = ttk.Treeview(tabla_frame, columns=columnas, show="headings", selectmode="extended")

        encabezados = {
            "id": ("ID", 50),
            "nombre": ("Nombre", 130),
            "apellido": ("Apellido", 130),
            "correo": ("Correo", 220),
            "telefono": ("Teléfono", 110),
            "estado": ("Estado", 90),
        }
        for col, (titulo, ancho) in encabezados.items():
            self.tabla.heading(col, text=titulo)
            self.tabla.column(col, width=ancho, anchor="w")

        scroll = ttk.Scrollbar(tabla_frame, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scroll.set)
        self.tabla.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        # Pie con resumen de lo que se borrará + botón de borrado
        pie = tk.Frame(contenedor, bg="#0f1720")
        pie.pack(fill="x", pady=(12, 0))

        ttk.Label(
            pie,
            text="Al eliminar un paciente también se borran sus citas, historial clínico,\n"
                 "registros clínicos, tratamientos, facturas, pagos y consentimientos asociados.",
            style="Sub.TLabel",
            justify="left"
        ).pack(anchor="w")

        ttk.Button(
            pie, text="🗑  Eliminar paciente(s) seleccionado(s)",
            style="Danger.TButton",
            command=self.eliminar_seleccionados
        ).pack(anchor="e", pady=(10, 0))

    # ──────────────────────────────────────────────────────────────
    # CARGA / SELECCIÓN DE BASE DE DATOS
    # ──────────────────────────────────────────────────────────────
    def _intentar_autocargar_bd(self):
        candidata = os.path.join(ruta_base_predeterminada(), NOMBRE_BD)
        if os.path.exists(candidata):
            self._conectar(candidata)
        else:
            self.lbl_ruta.configure(
                text="No se encontró clinident.db junto al programa. Usa 'Elegir base de datos...'."
            )

    def elegir_bd(self):
        ruta = filedialog.askopenfilename(
            title="Selecciona clinident.db",
            filetypes=[("Base de datos SQLite", "*.db"), ("Todos los archivos", "*.*")]
        )
        if ruta:
            self._conectar(ruta)

    def _conectar(self, ruta):
        try:
            if self.conexion:
                self.conexion.close()
            conexion = sqlite3.connect(ruta)
            conexion.execute("PRAGMA foreign_keys = ON")
            conexion.row_factory = sqlite3.Row
            self.conexion = conexion
            self.ruta_bd = ruta
            self.lbl_ruta.configure(text=f"Conectado a: {ruta}")
            self.cargar_pacientes()
        except sqlite3.Error as e:
            messagebox.showerror("Error de conexión", f"No se pudo abrir la base de datos:\n{e}")

    def cargar_pacientes(self):
        if not self.conexion:
            messagebox.showwarning("Sin base de datos", "Primero selecciona el archivo clinident.db.")
            return

        for fila in self.tabla.get_children():
            self.tabla.delete(fila)

        try:
            cur = self.conexion.cursor()
            cur.execute(
                """
                SELECT id_usuario, nombre, apellido, correo, telefono, estado
                FROM tblusuario
                WHERE id_rol = ?
                ORDER BY id_usuario ASC
                """,
                [ID_ROL_PACIENTE]
            )
            filas = cur.fetchall()
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"No se pudo leer la tabla de usuarios:\n{e}")
            return

        for f in filas:
            self.tabla.insert("", "end", values=(
                f["id_usuario"], f["nombre"], f["apellido"],
                f["correo"] or "—", f["telefono"] or "—", f["estado"]
            ))

        self.lbl_contador.configure(text=f"{len(filas)} paciente(s) encontrados")

    # ──────────────────────────────────────────────────────────────
    # BORRADO EN CASCADA
    # ──────────────────────────────────────────────────────────────
    def eliminar_seleccionados(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showinfo("Nada seleccionado", "Selecciona al menos un paciente de la lista.")
            return

        pacientes = []
        for item in seleccion:
            valores = self.tabla.item(item, "values")
            pacientes.append({
                "id_usuario": int(valores[0]),
                "nombre": valores[1],
                "apellido": valores[2],
            })

        nombres = ", ".join(f"{p['nombre']} {p['apellido']} (ID {p['id_usuario']})" for p in pacientes)
        confirmar = messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Seguro que deseas eliminar definitivamente a:\n\n{nombres}\n\n"
            "Se borrarán también todas sus citas, historial clínico, tratamientos,\n"
            "facturas, pagos y consentimientos asociados. Esta acción no se puede deshacer."
        )
        if not confirmar:
            return

        errores = []
        eliminados = 0
        for p in pacientes:
            try:
                self._borrar_paciente_en_cascada(p["id_usuario"])
                eliminados += 1
            except sqlite3.Error as e:
                errores.append(f"{p['nombre']} {p['apellido']}: {e}")

        if errores:
            messagebox.showerror(
                "Algunos registros no se pudieron eliminar",
                "\n".join(errores)
            )
        else:
            messagebox.showinfo("Listo", f"{eliminados} paciente(s) eliminado(s) correctamente.")

        self.cargar_pacientes()

    def _borrar_paciente_en_cascada(self, id_usuario):
        """
        Elimina un paciente y todo lo que depende de él, respetando
        el orden correcto de claves foráneas (de lo más "hijo" a lo más "padre").
        Todo ocurre dentro de una sola transacción: si algo falla, no se
        borra nada (rollback automático).
        """
        cur = self.conexion.cursor()
        try:
            cur.execute("BEGIN")

            # IDs de citas del paciente
            cur.execute("SELECT id_cita FROM tblcita WHERE id_usuario = ?", [id_usuario])
            ids_citas = [r["id_cita"] for r in cur.fetchall()]

            # IDs de tratamientos del paciente
            cur.execute("SELECT id_tratamiento FROM tbltratamiento WHERE id_usuario = ?", [id_usuario])
            ids_tratamientos = [r["id_tratamiento"] for r in cur.fetchall()]

            # IDs de historial clínico ligado a esas citas o tratamientos
            ids_historial = []
            if ids_citas:
                cur.execute(
                    f"SELECT id_historial_clinico FROM tblhistorialclinico WHERE id_cita IN ({_marcadores(ids_citas)})",
                    ids_citas
                )
                ids_historial += [r["id_historial_clinico"] for r in cur.fetchall()]
            if ids_tratamientos:
                cur.execute(
                    f"SELECT id_historial_clinico FROM tblhistorialclinico WHERE id_tratamiento IN ({_marcadores(ids_tratamientos)})",
                    ids_tratamientos
                )
                ids_historial += [r["id_historial_clinico"] for r in cur.fetchall()]
            ids_historial = list(set(ids_historial))

            # IDs de facturas ligadas a esos tratamientos
            ids_facturas = []
            if ids_tratamientos:
                cur.execute(
                    f"SELECT id_factura FROM tblfactura WHERE id_tratamiento IN ({_marcadores(ids_tratamientos)})",
                    ids_tratamientos
                )
                ids_facturas = [r["id_factura"] for r in cur.fetchall()]

            # 1. Registro clínico (depende de historial clínico)
            if ids_historial:
                cur.execute(
                    f"DELETE FROM tblregistroclinico WHERE id_historial_clinico IN ({_marcadores(ids_historial)})",
                    ids_historial
                )

            # 2. Historial clínico (depende de cita / tratamiento)
            if ids_historial:
                cur.execute(
                    f"DELETE FROM tblhistorialclinico WHERE id_historial_clinico IN ({_marcadores(ids_historial)})",
                    ids_historial
                )

            # 3. Pagos e historial de facturación (dependen de factura)
            if ids_facturas:
                cur.execute(
                    f"DELETE FROM tblpago WHERE id_factura IN ({_marcadores(ids_facturas)})",
                    ids_facturas
                )
                cur.execute(
                    f"DELETE FROM tblhistorialfacturacion WHERE id_factura IN ({_marcadores(ids_facturas)})",
                    ids_facturas
                )

            # 4. Facturas (dependen de tratamiento)
            if ids_facturas:
                cur.execute(
                    f"DELETE FROM tblfactura WHERE id_factura IN ({_marcadores(ids_facturas)})",
                    ids_facturas
                )

            # 5. Tratamientos del paciente
            if ids_tratamientos:
                cur.execute(
                    f"DELETE FROM tbltratamiento WHERE id_tratamiento IN ({_marcadores(ids_tratamientos)})",
                    ids_tratamientos
                )

            # 6. Modificaciones de cita y agenda (dependen de cita)
            if ids_citas:
                cur.execute(
                    f"DELETE FROM tblhistorialmodificaciones WHERE id_cita IN ({_marcadores(ids_citas)})",
                    ids_citas
                )
                cur.execute(
                    f"DELETE FROM tblagenda WHERE id_cita IN ({_marcadores(ids_citas)})",
                    ids_citas
                )

            # 7. Citas del paciente
            if ids_citas:
                cur.execute(
                    f"DELETE FROM tblcita WHERE id_cita IN ({_marcadores(ids_citas)})",
                    ids_citas
                )

            # 8. Consentimientos del paciente
            cur.execute("DELETE FROM tblconsentimiento WHERE id_usuario = ?", [id_usuario])

            # 9. Relación usuario-rol (tabla puente, si existe)
            try:
                cur.execute("DELETE FROM tblusuario_rol WHERE id_usuario = ?", [id_usuario])
            except sqlite3.OperationalError:
                pass  # La tabla puede no existir en BDs más antiguas

            # 10. Finalmente, el usuario/paciente
            cur.execute("DELETE FROM tblusuario WHERE id_usuario = ?", [id_usuario])

            self.conexion.commit()
        except sqlite3.Error:
            self.conexion.rollback()
            raise

    def destroy(self):
        if self.conexion:
            self.conexion.close()
        super().destroy()


def _marcadores(lista):
    """Genera 'placeholders' tipo ?,?,?,... según la cantidad de elementos."""
    return ",".join(["?"] * len(lista))


if __name__ == "__main__":
    app = GestorPacientes()
    app.mainloop()