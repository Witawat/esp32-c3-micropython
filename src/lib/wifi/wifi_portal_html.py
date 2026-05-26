"""
WiFi Portal HTML Template
แม่แบบ HTML สำหรับ WiFi Configuration Portal
"""

PORTAL_HTML = """<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ESP32-C3 WiFi Setup</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%%, #764ba2 100%%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }

        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            max-width: 500px;
            width: 100%%;
            padding: 40px;
        }

        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 10px;
            font-size: 2em;
        }

        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 30px;
            font-size: 0.9em;
        }

        .status-bar {
            background: #f0f0f0;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .status-bar.connected {
            background: #d4edda;
        }

        .status-bar.disconnected {
            background: #fff3cd;
        }

        .status-icon {
            font-size: 1.5em;
        }

        .status-text {
            flex: 1;
        }

        .status-text strong {
            display: block;
            color: #333;
        }

        .status-text small {
            color: #666;
            font-size: 0.8em;
        }

        .form-group {
            margin-bottom: 20px;
        }

        label {
            display: block;
            margin-bottom: 8px;
            color: #555;
            font-weight: 500;
        }

        input[type="text"],
        input[type="password"],
        select {
            width: 100%%;
            padding: 12px 15px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 1em;
            transition: all 0.3s;
        }

        input[type="text"]:focus,
        input[type="password"]:focus,
        select:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        .wifi-list {
            max-height: 200px;
            overflow-y: auto;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            margin-top: 10px;
        }

        .wifi-item {
            padding: 12px 15px;
            border-bottom: 1px solid #f0f0f0;
            cursor: pointer;
            transition: background 0.2s;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .wifi-item:last-child {
            border-bottom: none;
        }

        .wifi-item:hover {
            background: #f5f5f5;
        }

        .wifi-info {
            flex: 1;
        }

        .wifi-name {
            font-weight: 500;
            color: #333;
        }

        .wifi-signal {
            font-size: 0.8em;
            color: #666;
        }

        .wifi-secure {
            font-size: 1.2em;
        }

        .btn {
            width: 100%%;
            padding: 14px;
            border: none;
            border-radius: 10px;
            font-size: 1em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            margin-top: 10px;
        }

        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%%, #764ba2 100%%);
            color: white;
        }

        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }

        .btn-secondary {
            background: #6c757d;
            color: white;
        }

        .btn-secondary:hover {
            background: #5a6268;
        }

        .btn-scan {
            background: #28a745;
            color: white;
        }

        .btn-scan:hover {
            background: #218838;
        }

        .message {
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
            font-weight: 500;
        }

        .message.success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }

        .message.error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }

        .message.info {
            background: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }

        .loading {
            display: none;
            text-align: center;
            padding: 20px;
        }

        .loading.show {
            display: block;
        }

        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 10px;
        }

        @keyframes spin {
            0%% { transform: rotate(0deg); }
            100%% { transform: rotate(360deg); }
        }

        .footer {
            text-align: center;
            margin-top: 20px;
            color: #999;
            font-size: 0.8em;
        }

        .advanced-toggle {
            text-align: center;
            margin-top: 15px;
        }

        .advanced-toggle a {
            color: #667eea;
            text-decoration: none;
            font-size: 0.9em;
        }

        .advanced-options {
            display: none;
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
        }

        .advanced-options.show {
            display: block;
        }

        .checkbox-group {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 10px;
        }

        .checkbox-group input[type="checkbox"] {
            width: 18px;
            height: 18px;
        }

        .checkbox-group label {
            margin-bottom: 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔧 WiFi Setup</h1>
        <p class="subtitle">ESP32-C3 WiFi Configuration Portal</p>

        <div id="status" class="status-bar disconnected">
            <span class="status-icon">⚠️</span>
            <div class="status-text">
                <strong id="status-title">ไม่ได้เชื่อมต่อ WiFi</strong>
                <small id="status-desc">กรุณาเลือกเครือข่าย WiFi</small>
            </div>
        </div>

        <div id="message"></div>

        <form id="wifiForm">
            <div class="form-group">
                <label for="ssid">📶 WiFi Network</label>
                <input type="text" id="ssid" name="ssid" placeholder="ชื่อ WiFi" required>
                
                <button type="button" class="btn btn-scan" onclick="scanNetworks()">
                    🔍 สแกน WiFi
                </button>
                
                <div id="wifiList" class="wifi-list" style="display: none;"></div>
            </div>

            <div class="form-group">
                <label for="password">🔒 Password</label>
                <input type="password" id="password" name="password" placeholder="รหัสผ่าน WiFi">
            </div>

            <div class="advanced-toggle">
                <a href="#" onclick="toggleAdvanced(); return false;">
                    ⚙️ ตัวเลือกขั้นสูง
                </a>
            </div>

            <div id="advancedOptions" class="advanced-options">
                <div class="checkbox-group">
                    <input type="checkbox" id="autoConnect" checked>
                    <label for="autoConnect">เชื่อมต่ออัตโนมัติเมื่อเปิดเครื่อง</label>
                </div>

                <div class="checkbox-group">
                    <input type="checkbox" id="reconnect" checked>
                    <label for="reconnect">เชื่อมต่อใหม่เมื่อหลุด</label>
                </div>

                <div class="form-group">
                    <label for="timeout">⏱️ Timeout (วินาที)</label>
                    <input type="number" id="timeout" name="timeout" value="15" min="5" max="60">
                </div>

                <div class="form-group">
                    <label for="reconnectInterval">🔄 ตรวจสอบทุก (วินาที)</label>
                    <input type="number" id="reconnectInterval" name="reconnectInterval" value="30" min="10" max="300">
                </div>
            </div>

            <button type="submit" class="btn btn-primary">
                💾 บันทึกและเชื่อมต่อ
            </button>
        </form>

        <button class="btn btn-secondary" onclick="testConnection()">
            🧪 ทดสอบการเชื่อมต่อ
        </button>

        <div id="loading" class="loading">
            <div class="spinner"></div>
            <p>กำลังดำเนินการ...</p>
        </div>

        <div class="footer">
            <p>ESP32-C3 WiFi Manager v1.0</p>
        </div>
    </div>

    <script>
        // โหลดสถานะเมื่อเปิดหน้า
        window.onload = function() {
            loadStatus();
        };

        async function loadStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                
                const statusDiv = document.getElementById('status');
                const statusTitle = document.getElementById('status-title');
                const statusDesc = document.getElementById('status-desc');
                
                if (data.connected) {
                    statusDiv.className = 'status-bar connected';
                    statusTitle.textContent = '✅ เชื่อมต่อ WiFi แล้ว';
                    statusDesc.textContent = `IP: ${data.ip || 'N/A'}`;
                } else {
                    statusDiv.className = 'status-bar disconnected';
                    statusTitle.textContent = '⚠️ ไม่ได้เชื่อมต่อ WiFi';
                    statusDesc.textContent = 'กรุณาเลือกเครือข่าย WiFi';
                }
            } catch (error) {
                console.error('Failed to load status:', error);
            }
        }

        async function scanNetworks() {
            const loading = document.getElementById('loading');
            const wifiList = document.getElementById('wifiList');
            
            loading.classList.add('show');
            wifiList.style.display = 'none';
            
            try {
                const response = await fetch('/api/scan');
                const networks = await response.json();
                
                if (networks.length === 0) {
                    showMessage('ไม่พบ WiFi networks', 'info');
                    return;
                }
                
                wifiList.innerHTML = '';
                networks.forEach(net => {
                    const item = document.createElement('div');
                    item.className = 'wifi-item';
                    item.onclick = () => selectNetwork(net.ssid);
                    
                    const signal = net.signal > -50 ? '📶📶📶' : 
                                  net.signal > -70 ? '📶📶' : '📶';
                    const secure = net.secure ? '🔒' : '🔓';
                    
                    item.innerHTML = `
                        <div class="wifi-info">
                            <div class="wifi-name">${net.ssid}</div>
                            <div class="wifi-signal">${signal} ${net.signal} dBm</div>
                        </div>
                        <div class="wifi-secure">${secure}</div>
                    `;
                    
                    wifiList.appendChild(item);
                });
                
                wifiList.style.display = 'block';
            } catch (error) {
                showMessage('ไม่สามารถสแกนเครือข่ายได้: ' + error.message, 'error');
            } finally {
                loading.classList.remove('show');
            }
        }

        function selectNetwork(ssid) {
            document.getElementById('ssid').value = ssid;
            document.getElementById('wifiList').style.display = 'none';
            document.getElementById('password').focus();
        }

        document.getElementById('wifiForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const loading = document.getElementById('loading');
            loading.classList.add('show');
            
            const formData = {
                ssid: document.getElementById('ssid').value,
                password: document.getElementById('password').value,
                auto_connect: document.getElementById('autoConnect').checked,
                reconnect: document.getElementById('reconnect').checked,
                timeout: parseInt(document.getElementById('timeout').value),
                reconnect_interval: parseInt(document.getElementById('reconnectInterval').value)
            };
            
            try {
                const response = await fetch('/api/save', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(formData)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showMessage('✅ บันทึกการตั้งค่าสำเร็จ กำลังเชื่อมต่อ...', 'success');
                    loadStatus();
                } else {
                    showMessage('❌ ไม่สามารถบันทึกการตั้งค่าได้', 'error');
                }
            } catch (error) {
                showMessage('❌ เกิดข้อผิดพลาด: ' + error.message, 'error');
            } finally {
                loading.classList.remove('show');
            }
        });

        async function testConnection() {
            const loading = document.getElementById('loading');
            loading.classList.add('show');
            
            try {
                const response = await fetch('/api/test');
                const result = await response.json();
                
                if (result.connected) {
                    showMessage(`✅ การเชื่อมต่อสำเร็จ! IP: ${result.ip}`, 'success');
                    loadStatus();
                } else {
                    showMessage('❌ การเชื่อมต่อไม่สำเร็จ', 'error');
                }
            } catch (error) {
                showMessage('❌ ไม่สามารถทดสอบการเชื่อมต่อได้', 'error');
            } finally {
                loading.classList.remove('show');
            }
        }

        function toggleAdvanced() {
            const options = document.getElementById('advancedOptions');
            options.classList.toggle('show');
        }

        function showMessage(text, type) {
            const messageDiv = document.getElementById('message');
            messageDiv.className = `message ${type}`;
            messageDiv.textContent = text;
            
            setTimeout(() => {
                messageDiv.textContent = '';
                messageDiv.className = '';
            }, 5000);
        }
    </script>
</body>
</html>
"""


# 404 Page HTML
ERROR_404_HTML = """<!DOCTYPE html>
<html>
<head><title>404</title></head>
<body>
<h1>404 - Page Not Found</h1>
<p>หน้าที่คุณต้องการไม่พบ</p>
<a href="/">กลับหน้าหลัก</a>
</body>
</html>
"""
