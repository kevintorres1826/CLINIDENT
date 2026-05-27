<?php
header('Content-Type: application/json');
session_start();

// 1. Ruta corregida para salir de la carpeta 'login/' y buscar en la raíz
require_once '../conexion.php';

// Obtener datos del cuerpo de la petición (JSON o POST tradicional)
$correoInput = isset($_POST['usuario']) ? trim($_POST['usuario']) : '';
$passInput   = isset($_POST['contrasena']) ? $_POST['contrasena'] : '';
$rolSeleccionado = isset($_POST['rol']) ? trim($_POST['rol']) : '';

if (empty($correoInput) || empty($passInput) || empty($rolSeleccionado)) {
    echo json_encode(['status' => 'error', 'msg' => '⚠️ Por favor escribe tu correo, contraseña y selecciona el rol.']);
    exit;
}

// Mapeo de roles de la UI al ID de la Base de Datos (tblrol)
// 1 = administrador, 2 = odontologo, 3 = recepcionista, 4 = paciente
$mapeoRoles = [
    'paciente'  => 4,
    'odontologo' => 2,
    'recepcion' => 3,
    'admin'     => 1
];

$idRolEsperado = isset($mapeoRoles[$rolSeleccionado]) ? $mapeoRoles[$rolSeleccionado] : 4;

// Buscar usuario en tblusuario con su respectivo rol
$sql_user = "SELECT id_usuario, id_rol, nombre, apellido, contrasena, estado FROM tblusuario WHERE correo = ? AND id_rol = ?";
$stmt = $conexion->prepare($sql_user);

if ($stmt) {
    $stmt->bind_param("si", $correoInput, $idRolEsperado);
    $stmt->execute();
    $result = $stmt->get_result();
    
    if ($result->num_rows === 1) {
        $usuario = $result->fetch_assoc();
        
        // Verificar si la cuenta está Activa
        if ($usuario['estado'] !== 'Activo') {
            echo json_encode(['status' => 'error', 'msg' => '⚠️ Tu cuenta está inactiva. Comunícate con soporte.']);
            $stmt->close();
            $conexion->close();
            exit;
        }
        
        // CORRECCIÓN AQUÍ: Cambiado password_verify por === porque tus datos están en texto plano en la BD
        if ($passInput === $usuario['contrasena']) {
            // Guardar variables de sesión para protección de páginas internas
            $_SESSION['id_usuario'] = $usuario['id_usuario'];
            $_SESSION['id_rol']     = $usuario['id_rol'];
            $_SESSION['nombre']     = $usuario['nombre'];
            $_SESSION['apellido']   = $usuario['apellido'];
            $_SESSION['correo']     = $correoInput;
            
            // Definición de las rutas del software basadas en el rol
            $rutas = [
                4 => '../agenda cliente/index.html',     // Paciente
                2 => '../odontologo/panel_medico.html',  // Odontólogo
                3 => '../odontologo/panel_medico.html',  // Recepcionista
                1 => '../odontologo/panel_medico.html'   // Administrador
            ];
            
            $redireccion = isset($rutas[$usuario['id_rol']]) ? $rutas[$usuario['id_rol']] : '../agenda cliente/index.html';
            
            echo json_encode([
                'status' => 'success',
                'msg' => '¡Ingreso correcto!',
                'redirect' => $redireccion
            ]);
        } else {
            // Error genérico para no dar pistas en caso de ciberataques
            echo json_encode(['status' => 'error', 'msg' => '⚠️ Correo o contraseña incorrectos.']);
        }
    } else {
        echo json_encode(['status' => 'error', 'msg' => '⚠️ No se encontró ningún usuario con esas credenciales para el rol seleccionado.']);
    }
    $stmt->close();
} else {
    echo json_encode(['status' => 'error', 'msg' => 'Error de consulta en el servidor.']);
}

$conexion->close();
?>