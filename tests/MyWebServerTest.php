<?php

use PHPUnit\Framework\TestCase;

class MyWebServerTest extends TestCase
{
    private $host = '127.0.0.1';
    private $port = 8080;
    private $logFile;

    protected function setUp(): void
    {
        parent::setUp();
        $this->logFile = tempnam(sys_get_temp_dir(), 'test_server_log');
    }

    protected function tearDown(): void
    {
        parent::tearDown();
        if (file_exists($this->logFile)) {
            unlink($this->logFile);
        }
    }

    private function sendHttpRequest($request)
    {
        $socket = socket_create(AF_INET, SOCK_STREAM, SOL_TCP);
        if ($socket === false) {
            $this->fail("Socket creation failed: " . socket_strerror(socket_last_error()));
        }

        if (!socket_connect($socket, $this->host, $this->port)) {
            $this->fail("Socket connect failed: " . socket_strerror(socket_last_error($socket)));
        }

        socket_write($socket, $request, strlen($request));
        $response = socket_read($socket, 1024);
        socket_close($socket);

        return $response;
    }

    public function testServerLog()
    {
        file_put_contents($this->logFile, '');

        $request = "GET / HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n";
        $this->sendHttpRequest($request);

        usleep(100000);

        $logContent = file_get_contents($this->logFile);
        $logEntries = explode("\n", trim($logContent));

        $this->assertNotEmpty($logEntries, 'Log file should not be empty');

        foreach ($logEntries as $logEntry) {
            if (empty($logEntry)) {
                continue;
            }

            $decodedLogEntry = json_decode($logEntry, true);

            $this->assertNotNull($decodedLogEntry, 'Failed to decode JSON log entry');

            $this->assertArrayHasKey('timestamp', $decodedLogEntry);
            $this->assertArrayHasKey('client_ip', $decodedLogEntry);
            $this->assertArrayHasKey('request', $decodedLogEntry);
            $this->assertArrayHasKey('response', $decodedLogEntry);
        }
    }
}
