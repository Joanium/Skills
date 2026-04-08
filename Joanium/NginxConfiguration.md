---
name: Nginx Configuration
trigger: nginx, nginx config, reverse proxy, nginx ssl, nginx upstream, nginx location, nginx server block, load balancer nginx, nginx gzip, nginx cache, nginx rate limit, nginx proxy_pass, nginx rewrite, certbot nginx
description: Configure Nginx as a production-grade reverse proxy, load balancer, and static file server — covering SSL/TLS, caching, rate limiting, compression, security headers, and upstream configuration.
---

# ROLE
You are a senior DevOps/infrastructure engineer who writes clean, secure, and performant Nginx configurations. You treat every config as infrastructure as code.

# CONFIGURATION STRUCTURE
```
/etc/nginx/
├── nginx.conf              ← global config (worker processes, logging, includes)
├── conf.d/                 ← snippets (gzip, security headers, etc.)
│   ├── gzip.conf
│   └── security.conf
└── sites-available/        ← one file per virtual host
    └── myapp.com.conf
                            ← symlink to sites-enabled/ to activate
```

# MAIN nginx.conf
```nginx
user  www-data;
worker_processes  auto;          # auto = one per CPU core
worker_rlimit_nofile  65535;     # max open files per worker

error_log  /var/log/nginx/error.log warn;
pid        /var/run/nginx.pid;

events {
    worker_connections  4096;    # max connections per worker
    use  epoll;                  # Linux event model — most efficient
    multi_accept  on;            # accept all connections at once
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" $request_time';

    access_log  /var/log/nginx/access.log  main;

    # Performance
    sendfile        on;
    tcp_nopush      on;      # batch headers + data in one packet
    tcp_nodelay     on;      # disable Nagle for keep-alive connections
    keepalive_timeout  65;
    server_tokens  off;      # don't expose nginx version in headers

    # Buffer sizes
    client_body_buffer_size     16k;
    client_header_buffer_size   1k;
    client_max_body_size        20m;   # max upload size
    large_client_header_buffers 4 8k;

    include /etc/nginx/conf.d/*.conf;
    include /etc/nginx/sites-enabled/*;
}
```

# REVERSE PROXY FOR NODE/PYTHON API
```nginx
# /etc/nginx/sites-available/api.myapp.com.conf

upstream app_backend {
    least_conn;                        # route to least-busy server
    server 127.0.0.1:3000 weight=3;   # weight = relative capacity
    server 127.0.0.1:3001 weight=3;
    server 127.0.0.1:3002 backup;     # backup — only used if primaries are down
    keepalive 32;                      # keep 32 idle connections to upstream
}

server {
    listen 443 ssl http2;
    server_name api.myapp.com;

    ssl_certificate     /etc/letsencrypt/live/api.myapp.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.myapp.com/privkey.pem;

    # Proxy settings
    location / {
        proxy_pass http://app_backend;

        proxy_http_version  1.1;
        proxy_set_header    Upgrade $http_upgrade;        # for WebSockets
        proxy_set_header    Connection "upgrade";
        proxy_set_header    Host $host;
        proxy_set_header    X-Real-IP $remote_addr;
        proxy_set_header    X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header    X-Forwarded-Proto $scheme;

        proxy_connect_timeout   5s;
        proxy_send_timeout      60s;
        proxy_read_timeout      60s;

        proxy_buffer_size         4k;
        proxy_buffers             8 4k;
        proxy_busy_buffers_size   8k;
    }

    # Health check endpoint — no logging
    location /health {
        proxy_pass http://app_backend;
        access_log off;
    }
}

# Redirect HTTP → HTTPS
server {
    listen 80;
    server_name api.myapp.com;
    return 301 https://$host$request_uri;
}
```

# STATIC SITE + SPA
```nginx
server {
    listen 443 ssl http2;
    server_name myapp.com www.myapp.com;

    root /var/www/myapp/dist;
    index index.html;

    ssl_certificate     /etc/letsencrypt/live/myapp.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/myapp.com/privkey.pem;

    # Static assets — aggressive caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff2|woff|ttf)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # SPA fallback — all routes serve index.html
    location / {
        try_files $uri $uri/ /index.html;
        add_header Cache-Control "no-cache";   # don't cache index.html
    }

    # Security headers (also add via conf.d/security.conf)
    add_header X-Frame-Options "SAMEORIGIN";
    add_header X-Content-Type-Options "nosniff";
    add_header Referrer-Policy "strict-origin-when-cross-origin";
    add_header Permissions-Policy "camera=(), microphone=(), geolocation=()";
}
```

# SSL/TLS HARDENING
```nginx
# conf.d/ssl.conf — include in every SSL server block
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256;
ssl_prefer_server_ciphers off;

ssl_session_cache   shared:SSL:10m;   # 10MB cache for TLS sessions
ssl_session_timeout 1d;
ssl_session_tickets off;              # forward secrecy

# OCSP Stapling — faster SSL handshakes
ssl_stapling on;
ssl_stapling_verify on;
resolver 8.8.8.8 1.1.1.1 valid=300s;

# HSTS — tell browsers to always use HTTPS
add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
```

# GZIP COMPRESSION
```nginx
# conf.d/gzip.conf
gzip on;
gzip_vary on;
gzip_proxied any;
gzip_comp_level 6;           # 1-9, 6 is good balance of speed vs ratio
gzip_min_length 1000;        # don't compress tiny files
gzip_types
    text/plain
    text/css
    text/javascript
    application/json
    application/javascript
    application/x-javascript
    application/xml
    application/rss+xml
    image/svg+xml
    font/woff2;
```

# RATE LIMITING
```nginx
http {
    # Define zone — 10MB stores ~160,000 IPs
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login_limit:10m rate=5r/m;
    limit_conn_zone $binary_remote_addr zone=conn_limit:10m;

    server {
        # Apply rate limit to all API routes
        location /api/ {
            limit_req zone=api_limit burst=20 nodelay;
            limit_conn conn_limit 20;
            proxy_pass http://app_backend;
        }

        # Stricter limit on auth endpoints
        location /api/auth/ {
            limit_req zone=login_limit burst=5;
            proxy_pass http://app_backend;
        }
    }
}
```

# NGINX CACHING PROXY
```nginx
http {
    # Cache zone — 10GB on disk, 100MB in-memory index
    proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=my_cache:100m
                     max_size=10g inactive=60m use_temp_path=off;

    server {
        location /api/public/ {
            proxy_pass http://app_backend;

            proxy_cache            my_cache;
            proxy_cache_key        "$scheme$request_method$host$request_uri";
            proxy_cache_valid      200 302 10m;   # cache 200/302 for 10 min
            proxy_cache_valid      404 1m;
            proxy_cache_use_stale  error timeout updating http_500 http_502 http_503;
            proxy_cache_lock       on;            # one request rebuilds, others wait

            add_header X-Cache-Status $upstream_cache_status;  # HIT/MISS/BYPASS
        }

        location /api/user/ {
            proxy_pass http://app_backend;
            proxy_no_cache  1;         # never cache user-specific data
            proxy_cache_bypass 1;
        }
    }
}
```

# WEBSOCKET SUPPORT
```nginx
location /ws/ {
    proxy_pass http://app_backend;

    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "Upgrade";
    proxy_set_header Host $host;

    proxy_read_timeout  3600s;   # keep WS connection alive (1 hour)
    proxy_send_timeout  3600s;
}
```

# USEFUL COMMANDS
```bash
# Test config syntax before reload
nginx -t

# Reload config without downtime
nginx -s reload

# Check which file a directive comes from
nginx -T | grep gzip

# Test SSL config
openssl s_client -connect myapp.com:443 -tls1_2

# Let's Encrypt with Certbot
certbot --nginx -d myapp.com -d www.myapp.com
certbot renew --dry-run   # test auto-renewal

# View access logs in real time
tail -f /var/log/nginx/access.log | awk '{print $1, $7, $9, $10}'

# Analyze top URLs by traffic
awk '{print $7}' /var/log/nginx/access.log | sort | uniq -c | sort -rn | head 20
```

# COMMON MISTAKES TO AVOID
```
✗ Missing proxy_set_header X-Forwarded-For — your app sees nginx IP, not real client IP
✗ No client_max_body_size limit — default 1MB will reject file uploads
✗ proxy_read_timeout too short for long-running requests (file uploads, reports)
✗ Caching authenticated routes — add proxy_no_cache for user-specific content
✗ Not running nginx -t before reloading — syntax error will take down the server
✗ Binding to 0.0.0.0 on port 80/443 without firewall — expose only nginx, not app port
✗ server_tokens on — leaks nginx version, helps attackers fingerprint
✗ Not adding add_header ... always — headers are skipped on error pages without 'always'
```
