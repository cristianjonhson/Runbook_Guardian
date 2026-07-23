---
title: "High CPU Usage on Linux Servers"
service: "linux-infrastructure"
version: "1.3.0"
last_reviewed: "2026-07-10"
status: "active"
---

## Symptoms

- CPU usage consistently above 90% for more than 5 minutes.
- Slow response times from services running on the host.
- Load average exceeds the number of available CPU cores.
- Alerts triggered from monitoring system (CloudWatch, Datadog, Prometheus).

## Diagnosis

1. Check current CPU usage and top processes:
   ```
   top -bn1 | head -20
   ```

2. Identify specific processes consuming CPU:
   ```
   ps aux --sort=-%cpu | head -10
   ```

3. Check load average history:
   ```
   uptime
   sar -u 1 5
   ```

4. Verify if the issue is user-space or kernel:
   ```
   vmstat 1 5
   ```
   - High `us` (user): application-level issue.
   - High `sy` (system): kernel or I/O issue.

5. Check for runaway processes or fork bombs:
   ```
   ps -eo pid,ppid,%cpu,cmd --sort=-%cpu | head -20
   ```

## Resolution

1. If a specific application is consuming excessive CPU, restart the service:
   ```
   systemctl restart <service-name>
   ```

2. If a runaway process is detected, reduce its priority:
   ```
   renice +10 -p <PID>
   ```

3. If the process is unresponsive and non-critical, terminate it:
   ```
   kill -15 <PID>
   ```
   Wait 30 seconds. If still running:
   ```
   kill -9 <PID>
   ```

4. If CPU is high due to legitimate load, consider scaling:
   - Horizontal: add more instances behind the load balancer.
   - Vertical: resize the instance (requires downtime).

5. After resolution, verify CPU has returned to normal:
   ```
   top -bn1 | grep "Cpu(s)"
   ```

## Escalation

- If the issue persists after restarting the service, escalate to the application team.
- If multiple hosts are affected simultaneously, check for upstream dependency issues.
- If kernel CPU is high, engage the infrastructure team for deeper analysis.

## Prevention

- Set up CPU usage alerts at 80% threshold.
- Implement auto-scaling policies for predictable load patterns.
- Review application performance quarterly.
