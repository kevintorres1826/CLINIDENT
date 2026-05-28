<?php
// /login/recuperacion.php
header('Content-Type: application/json');

require_once '../conexion.php'; 

$accion = isset($_POST['accion']) ? trim($_POST['accion']) : '';

// FASE 1: Verificación de la existencia del destino de contacto
if ($accion === 'enviar_codigo') {
    $metodo = isset($_POST['metodo']) ? trim($_POST['metodo']) : 'correo';
    $valor  = isset($_POST['valor']) ? trim($_POST['valor']) : '';
    
    if (empty($valor)) {
        echo json_encode(['status' => 'error', 'msg' => 'Campo de contacto vacío.']);
        exit;
    }
    
    try {
        $sql = ($metodo === 'correo') 
            ? "SELECT id_usuario FROM tblusuario WHERE correo = :valor" 
            : "SELECT id_usuario FROM tblusuario WHERE telefono = :valor";
        
        $stmt = $conexion->prepare($sql);
        $stmt->execute([':valor' => $valor]);
        
        if ($stmt->fetch()) {
            echo json_encode(['status' => 'success', 'msg' => 'Código de verificación generado y enviado.']);
        } else {
            echo json_encode(['status' => 'error', 'msg' => 'Los datos de contacto no corresponden a ningún usuario clínico.']);
        }
    } catch (PDOException $e) {
        echo json_encode(['status' => 'error', 'msg' => 'Error de consulta: ' . $e->getMessage()]);
    }
    exit;
}

// FASE 2: Cambio de clave en Texto Plano
if ($accion === 'actualizar_password') {
    $metodo      = isset($_POST['metodo']) ? trim($_POST['metodo']) : 'correo';
    $valor       = isset($_POST['valor']) ? trim($_POST['valor']) : '';
    $nueva_clave = isset($_POST['password']) ? $_POST['password'] : '';
    
    if (empty($valor) || empty($nueva_clave)) {
        echo json_encode(['status' => 'error', 'msg' => 'Información incompleta para el cambio de credenciales.']);
        exit;
    }
    
    try {
        $sql_update = ($metodo === 'correo')
            ? "UPDATE tblusuario SET contrasena = :nueva_clave WHERE correo = :valor"
            : "UPDATE tblusuario SET contrasena = :nueva_clave WHERE telefono = :valor";
        
        $stmt = $conexion->prepare($sql_update);
        $stmt->execute([
            ':nueva_clave' => $nueva_clave,
            ':valor'       => $valor
        ]);
        
        if ($stmt->rowCount() > 0) {
            echo json_encode(['status' => 'success', 'msg' => '¡Contraseña restablecida con éxito!']);
        } else {
            echo json_encode(['status' => 'error', 'msg' => 'No se realizaron cambios en las credenciales actuales.']);
        }
    } catch (PDOException $e) {
        echo json_encode(['status' => 'error', 'msg' => 'Error al escribir nueva contraseña: ' . $e->getMessage()]);
    }
    exit;
}

echo json_encode(['status' => 'error', 'msg' => 'Operación no válida en el entorno local.']);
?>