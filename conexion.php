<?php
$host = "localhost";
$user = "root";
$password = ""; // En XAMPP por defecto va vacío en Linux, déjalo así
$database = "clinident";

// Creamos la conexión en formato MySQLi
$conexion = new mysqli($host, $user, $password, $database);

// Forzamos UTF-8 para evitar problemas con eñes o acentos
$conexion->set_charset("utf8mb4");

// Si la conexión falla, frena el código y muestra el error exacto
if ($conexion->connect_error) {
    die(json_encode([
        'status' => 'error', 
        'msg' => '⚠️ Error de conexión a la base de datos: ' . $conexion->connect_error
    ]));
}
?>