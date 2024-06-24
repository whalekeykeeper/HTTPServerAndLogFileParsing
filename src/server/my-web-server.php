<?php

/**
 * A basic HTTP server in PHP using sockets.
 * Usage: php my-web-server.php [host] [port]
 * Default host: 127.0.0.1
 * Default port: 8080
 */

// Check if there are exactly 3 arguments (script name, host, port)
if ($argc !== 3) {
    echo "Usage: php " . $argv[0] . " <host> <port>\n";
    echo "Example: php " . $argv[0] . " 127.0.0.1 8080\n";
    exit(1);
}

$host = $argv[1];
$port = $argv[2];
$logDir = __DIR__ . '/../../logs/';
$logFile = $logDir . 'server.log';

$current_timezone = date_default_timezone_get();
if ($current_timezone !== 'CET') {
    date_default_timezone_set('CET');
}

if (!is_dir($logDir)) {
    mkdir($logDir, 0777, true);
}

$socket = initialize_socket($host, $port);
if (!$socket) {
    exit(1);
}

start_server($socket, $logFile);

function initialize_socket($host, $port)
{
    $socket = socket_create(AF_INET, SOCK_STREAM, SOL_TCP);
    if ($socket === false) {
        echo "Socket creation failed: " . socket_strerror(socket_last_error()) . "\n";
        return false;
    }

    if (socket_bind($socket, $host, $port) === false) {
        echo "Socket bind failed: " . socket_strerror(socket_last_error($socket)) . "\n";
        socket_close($socket);
        return false;
    }

    if (socket_listen($socket, 5) === false) {
        echo "Socket listen failed: " . socket_strerror(socket_last_error($socket)) . "\n";
        socket_close($socket);
        return false;
    }

    echo "Server listening on $host:$port...\n";
    return $socket;
}

/**
 * Main server loop to accept and handle client connections.
 */
function start_server($socket, $logFile)
{
    while (true) {
        $client = socket_accept($socket);
        if ($client === false) {
            echo "Socket accept failed: " . socket_strerror(socket_last_error($socket)) . "\n";
            continue;
        }

        handle_client_request($client, $logFile);
        socket_close($client);
    }
}

/**
 * Handle incoming client request: read, log, and respond.
 */
function handle_client_request($client, $logFile)
{
    $request = socket_read($client, 1024);
    if ($request === false) {
        echo "Socket read failed: " . socket_strerror(socket_last_error($client)) . "\n";
        return;
    }

    socket_getpeername($client, $clientIp);

    $logEntry = date('Y-m-d H:i:s') . " - IP: $clientIp - Request: " . trim($request) . "\n";
    file_put_contents($logFile, $logEntry, FILE_APPEND);

    $response = "HTTP/1.1 200 OK\r\n" .
        "Content-Type: text/plain\r\n" .
        "Content-Length: 13\r\n" .
        "\r\n" .
        "Successfully connected; " . date('Y-m-d H:i:s') . "\r\n";

    socket_write($client, $response, strlen($response));
}
?>