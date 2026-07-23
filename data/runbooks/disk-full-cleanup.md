---
title: "Disk Full - Emergency Cleanup Procedures"
service: "linux-infrastructure"
version: "2.1.0"
last_reviewed: "2026-07-05"
status: "active"
---

## Symptoms

- Disk usage at 90% or above on any mounted partition.
- Applications failing to write logs or temp files.
- Database refusing writes due to insufficient disk space.
- Alert: "Disk space critically low on /dev/sda1".

## Diagnosis

1. Check disk usage across all partitions:
   ```
   df -h
   ```

2. Identify largest directories consuming space:
   ```
   du -sh /* 2>/dev/null | sort -rh | head -10
   ```

3. Find largest files modified in the last 7 days:
   ```
   find / -type f -mtime -7 -size +100M -exec ls -lh {} \; 2>/dev/null
   ```

4. Check for deleted files still held open by processes:
   ```
   lsof +L1
   ```

5. Check log rotation status:
   ```
   ls -lh /var/log/*.log
   journalctl --disk-usage
   ```

## Resolution

1. Clean package manager cache (safe, recoverable):
   ```
   apt-get clean
   yum clean all
   ```

2. Remove old journal logs (keep last 3 days):
   ```
   journalctl --vacuum-time=3d
   ```

3. Compress large log files:
   ```
   find /var/log -name "*.log" -size +100M -exec gzip {} \;
   ```

4. Remove temporary files older than 7 days:
   ```
   find /tmp -type f -atime +7 -delete
   ```

5. If deleted files are held by processes, restart those services:
   ```
   systemctl restart <service-holding-deleted-files>
   ```

6. WARNING: Do NOT run `rm -rf /` or delete system directories.
   Only remove files you can identify and verify are safe to delete.

7. After cleanup, verify available space:
   ```
   df -h
   ```

## Escalation

- If disk is full and no safe files can be removed, escalate to infrastructure team for volume expansion.
- If database disk is full, engage the DBA team immediately.
- Consider adding additional EBS volumes if on AWS.

## Prevention

- Set disk usage alerts at 80% threshold.
- Implement log rotation with size limits (logrotate).
- Schedule weekly cleanup cron jobs for /tmp and old logs.
- Monitor disk growth trends for capacity planning.
