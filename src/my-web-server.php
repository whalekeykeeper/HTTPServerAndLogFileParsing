<?php

/**
 * A basic HTTP server in PHP using sockets.
 * Usage: php my-web-server.php [host] [port]
 * Default host: 127.0.0.1
 * Default port: 8080
 */

// Check if there are 3 or 4 arguments (script name, host, port, and optionally log_file_location)
if (isset($argv) && (count($argv) === 3 || count($argv) === 4)) {
    $host = $argv[1];
    $port = $argv[2];
    $logFile = $argv[3] ?? __DIR__ . '/../logs/server.log';
} else {
    echo "Usage: php " . ($argv[0] ?? 'my-web-server.php') . " <host> <port> [<log_file_location>]\n";
    echo "Example: php " . ($argv[0] ?? 'my-web-server.php') . " 127.0.0.1 8080 logs/server.log\n";
    exit(1);
}

$logDir = dirname($logFile);
if (!is_dir($logDir)) {
    mkdir($logDir, 0777, true);
}

$current_timezone = date_default_timezone_get();
if ($current_timezone !== 'CET') {
    date_default_timezone_set('CET');
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
 * Handle incoming client request: read, respond, and log
 */
function handle_client_request($client, $logFile)
{
    $request = '';
    while ($buffer = socket_read($client, 1024)) {
        $request .= $buffer;
        if (strpos($request, "\r\n\r\n") !== false) {
            break;
        }
    }

    socket_getpeername($client, $clientAddress);
    $clientIp = $clientAddress ?? 'UNKNOWN';

    $response = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nSuccessfully connected!";
    socket_write($client, $response);

    $httpCode = '';
    if (preg_match('/HTTP\/\d\.\d\s+(\d{3})/', $response, $matches)) {
        $httpCode = $matches[1];
    }

    $logEntry = [
        'timestamp' => date('Y-m-d H:i:s'),
        'client_ip' => $clientIp,
        'HTTP_code' => $httpCode
    ];

    $logEntryJson = json_encode($logEntry) . PHP_EOL;

    echo "Log entry: $logEntryJson\n";

    file_put_contents($logFile, $logEntryJson, FILE_APPEND);
}