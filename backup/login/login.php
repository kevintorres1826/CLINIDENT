<?php
// /login/login.php
header('Content-Type: application/json');
session_start();

// Sube un nivel para encontrar el conector portátil de la raíz
require_once '../conexion.php';

$correoInput = isset($_POST['usuario']) ? trim($_POST['usuario']) : '';
$passInput   = isset($_POST['contrasena']) ? $_POST['contrasena'] : '';

// SE QUITÓ LA VALIDACIÓN DEL ROL REQUERIDO AQUÍ
if (empty($correoInput) || empty($passInput)) {
    echo json_encode(['status' => 'error', 'msg' => '⚠️ Por favor escribe tu correo y contraseña.']);
    exit;
}

try {
    // 1. Buscamos al usuario únicamente por su correo electrónico
    $sql_user = "SELECT id_usuario, id_rol, nombre, apellido, contrasena, estado 
                 FROM tblusuario 
                 WHERE correo = :correo";
                 
    $stmt = $conexion->prepare($sql_user);
    $stmt->execute([':correo' => $correoInput]);
    
    $usuario = $stmt->fetch();

    if ($usuario) {
        // 2. Validamos la contraseña en texto plano
        if ($passInput === $usuario['contrasena']) {
            
            if ($usuario['estado'] !== 'Activo') {
                echo json_encode(['status' => 'error', 'msg' => '⚠️ Tu usuario clínico se encuentra inactivo.']);
                exit;
            }

            // Guardamos las variables de sesión
            $_SESSION['id_usuario'] = $usuario['id_usuario'];
            $_SESSION['id_rol']     = $usuario['id_rol'];
            $_SESSION['nombre']     = $usuario['nombre'];
            $_SESSION['apellido']   = $usuario['apellido'];
            $_SESSION['correo']     = $correoInput;
            
            // 3. Redirección automática según el id_rol real de la base de datos (clinident.db)
            $rutas = [
                1 => '../odontologo/panel_medico.html',  // Administrador
                2 => '../odontologo/panel_medico.html',  // Odontólogo
                3 => '../odontologo/panel_medico.html',  // Recepcionista
                4 => '../agenda cliente/index.html'      // Paciente
            ];
            
            $redireccion = isset($rutas[$usuario['id_rol']]) ? $rutas[$usuario['id_rol']] : '../agenda cliente/index.html';
            
            echo json_encode([
                'status' => 'success',
                'msg' => '¡Ingreso correcto!',
                'redirect' => $redireccion
            ]);
        } else {
            echo json_encode(['status' => 'error', 'msg' => '⚠️ Correo o contraseña incorrectos.']);
        }
    } else {
        echo json_encode(['status' => 'error', 'msg' => '⚠️ Correo o contraseña incorrectos.']);
    }

} catch (PDOException $e) {
    echo json_encode(['status' => 'error', 'msg' => 'Error de lectura local: ' . $e->getMessage()]);
}
?>