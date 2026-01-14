# Pi in the sky

This project aims to use on-device models to detect the presence of birds in images taken from a USB webcam attached to a Raspberry Pi v4.

## Setup

Install the package:

```bash
uv pip install -e .
```

Or install globally:

```bash
uv tool install -e .
```

The TFLite model (SSD MobileNet V1, ~4MB) is automatically downloaded on first run from Google's official storage.

## Usage

List available cameras:

```bash
pisky list
```

Capture and detect birds:

```bash
pisky shoot                     # Use default camera (index 0)
pisky shoot --camera 1          # Use specific camera
pisky shoot --keep-all          # Keep images even if no birds detected
```

Show configuration and model source:

```bash
pisky info
```

## Configuration

By default, `pisky` stores data in `~/.pisky/` (models, images, and database). To use a different location, set the `PISKY_DATA_DIR` environment variable:

```bash
export PISKY_DATA_DIR=/path/to/data
pisky shoot
```

## Web Dashboard

Start the API server:

```bash
pisky serve
```

For development, run the SvelteKit dev server:

```bash
cd client && npm run dev
```

## Production Deployment (Raspberry Pi)

### Build the frontend

```bash
cd client
npm install
npm run build
```

### systemd services

Create two service files:

**/etc/systemd/system/pisky-api.service**

```ini
[Unit]
Description=Pi in the Sky API
After=network.target

[Service]
Type=simple
User=john
ExecStart=/home/john/.local/bin/pisky serve --host 127.0.0.1 --port 8000
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

**/etc/systemd/system/pisky-web.service**

```ini
[Unit]
Description=Pi in the Sky Web Dashboard
After=network.target pisky-api.service

[Service]
Type=simple
User=john
WorkingDirectory=/home/john/pi-in-the-sky/client
Environment=PORT=3000
Environment=ORIGIN=http://pisky.local:3000
ExecStart=/usr/bin/node build
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start the services:

```bash
sudo systemctl daemon-reload
sudo systemctl enable pisky-api pisky-web
sudo systemctl start pisky-api pisky-web
```

Check status:

```bash
sudo systemctl status pisky-api pisky-web
```

View logs:

```bash
journalctl -u pisky-api -f
journalctl -u pisky-web -f
```

### nginx reverse proxy

The Vite proxy only works in dev mode. For production, use nginx to route requests:

```bash
sudo apt install nginx
```

**/etc/nginx/sites-available/pisky**

```nginx
server {
    listen 80;
    server_name pisky.local;

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
    }

    location /images/ {
        proxy_pass http://127.0.0.1:8000;
    }

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/pisky /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo systemctl restart nginx
```

Access the dashboard at http://pisky.local (or your Pi's IP address).
