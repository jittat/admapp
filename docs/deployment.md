# Deployment (gunicorn + systemd + nginx)

Point-in-time notes on how the production server runs admapp, plus known
open issues. Verify against the server before relying on details.

Server-specific values (user, directories, socket path) are deliberately
left out and shown as placeholders:

| Placeholder     | Meaning                                         |
|-----------------|-------------------------------------------------|
| `<deploy-user>` | Unix user gunicorn runs as                      |
| `<project-dir>` | Checkout of this repo on the server             |
| `<venv-dir>`    | Python virtualenv used by gunicorn              |
| `<socket-path>` | Unix socket gunicorn binds to and nginx proxies |

## Layout

nginx serves the site under the `/kuadm/` prefix and proxies to gunicorn
over a unix socket. gunicorn is supervised by systemd.

### systemd unit

Typical location: `/etc/systemd/system/<name>.service` (confirm the actual
path and service name with `systemctl cat <service>`).

```ini
[Unit]
Description=gunicorn admapp daemon
After=network.target

[Service]
User=<deploy-user>
Group=www-data
WorkingDirectory=<project-dir>
ExecStart=<venv-dir>/bin/gunicorn --access-logfile - --workers 50 --bind unix:<socket-path> admapp.wsgi:application

[Install]
WantedBy=multi-user.target
```

- Group `www-data` lets nginx reach the socket.
- No `-c` config file: all gunicorn settings are on `ExecStart`. gunicorn
  would still auto-load `gunicorn.conf.py` from `WorkingDirectory` if one
  appeared there.
- No `--timeout`, so gunicorn's default of 30s applies. Long requests
  (exports, PDF checks) are killed at that limit.
- 50 workers is above the usual `2 × cores + 1` guideline; watch memory at
  peak periods.
- Access log goes to stdout, so it lands in journald (`journalctl -u <service>`).

After editing the unit: `sudo systemctl daemon-reload && sudo systemctl
restart <service>`. After code/dependency changes: `restart` only.

### nginx location

```nginx
location /kuadm/ {
    include proxy_params;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    #proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;

    proxy_pass http://unix:<socket-path>:/;
}
```

The trailing `/` in `proxy_pass` strips `/kuadm/` before the request
reaches Django; Django builds `/kuadm/...` URLs from the script prefix.

## Open issues

### `DisallowedHost` error emails with the socket path as host (open, 2026-10-06)

**Symptom.** Many admin error emails like:

```
DisallowedHost at /regis/login/test-cgi
Invalid HTTP_HOST header: '<socket-path>:'.
The domain name provided is not valid according to RFC 1034/1035.
Request URL: https://<socket-path>:/kuadm/regis/login/test-cgi?*
```

Other paths seen: `/regis/register/?<script`, `/en/regis/forget/formmail`.
These are vulnerability-scanner probes. Django rejects them with a 400, so
nothing gets through. The problem is the email noise.

**Cause.** Scanners send requests with no `Host` header (typically
HTTP/1.0). `proxy_params` (Debian/Ubuntu) sets
`proxy_set_header Host $http_host;`, and `$http_host` is empty in that
case, so nginx forwards no `Host` header at all. gunicorn then fills in
`SERVER_NAME` from its bind address, which is the socket path, with an
empty `SERVER_PORT`. Django builds `<socket-path>:` as the host, rejects
it as an invalid hostname and logs the error to
`django.security.DisallowedHost`, which emails the admins.

**Fix 1: nginx (root cause).** Send `Host $host`. `$host` falls back to
`server_name` when the client sent no Host header. Don't just uncomment
the `Host $host` line: together with `include proxy_params` that sends two
`Host` headers, which newer gunicorn rejects. Replace the include with
explicit headers:

```nginx
location /kuadm/ {
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    proxy_pass http://unix:<socket-path>:/;
}
```

Keep `X-Forwarded-Proto` (from `proxy_params`), because Django relies on
it to know requests came in over https. Check the server's
`/etc/nginx/proxy_params` first, then run
`sudo nginx -t && sudo systemctl reload nginx`. Optionally, add a
`default_server` block that does `return 444;` so requests for unknown
hostnames never reach gunicorn.

**Fix 2: Django (stop the emails).** Scanners that send a made-up `Host`
still raise `DisallowedHost` after Fix 1. Silence that logger in `LOGGING`
(`admapp/settings.py`), as the Django docs recommend:

```python
'handlers': {
    # ...
    'null': {'class': 'logging.NullHandler'},
},
'loggers': {
    # ...
    'django.security.DisallowedHost': {
        'handlers': ['null'],
        'propagate': False,
    },
},
```

Those requests still get a 400; only the email goes away.
