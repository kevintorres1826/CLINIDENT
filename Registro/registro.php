<?php
header('Content-Type: application/json');

// MODIFICACIÓN 1: Cambiado a '../conexion.php' para salir de la carpeta Registro/
require_once '../conexion.php';

// Recibir y limpiar los datos enviados por POST
$nombre   = isset($_POST['nombre']) ? trim($_POST['nombre']) : '';
$apellido = isset($_POST['apellido']) ? trim($_POST['apellido']) : '';
$email    = isset($_POST['email']) ? trim($_POST['email']) : '';
$telefono = isset($_POST['telefono']) ? trim($_POST['telefono']) : '';
$password = isset($_POST['password']) ? $_POST['password'] : '';

// Validar campos obligatorios básicos
if (empty($nombre) || empty($apellido) || empty($email) || empty($password)) {
    echo json_encode(['status' => 'error', 'msg' => 'Por favor completa todos los campos obligatorios.']);
    exit;
}

// 1. Validar que el correo no esté registrado previamente
$sql_check = "SELECT id_usuario FROM tblusuario WHERE correo = ?";
$stmt_check = $conexion->prepare($sql_check);
$stmt_check->bind_param("s", $email);
$stmt_check->execute();
$stmt_check->store_result();

if ($stmt_check->num_rows > 0) {
    echo json_encode(['status' => 'error', 'msg' => 'El correo electrónico ya se encuentra registrado.']);
    $stmt_check->close();
    $conexion->close();
    exit;
}
$stmt_check->close();

// MODIFICACIÓN 2: Guardamos en texto plano temporalmente para que coincida con tus datos viejos de SQL
// (Y para que el login.php que acabamos de arreglar los deje entrar sin problemas)
$pass_guardar = $password; 

// 3. Asignar por defecto el rol de Paciente (id_rol = 4 según tblrol)
$id_rol_paciente = 4;
$estado_activo = 'Activo';

// 4. Preparar la inserción en la tabla correcta de tu base de datos: tblusuario
$sql_insert = "INSERT INTO tblusuario (id_rol, nombre, apellido, correo, telefono, contrasena, estado) VALUES (?, ?, ?, ?, ?, ?, ?)";
$stmt_insert = $conexion->prepare($sql_insert);

if ($stmt_insert) {
    // Enviamos $pass_guardar en lugar de la versión encriptada anterior
    $stmt_insert->bind_param("issssss", $id_rol_paciente, $nombre, $apellido, $email, $telefono, $pass_guardar, $estado_activo);
    
    if ($stmt_insert->execute()) {
        echo json_encode([
            'status' => 'success', 
            'msg' => 'Cuenta creada exitosamente en la base de datos de CLINIDENT.'
        ]);
    } else {
        echo json_encode([
            'status' => 'error', 
            'msg' => 'Error al guardar los datos del registro en la base de datos.'
        ]);
    }
    $stmt_insert->close();
} else {
    echo json_encode([
        'status' => 'error', 
        'msg' => 'Error de preparación de consulta SQL para registro.'
    ]);
}

$conexion->close();
?>