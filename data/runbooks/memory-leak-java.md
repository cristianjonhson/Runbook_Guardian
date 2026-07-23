---
title: "Java Application Memory Leak Investigation"
service: "java-applications"
version: "1.1.0"
last_reviewed: "2025-01-15"
status: "deprecated"
---

## Symptoms

- Java heap usage steadily increasing over time without release.
- OutOfMemoryError in application logs.
- Garbage collection pauses becoming longer and more frequent.
- Application response time degradation over days.
- Container/pod being OOM-killed by orchestrator.

## Diagnosis

1. Check current JVM memory usage:
   ```
   jstat -gcutil <PID> 1000 5
   ```

2. Review GC logs for Full GC frequency:
   ```
   grep "Full GC" /var/log/app/gc.log | tail -20
   ```

3. Capture heap dump for analysis:
   ```
   jmap -dump:live,format=b,file=/tmp/heapdump.hprof <PID>
   ```

4. Check heap histogram for object count:
   ```
   jmap -histo:live <PID> | head -30
   ```

5. Monitor memory trend over time:
   ```
   while true; do jstat -gcutil <PID> | tail -1; sleep 60; done
   ```

## Resolution

1. If the application is unresponsive, restart it immediately:
   ```
   systemctl restart <java-service>
   ```

2. Increase heap size as temporary mitigation:
   ```
   # In service configuration, adjust -Xmx:
   JAVA_OPTS="-Xmx4g -Xms2g"
   systemctl restart <java-service>
   ```

3. Analyze the heap dump with a profiler:
   - Open `/tmp/heapdump.hprof` in Eclipse MAT or VisualVM.
   - Look for: retained heap size, dominator tree, leak suspects.

4. Common leak patterns to check:
   - Unbounded caches without eviction.
   - Event listeners not being unregistered.
   - ThreadLocal variables not cleaned up.
   - Large collections growing without bounds.

5. After identifying the leak, deploy a fix and monitor:
   ```
   # Verify heap stabilizes after fix
   jstat -gcutil <PID> 5000 60
   ```

## Escalation

- If the leak is in application code, engage the development team with the heap dump analysis.
- If the leak is in a third-party library, check for known issues and patches.
- If immediate restart does not help, consider rolling back to the last known good version.

## Prevention

- Set up memory usage alerts at 80% of max heap.
- Enable GC logging in all Java services.
- Run periodic memory profiling in staging.
- Implement circuit breakers to prevent cascading failures.
- Review memory usage trends in weekly operational reviews.
