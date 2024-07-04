<?php

use PHPUnit\Framework\TestCase;

class MyWebServerTest extends TestCase
{
    private $logFile;

    protected function setUp(): void
    {
        parent::setUp();
        $this->logFile = tempnam(sys_get_temp_dir(), 'test_server_log');
        $logContent = file_get_contents($this->logFile);
    }

    protected function tearDown(): void
    {
        parent::tearDown();
        if (file_exists($this->logFile)) {
            unlink($this->logFile);
        }
    }

    private function sendHttpRequest($request): string
    {
        $host = '127.0.0.1';
        $port = 8080;

        //TODO: handle exceptions
        $socket = socket_create(AF_INET, SOCK_STREAM, SOL_TCP);
        if ($socket === false) {
            throw new \Exception("Socket creation failed: " . socket_strerror(socket_last_error()));
        }

        if (!socket_connect($socket, $host, $port)) {
            throw new \Exception("Socket connection failed: " . socket_strerror(socket_last_error($socket)));
        }

        socket_write($socket, $request);

        $response = '';
        while ($buffer = socket_read($socket, 1024)) {
            $response .= $buffer;
        }

        socket_close($socket);

        return $response;
    }

    public function testServerLog()
    {
        $request = "GET / HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n";
        $response = $this->sendHttpRequest($request);
        $expectedResponse = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nSuccessfully connected!";
        // Assert that the response matches the expected response.
        $this->assertEquals($expectedResponse, $response, 'Server response does not match expected');

        $httpCode = '';
        if (preg_match('/HTTP\/\d\.\d\s+(\d{3})/', $response, $matches)) {
            $httpCode = $matches[1];
        }
        $logEntry = [
            'timestamp' => date('Y-m-d H:i:s'),
            'client_ip' => '127.0.0.1',
            'HTTP_code' => $httpCode
        ];
        // TODO: instead of writing to the log file, consider using a logger object
        $logEntryJson = json_encode($logEntry) . PHP_EOL;
        file_put_contents($this->logFile, $logEntryJson);

        $logContent = file_get_contents($this->logFile);
        $logEntries = explode("\n", trim($logContent));
        $this->assertNotEmpty($logEntries, 'Log file should not be empty');
        foreach ($logEntries as $entry) {
            if (empty($entry)) {
                continue;
            }
            // Assert that log entry has the expected structure.
            $decodedLogEntry = json_decode($entry, true);
            $this->assertNotNull($decodedLogEntry, 'Failed to decode JSON log entry');
            $this->assertIsArray($decodedLogEntry, 'Decoded log entry is not an array');
            $this->assertNotNull($decodedLogEntry, 'Failed to decode JSON log entry');
            $this->assertArrayHasKey('timestamp', $decodedLogEntry);
            $this->assertArrayHasKey('client_ip', $decodedLogEntry);
            $this->assertArrayHasKey('HTTP_code', $decodedLogEntry);

            $this->assertEquals($logEntry['client_ip'], $decodedLogEntry['client_ip']);
            $this->assertEquals($logEntry['HTTP_code'], $decodedLogEntry['HTTP_code']);
        }
    }
}