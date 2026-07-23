---
title: "Restart Nginx Service"
service: "nginx"
version: "1.2.0"
last_reviewed: "2026-07-01"
status: "active"
---

## Symptoms

- 502 Bad Gateway errors reported by users or monitoring.
- 503 Service Unavailable responses.
- Connection refused on port 80 or 443.
- Health check failures from load balancer.
- Nginx worker processes consuming excessive memory.

## Diagnosis

1. Check Nginx service status:
   ```
   systemctl status nginx
   ```

2. Verify Nginx is listening on expected ports:
   ```
   ss -tlnp | grep nginx
   ```

3. Check recent error logs:
   ```
   tail -50 /var/log/nginx/error.log
   ```

4. Verify configuration syntax:
   ```
   nginx -t
   ```

5. Check if upstream backends are healthy:
   ```
   curl -I http://localhost:8080/health
   ```

6. Check worker process count and connections:
   ```
   ps aux | grep nginx
   cat /proc/$(cat /var/run/nginx.pid)/status
   ```

## Resolution

1. If configuration test passes, try a graceful reload first:
   ```
   systemctl reload nginx
   ```
   This reloads configuration without dropping connections.

2. If reload does not resolve the issue, perform a full restart:
   ```
   systemctl restart nginx
   ```

3. Verify the service is running after restart:
   ```
   systemctl status nginx
   curl -I http://localhost
   ```

4. If restart fails, check for port conflicts:
   ```
   ss -tlnp | grep :80
   ss -tlnp | grep :443
   ```

5. If another process holds the port, identify and stop it:
   ```
   fuser -k 80/tcp
   systemctl start nginx
   ```

6. Verify health from the load balancer's perspective:
   ```
   curl -I http://localhost/health
   ```

## Escalation

- If Nginx repeatedly crashes after restart, escalate to the platform team.
- If upstream backends are failing, engage the application team.
- If SSL/TLS errors occur, check certificate expiry and engage security team.

## Prevention

- Monitor Nginx error rates and response times.
- Set alerts for worker process crashes.
- Implement graceful restart in deployment pipelines.
- Review and test configuration changes in staging before production.
