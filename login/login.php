<?php
// /login/login.php
header('Content-Type: application/json');
session_start();

// Sube un nivel para encontrar el conector portátil de la raíz
require_once '../conexion.php';

$correoInput     = isset($_POST['usuario']) ? trim($_POST['usuario']) : '';
$passInput       = isset($_POST['contrasena']) ? $_POST['contrasena'] : '';
$rolSeleccionado = isset($_POST['rol']) ? trim($_POST['rol']) : '';

if (empty($correoInput) || empty($passInput) || empty($rolSeleccionado)) {
    echo json_encode(['status' => 'error', 'msg' => '⚠️ Por favor escribe tu correo, contraseña y selecciona el rol.']);
    exit;
}

// Sincronización estricta con la tabla tblrol de clinident.db
$mapeoRoles = [
    'admin'      => 1,
    'odontologo' => 2,
    'recepcion'  => 3,
    'paciente'   => 4
];

$idRolEsperado = isset($mapeoRoles[$rolSeleccionado]) ? $mapeoRoles[$rolSeleccionado] : 4;

try {
    $sql_user = "SELECT id_usuario, id_rol, nombre, apellido, contrasena, estado 
                 FROM tblusuario 
                 WHERE correo = :correo AND id_rol = :id_rol";
                 
    $stmt = $conexion->prepare($sql_user);
    $stmt->execute([
        ':correo' => $correoInput,
        ':id_rol' => $idRolEsperado
    ]);
    
    $usuario = $stmt->fetch();

    if ($usuario) {
        // Validación directa en texto plano idéntica a tus registros semilla
        if ($passInput === $usuario['contrasena']) {
            
            if ($usuario['estado'] !== 'Activo') {
                echo json_encode(['status' => 'error', 'msg' => '⚠️ Tu usuario clínico se encuentra inactivo.']);
                exit;
            }

            $_SESSION['id_usuario'] = $usuario['id_usuario'];
            $_SESSION['id_rol']     = $usuario['id_rol'];
            $_SESSION['nombre']     = $usuario['nombre'];
            $_SESSION['apellido']   = $usuario['apellido'];
            $_SESSION['correo']     = $correoInput;
            
            // Redirecciones relativas calculadas desde la perspectiva de la carpeta /login/
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
        echo json_encode(['status' => 'error', 'msg' => '⚠️ No se encontró ningún usuario con esas credenciales para el rol seleccionado.']);
    }

} catch (PDOException $e) {
    echo json_encode(['status' => 'error', 'msg' => 'Error de lectura local: ' . $e->getMessage()]);
}
?>