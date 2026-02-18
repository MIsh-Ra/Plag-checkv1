# Remote Development Guide

This guide explains how to develop Alethian on your local machine's IDE (VS Code) while the code execution and infrastructure run on a remote SSH server (e.g., AWS EC2, DigitalOcean, or a University High-Performance Cluster).

## Recommended Approach: VS Code Remote - SSH

The best way to "develop here, run there" is using the **VS Code Remote - SSH** extension. This allows you to use your local VS Code interface (themes, keybindings, extensions) while editing files and running commands directly on the remote server.

### 1. Prerequisites
- **Local Machine:** VS Code installed.
- **Remote Server:** SSH access enabled explanation (e.g., `ssh user@1.2.3.4`).
- **VS Code Extension:** Install the [Remote - SSH](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-ssh) extension.

### 2. Setup Connection
1.  Open VS Code Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`).
2.  Type **"Remote-SSH: Connect to Host..."**.
3.  Enter your SSH connection string: `23uec552@172.22.2.151`.
4.  A new VS Code window will open connected to the server.

### 2a. Configure SSH Config (Optional but Recommended)
Instead of typing the IP every time, add this to your `~/.ssh/config` file:

```ssh
Host alethian-dev
    HostName 172.22.2.151
    User 23uec552
    # IdentityFile ~/.ssh/id_rsa  <-- Uncomment if using SSH keys
```

Then you can just connect to **Host: alethian-dev**.

### 3. Workflow
1.  **Open Folder:** In the remote window, use `File > Open Folder` and navigate to `/home/your-user/Alethian`.
2.  **Terminal:** Open the integrated terminal (`Ctrl+~`). This terminal is effectively an SSH shell on the server.
3.  **Run Infrastructure:**
    ```bash
    cd infrastructure
    docker-compose up -d
    ```
4.  **Run Frontend:**
    ```bash
    cd frontend
    npm run dev
    ```

### 4. Port Forwarding (The Magic Part) ✨
VS Code automatically detects running services.
- When `npm run dev` starts on port `5173` on the **server**, VS Code forwards it to `localhost:5173` on your **local machine**.
- You can open your **local browser** (Chrome/Safari) and go to `http://localhost:5173`.
- You are strictly viewing the app running on the server, but it feels local.

---

## Alternative: Manual SSH Tunneling

If you don't use VS Code, you can forward the ports manually via your terminal.

```bash
# Forward Local 5173 -> Remote 5173 (Frontend)
# Forward Local 8000 -> Remote 8000 (Backend API)
ssh -L 5173:localhost:5173 -L 8000:localhost:8000 user@your-server-ip
```

Then open `http://localhost:5173` in your browser.

---

## Deployment vs. Development

- **Development:** Use the methods above (Vite Dev Server + Hot Reload).
- **Staging/Production:**
    - Don't use `npm run dev`.
    - Build the frontend: `npm run build`.
    - Serve with Nginx (as defined in `Directory_Structure.md`).
    - Run Backend with Gunicorn/Uvicorn workers managed by Docker.

---

## Workspace Recommendations

This project includes a `.vscode/extensions.json` file that recommends the **Remote - SSH** extension. When you open this project in VS Code, you should see a prompt to install the recommended extensions.

## Troubleshooting

### Can't Find "Remote - SSH" Extension?
If you are using **VSCodium** or **Code - OSS** (common 
default installations on Linux like Manjaro/Arch), the official Microsoft "Remote - SSH" extension will NOT appear in the marketplace because it is proprietary.

**Solution 1: Install Official VS Code**
The easiest fix is to install the official proprietary build from [code.visualstudio.com](https://code.visualstudio.com/Download) (often named `visual-studio-code-bin` in AUR).

**Solution 2: Use "Open Remote - SSH"**
If you must stick with the open-source build, search for **Open Remote - SSH** (`jeanp413.open-remote-ssh`) instead. It provides similar functionality.

### Port Forwarding Not Working?
If `http://localhost:5173` is not loading:
1.  Check the **Ports** tab in VS Code (usually next to the Terminal).
2.  Ensure port `5173` is listed and the "Forwarded Address" is `localhost:5173`.
3.  If it's missing, click "Add Port" and type `5173`.
4.  If it says "Privacy: Private", that is fine (it means only you can access it via the tunnel).
