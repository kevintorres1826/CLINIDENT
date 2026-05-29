<?php
// /Registro/registro.php
header('Content-Type: application/json');

// Buscamos la conexión subiendo un nivel hacia la raíz
require_once '../conexion.php'; 

$nombre   = isset($_POST['nombre']) ? trim($_POST['nombre']) : '';
$apellido = isset($_POST['apellido']) ? trim($_POST['apellido']) : '';
$email    = isset($_POST['email']) ? trim($_POST['email']) : '';
$telefono = isset($_POST['telefono']) ? trim($_POST['telefono']) : '';
$password = isset($_POST['password']) ? $_POST['password'] : '';

if (empty($nombre) || empty($apellido) || empty($email) || empty($password)) {
    echo json_encode(['status' => 'error', 'msg' => 'Por favor completa todos los campos obligatorios.']);
    exit;
}

try {
    // 1. Validar duplicados localmente
    $sql_check = "SELECT id_usuario FROM tblusuario WHERE correo = :email";
    $stmt_check = $conexion->prepare($sql_check);
    $stmt_check->execute([':email' => $email]);
    
    if ($stmt_check->fetch()) {
        echo json_encode(['status' => 'error', 'msg' => 'El correo electrónico ya se encuentra registrado.']);
        exit;
    }

    $id_rol_paciente = 4; // Paciente predeterminado
    $estado_activo = 'Activo';

    // 2. Inserción compatible con SQLite
    $sql_insert = "INSERT INTO tblusuario (id_rol, nombre, apellido, correo, telefono, contrasena, estado) 
                   VALUES (:id_rol, :nombre, :apellido, :correo, :telefono, :contrasena, :estado)";
    
    $stmt_insert = $conexion->prepare($sql_insert);
    $resultado = $stmt_insert->execute([
        ':id_rol'     => $id_rol_paciente,
        ':nombre'     => $nombre,
        ':apellido'   => $apellido,
        ':correo'     => $email,
        ':telefono'   => !empty($telefono) ? $telefono : null,
        ':contrasena' => $password, // Almacenamiento en texto plano coherente con el login local
        ':estado'     => $estado_activo
    ]);

    if ($resultado) {
        echo json_encode([
            'status' => 'success', 
            'msg' => 'Cuenta creada con éxito en el sistema local.'
        ]);
    } else {
        echo json_encode(['status' => 'error', 'msg' => 'No se pudieron escribir los datos físicos en clinident.db.']);
    }

} catch (PDOException $e) {
    echo json_encode(['status' => 'error', 'msg' => 'Fallo interno de la base de datos portable: ' . $e->getMessage()]);
}
?>