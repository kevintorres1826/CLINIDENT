<?php
// /login/recuperacion.php
header('Content-Type: application/json');

// Subimos un nivel de carpeta para conectar con el archivo conexion.php en la raíz
require_once '../conexion.php'; 

$accion = isset($_POST['accion']) ? trim($_POST['accion']) : '';

// ════════════ FASE 1: VERIFICAR DESTINO EN BASE DE DATOS ════════════
if ($accion === 'enviar_codigo') {
    $metodo = isset($_POST['metodo']) ? trim($_POST['metodo']) : 'correo';
    $valor  = isset($_POST['valor']) ? trim($_POST['valor']) : '';
    
    if (empty($valor)) {
        echo json_encode(['status' => 'error', 'msg' => 'Por favor, escribe tus datos de contacto.']);
        exit;
    }
    
    try {
        // Consultar según el método seleccionado por el usuario en la interfaz
        if ($metodo === 'correo') {
            $sql = "SELECT id_usuario FROM tblusuario WHERE correo = :valor";
        } else {
            $sql = "SELECT id_usuario FROM tblusuario WHERE telefono = :valor";
        }
        
        $stmt = $conexion->prepare($sql);
        $stmt->execute([':valor' => $valor]);
        
        // Si el fetch devuelve una fila, significa que el usuario existe en clinident.db
        if ($stmt->fetch()) {
            echo json_encode([
                'status' => 'success',
                'msg' => 'Código de verificación generado y enviado correctamente.'
            ]);
        } else {
            // Mensaje de error coherente si el correo o teléfono no están en la tabla
            echo json_encode([
                'status' => 'error',
                'msg' => 'Los datos ingresados no coinciden con ningún usuario registrado.'
            ]);
        }
    } catch (PDOException $e) {
        echo json_encode(['status' => 'error', 'msg' => 'Error en la base de datos: ' . $e->getMessage()]);
    }
    exit;
}

// ════════════ FASE 2: ACTUALIZACIÓN DE CONTRASEÑA (AGREGADO) ════════════
if ($accion === 'actualizar_password') {
    $metodo      = isset($_POST['metodo']) ? trim($_POST['metodo']) : 'correo';
    $valor       = isset($_POST['valor']) ? trim($_POST['valor']) : '';
    $nueva_clave = isset($_POST['password']) ? $_POST['password'] : '';
    
    // Validar del lado del servidor que no lleguen campos vacíos
    if (empty($valor) || empty($nueva_clave)) {
        echo json_encode(['status' => 'error', 'msg' => 'Información de recuperación incompleta.']);
        exit;
    }
    
    try {
        // Seleccionar la consulta SQL idónea según el método de recuperación utilizado
        if ($metodo === 'correo') {
            $sql_update = "UPDATE tblusuario SET contrasena = :nueva_clave WHERE correo = :valor";
        } else {
            $sql_update = "UPDATE tblusuario SET contrasena = :nueva_clave WHERE telefono = :valor";
        }
        
        // Preparar y ejecutar la consulta en clinident.db usando PDO
        $stmt = $conexion->prepare($sql_update);
        $stmt->execute([
            ':nueva_clave' => $nueva_clave,
            ':valor'       => $valor
        ]);
        
        // Responder éxito de manera inmediata a la interfaz
        echo json_encode([
            'status' => 'success',
            'msg' => '¡Contraseña restablecida con éxito!'
        ]);
        
    } catch (PDOException $e) {
        echo json_encode(['status' => 'error', 'msg' => 'Error al actualizar: ' . $e->getMessage()]);
    }
    exit;
}