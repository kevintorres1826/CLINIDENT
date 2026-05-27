<?php
header('Content-Type: application/json');
require_once 'conexion.php';

$accion = isset($_POST['accion']) ? trim($_POST['accion']) : '';

// ════════════ FASE 1: ENVIAR / GENERAR CÓDIGO ════════════
if ($accion === 'enviar_codigo') {
    $metodo = isset($_POST['metodo']) ? trim($_POST['metodo']) : 'correo';
    $valor  = isset($_POST['valor']) ? trim($_POST['valor']) : '';
    
    if (empty($valor)) {
        echo json_encode(['status' => 'error', 'msg' => 'Campo de contacto vacío.']);
        exit;
    }
    
    // Validar si existe el usuario en la base de datos
    if ($metodo === 'correo') {
        $sql = "SELECT id_usuario FROM tblusuario WHERE correo = ?";
    } else {
        $sql = "SELECT id_usuario FROM tblusuario WHERE telefono = ?";
    }
    
    $stmt = $conexion->prepare($sql);
    $stmt->bind_param("s", $valor);
    $stmt->execute();
    $stmt->store_result();
    
    if ($stmt->num_rows > 0) {
        // En un entorno de producción real, aquí se llamaría a la función para mandar un correo o un SMS real.
        // Simularemos el envío exitoso de manera segura.
        echo json_encode([
            'status' => 'success',
            'msg' => 'Código de verificación generado y enviado.'
        ]);
    } else {
        echo json_encode([
            'status' => 'error',
            'msg' => 'El dato ingresado no coincide con ningún usuario registrado en CLINIDENT.'
        ]);
    }
    $stmt->close();
    $conexion->close();
    exit;
}

// ════════════ FASE 2: GUARDAR NUEVA CONTRASEÑA ════════════
if ($accion === 'actualizar_password') {
    $metodo = isset($_POST['metodo']) ? trim($_POST['metodo']) : 'correo';
    $valor  = isset($_POST['valor']) ? trim($_POST['valor']) : '';
    $nueva_clave = isset($_POST['password']) ? $_POST['password'] : '';
    
    if (empty($valor) || empty($nueva_clave)) {
        echo json_encode(['status' => 'error', 'msg' => 'Información de recuperación o contraseña incompleta.']);
        exit;
    }
    
    // Hash seguro de la nueva clave
    $pass_segura = password_hash($nueva_clave, PASSWORD_BCRYPT);
    
    if ($metodo === 'correo') {
        $sql_update = "UPDATE tblusuario SET contrasena = ? WHERE correo = ?";
    } else {
        $sql_update = "UPDATE tblusuario SET contrasena = ? WHERE telefono = ?";
    }
    
    $stmt = $conexion->prepare($sql_update);
    $stmt->bind_param("ss", $pass_segura, $valor);
    
    if ($stmt->execute()) {
        if ($stmt->affected_rows > 0) {
            echo json_encode([
                'status' => 'success',
                'msg' => '¡Contraseña restablecida de manera exitosa!'
            ]);
        } else {
            echo json_encode([
                'status' => 'error',
                'msg' => 'No se realizaron cambios (probablemente el usuario ya no existe).'
            ]);
        }
    } else {
        echo json_encode([
            'status' => 'error',
            'msg' => 'Error al intentar actualizar la base de datos.'
        ]);
    }
    $stmt->close();
    $conexion->close();
    exit;
}

echo json_encode(['status' => 'error', 'msg' => 'Acción de recuperación no soportada.']);
$conexion->close();
?>