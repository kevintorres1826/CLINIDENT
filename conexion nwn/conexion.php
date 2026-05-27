<?php
// Configuración centralizada de la base de datos de Clinident
$servidor = "localhost";
$usuario  = "root";
$pass_db  = ""; // Cambiar si tienes contraseña en tu servidor local de base de datos
$nombre_db = "clinident"; // Nombre según el volcado SQL de phpMyAdmin

// Crear la conexión usando MySQLi de manera orientada a objetos
$conexion = new mysqli($servidor, $usuario, $pass_db, $nombre_db);

// Comprobar si hay errores en la conexión
if ($conexion->connect_error) {
    header('Content-Type: application/json');
    echo json_encode([
        'status' => 'error',
        'msg' => 'Error de conexión a la base de datos: ' . $conexion->connect_error
    ]);
    exit;
}

// Configurar el conjunto de caracteres a UTF-8 para evitar problemas de tildes o eñes
$conexion->set_charset("utf8mb4");
?>