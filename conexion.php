<?php
// conexion.php

// Autodetecta la ubicación del .db al lado de este archivo (Ideal para portables)
$ruta_db = __DIR__ . '/clinident.db';

try {
    // Conexión nativa a SQLite mediante el driver PDO
    $conexion = new PDO("sqlite:" . $ruta_db);
    
    // Forzar que SQLite reporte cualquier error de sintaxis inmediatamente
    $conexion->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    
    // Retornar los datos limpios en arreglos asociativos
    $conexion->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);
    
    // Activar soporte interno de llaves foráneas para mantener la integridad de las tablas
    $conexion->exec("PRAGMA foreign_keys = ON;");

} catch (PDOException $e) {
    // Respuesta en JSON por si el front hace una petición asíncrona durante el fallo
    header('Content-Type: application/json');
    echo json_encode([
        'status' => 'error', 
        'msg' => 'Error de portabilidad: No se encontró o no se pudo abrir clinident.db. Asegúrate de que esté junto al ejecutable.'
    ]);
    exit;
}
?>