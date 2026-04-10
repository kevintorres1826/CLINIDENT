<?php
header('Content-Type: application/json');

// Configuración de conexión
$servidor = "localhost";
$usuario  = "root";
$pass_db  = ""; // En XAMPP por defecto es vacío
$nombre_db = "clinident_db";

// Crear conexión
$conexion = mysqli_connect($servidor, $usuario, $pass_db, $nombre_db);

if (!$conexion) {
    echo json_encode(['status' => 'error', 'msg' => 'Error de conexión a la base de datos']);
    exit;
}

// Recibir datos del JS
$nombre   = $_POST['nombre'] ?? '';
$apellido = $_POST['apellido'] ?? '';
$email    = $_POST['email'] ?? '';
$telefono = $_POST['telefono'] ?? '';
$password = $_POST['password'] ?? '';

// Validar que no estén vacíos
if (empty($nombre) || empty($email) || empty($password)) {
    echo json_encode(['status' => 'error', 'msg' => 'Campos incompletos']);
    exit;
}

// Encriptar contraseña para que sea seguro
$pass_segura = password_hash($password, PASSWORD_BCRYPT);

// Insertar en la tabla
$sql = "INSERT INTO usuarios (nombre, apellido, email, telefono, password) 
        VALUES ('$nombre', '$apellido', '$email', '$telefono', '$pass_segura')";

if (mysqli_query($conexion, $sql)) {
    echo json_encode(['status' => 'success', 'msg' => 'Usuario guardado en la base de datos']);
} else {
    // Si el correo ya existe, dará error por el campo UNIQUE
    echo json_encode(['status' => 'error', 'msg' => 'El correo ya está registrado o hubo un error.']);
}

mysqli_close($conexion);
?>