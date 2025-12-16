module.exports = {
  apps: [
    {
      name: "temu-api",
      script: ".venv/bin/uvicorn",
      args: "api.server:app --host 0.0.0.0 --port 8000",
      interpreter: "/home/chx/temu/.venv/bin/python3",
      env: {
        NODE_ENV: "production"
      },
      autorestart: true,
      watch: false,
      max_memory_restart: "500M",
      error_file: "logs/pm2-error.log",
      out_file: "logs/pm2-out.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss Z"
    }
  ]
};