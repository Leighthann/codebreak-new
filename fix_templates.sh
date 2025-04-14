#!/bin/bash

echo ">>> Creating template directories"
mkdir -p ~/codebreak-new/backend/templates
mkdir -p ~/codebreak-new/backend/static

echo ">>> Creating login.html template"
cat > ~/codebreak-new/backend/templates/login.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>CodeBreak - Login</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #0a0a19;
            color: white;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .container {
            background-color: rgba(0,0,0,0.7);
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0, 195, 255, 0.5);
            width: 350px;
        }
        h1 {
            text-align: center;
            color: #00c3ff;
        }
        form {
            display: flex;
            flex-direction: column;
        }
        label {
            margin-top: 10px;
            color: #00c3ff;
        }
        input {
            padding: 10px;
            margin-top: 5px;
            background-color: #111;
            border: 1px solid #333;
            color: white;
            border-radius: 5px;
        }
        button {
            margin-top: 20px;
            padding: 10px;
            background-color: #00c3ff;
            color: black;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
        }
        button:hover {
            background-color: #00a0cc;
        }
        .message {
            margin-top: 20px;
            padding: 10px;
            border-radius: 5px;
            text-align: center;
        }
        .error {
            background-color: rgba(255, 0, 0, 0.2);
            color: #ff5555;
        }
        .tabs {
            display: flex;
            margin-bottom: 20px;
        }
        .tab {
            flex: 1;
            padding: 10px;
            text-align: center;
            cursor: pointer;
            border-bottom: 2px solid #333;
        }
        .tab.active {
            border-bottom: 2px solid #00c3ff;
            color: #00c3ff;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>CODEBREAK</h1>
        
        <div class="tabs">
            <div class="tab active" id="login-tab" onclick="showTab('login')">Login</div>
            <div class="tab" id="register-tab" onclick="showTab('register')">Register</div>
        </div>
        
        <div id="login-form">
            <form action="/web-login" method="post">
                <label for="username">Username</label>
                <input type="text" id="username" name="username" required>
                
                <label for="password">Password</label>
                <input type="password" id="password" name="password" required>
                
                <button type="submit">Login</button>
            </form>
        </div>
        
        <div id="register-form" style="display: none;">
            <form action="/web-register" method="post">
                <label for="new-username">Username</label>
                <input type="text" id="new-username" name="username" required>
                
                <label for="new-password">Password</label>
                <input type="password" id="new-password" name="password" required>
                
                <label for="confirm-password">Confirm Password</label>
                <input type="password" id="confirm-password" name="confirm_password" required>
                
                <button type="submit">Register</button>
            </form>
        </div>
        
        {% if message %}
        <div class="message {% if error %}error{% endif %}">
            {{ message }}
        </div>
        {% endif %}
    </div>

    <script>
        function showTab(tab) {
            if (tab === 'login') {
                document.getElementById('login-form').style.display = 'block';
                document.getElementById('register-form').style.display = 'none';
                document.getElementById('login-tab').classList.add('active');
                document.getElementById('register-tab').classList.remove('active');
            } else {
                document.getElementById('login-form').style.display = 'none';
                document.getElementById('register-form').style.display = 'block';
                document.getElementById('login-tab').classList.remove('active');
                document.getElementById('register-tab').classList.add('active');
            }
        }
    </script>
</body>
</html>
EOF

echo ">>> Creating register.html template"
cat > ~/codebreak-new/backend/templates/register.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>CodeBreak - Register</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #0a0a19;
            color: white;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .container {
            background-color: rgba(0,0,0,0.7);
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0, 195, 255, 0.5);
            width: 350px;
        }
        h1 {
            text-align: center;
            color: #00c3ff;
        }
        form {
            display: flex;
            flex-direction: column;
        }
        label {
            margin-top: 10px;
            color: #00c3ff;
        }
        input {
            padding: 10px;
            margin-top: 5px;
            background-color: #111;
            border: 1px solid #333;
            color: white;
            border-radius: 5px;
        }
        button {
            margin-top: 20px;
            padding: 10px;
            background-color: #00c3ff;
            color: black;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
        }
        button:hover {
            background-color: #00a0cc;
        }
        .message {
            margin-top: 20px;
            padding: 10px;
            border-radius: 5px;
            text-align: center;
        }
        .error {
            background-color: rgba(255, 0, 0, 0.2);
            color: #ff5555;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>REGISTER</h1>
        <form action="/web-register" method="post">
            <label for="username">Username</label>
            <input type="text" id="username" name="username" required>
            
            <label for="password">Password</label>
            <input type="password" id="password" name="password" required>
            
            <label for="confirm_password">Confirm Password</label>
            <input type="password" id="confirm_password" name="confirm_password" required>
            
            <button type="submit">Register</button>
        </form>
        
        {% if message %}
        <div class="message {% if error %}error{% endif %}">
            {{ message }}
        </div>
        {% endif %}
        
        <p style="text-align: center; margin-top: 20px;">
            Already have an account? <a href="/login" style="color: #00c3ff;">Login</a>
        </p>
    </div>
</body>
</html>
EOF

echo ">>> Creating launch.html template"
cat > ~/codebreak-new/backend/templates/launch.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Launch CodeBreak</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #0a0a19;
            color: white;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .container {
            background-color: rgba(0,0,0,0.7);
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0, 195, 255, 0.5);
            width: 450px;
            text-align: center;
        }
        h1 {
            color: #00c3ff;
        }
        .button {
            display: inline-block;
            padding: 15px 30px;
            margin-top: 20px;
            background-color: #00c3ff;
            color: black;
            text-decoration: none;
            border-radius: 5px;
            font-weight: bold;
        }
        .button:hover {
            background-color: #00a0cc;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>LAUNCH CODEBREAK</h1>
        <p>Welcome, <strong>{{ username }}</strong>!</p>
        <p>You have successfully logged in.</p>
        
        <a href="codebreak://{{ token }}/{{ username }}" class="button">Launch Game</a>
        
        <p style="margin-top: 40px;">
            If you don't have the game client installed, you can 
            <a href="/download-client" style="color: #00c3ff;">download it here</a>.
        </p>
    </div>
</body>
</html>
EOF

echo ">>> Updating server_postgres.py template path"
sed -i "s|templates = Jinja2Templates(directory=\"backend/templates\")|templates = Jinja2Templates(directory=\"templates\")|g" ~/codebreak-new/backend/server_postgres.py

echo ">>> Restarting server"
sudo systemctl restart codebreak

echo ">>> Template setup complete!"