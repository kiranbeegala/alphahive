# 🚀 AlphaHive Cloud Deployment Guide (100% Free 24/7 Hosting)

This guide walks you through deploying **AlphaHive** to free cloud hosting so the autonomous trading desk and live dashboard run 24/7 without needing your laptop to stay open.

---

## 🏆 Option 1: 1-Click Deployment on Render.com (Easiest & Free)

Render provides a free Web Service container that builds and runs both the React frontend and FastAPI backend.

### Steps:
1. **Push your code to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Deploy AlphaHive multi-agent desk"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/alphahive.git
   git push -u origin main
   ```
2. **Open Render**:
   - Go to [dashboard.render.com](https://dashboard.render.com) and sign in with GitHub.
   - Click **New +** -> **Web Service**.
   - Select your `alphahive` repository.
   - Set **Runtime** to **Docker** (Render will automatically detect `Dockerfile` and `render.yaml`).
   - Select the **Free** instance type.
   - Region: Select **Singapore** (closest to India).
3. **Add Environment Variables**:
   Under **Environment Variables**, add:
   * `ANGELONE_API_KEY`: `ugPbHX57`
   * `ANGELONE_CLIENT_ID`: `B204938`
   * `ANGELONE_MPIN`: `2118`
   * `ANGELONE_TOTP_SECRET`: `AGGMQ25K6DP77SFFEBZSDYVTVM`
4. **Deploy**:
   - Click **Create Web Service**.
   - Within 2-3 minutes, your app will be live at `https://alphahive-xxxx.onrender.com`.

### ⏱️ Keep Render 100% Awake (Prevent 15-min Inactivity Sleep):
To prevent Render's free tier from sleeping outside market hours:
1. Go to [UptimeRobot.com](https://uptimerobot.com) (100% Free).
2. Click **Add New Monitor** -> Select **HTTP(s)**.
3. Name: `AlphaHive Health Check`.
4. URL: `https://your-app-name.onrender.com/api/v1/status`
5. Interval: **Every 5 minutes**.
6. Click **Create Monitor**. Your app will now stay online 24/7/365!

---

## ⚡ Option 2: Oracle Cloud Always-Free VM (Most Powerful - 24GB RAM)

Oracle Cloud gives you an **Always-Free Ubuntu Server** that never sleeps and has dedicated CPU/RAM.

### Steps:
1. Create a free account at [oracle.com/cloud/free](https://www.oracle.com/cloud/free/).
2. Create an **Ampere A1 Compute Instance** (Ubuntu 22.04 LTS, up to 4 OCPUs, 24 GB RAM - 100% free).
3. SSH into your instance:
   ```bash
   ssh -i your-key.key ubuntu@YOUR_VM_PUBLIC_IP
   ```
4. Install Docker & Git:
   ```bash
   sudo apt update && sudo apt install -y git docker.io docker-compose
   sudo usermod -aG docker $USER
   ```
5. Clone and Launch AlphaHive:
   ```bash
   git clone https://github.com/YOUR_USERNAME/alphahive.git
   cd alphahive
   docker-compose up -d --build
   ```
6. Open Port 8080 in Oracle Cloud Security Lists (Ingress Rules: Source `0.0.0.0/0`, Port `8080`).
7. Access your desk live at `http://YOUR_VM_PUBLIC_IP:8080`!

---

## 🐳 Option 3: Local 24/7 Docker Container (Home Server / Raspberry Pi)

If you have an old laptop, Mac mini, or Raspberry Pi at home:

```bash
# In the alphahive directory:
docker-compose up -d --build
```

View logs:
```bash
docker-compose logs -f
```
Stop container:
```bash
docker-compose down
```

---

## 🔒 Security Best Practices
* Never commit real trading credentials into public GitHub repositories.
* Use environment variables or GitHub Secrets when deploying.
