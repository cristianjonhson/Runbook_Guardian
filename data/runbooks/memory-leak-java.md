---
title: "Investigación de Memory Leak en Aplicación Java"
service: "java-applications"
version: "1.1.0"
last_reviewed: "2025-01-15"
status: "deprecated"
---

## Síntomas

- Uso de heap Java incrementando constantemente sin liberarse.
- OutOfMemoryError en logs de la aplicación.
- Pausas de garbage collection cada vez más largas y frecuentes.
- Degradación del tiempo de respuesta de la aplicación a lo largo de días.
- Contenedor/pod siendo OOM-killed por el orquestador.

## Diagnóstico

1. Verificar uso actual de memoria JVM:
   ```
   jstat -gcutil <PID> 1000 5
   ```

2. Revisar logs de GC para frecuencia de Full GC:
   ```
   grep "Full GC" /var/log/app/gc.log | tail -20
   ```

3. Capturar heap dump para análisis:
   ```
   jmap -dump:live,format=b,file=/tmp/heapdump.hprof <PID>
   ```

4. Verificar histograma de heap para conteo de objetos:
   ```
   jmap -histo:live <PID> | head -30
   ```

5. Monitorear tendencia de memoria en el tiempo:
   ```
   while true; do jstat -gcutil <PID> | tail -1; sleep 60; done
   ```

## Resolución

1. Si la aplicación no responde, reiniciarla inmediatamente:
   ```
   systemctl restart <servicio-java>
   ```

2. Incrementar tamaño de heap como mitigación temporal:
   ```
   # En la configuración del servicio, ajustar -Xmx:
   JAVA_OPTS="-Xmx4g -Xms2g"
   systemctl restart <servicio-java>
   ```

3. Analizar el heap dump con un profiler:
   - Abrir `/tmp/heapdump.hprof` en Eclipse MAT o VisualVM.
   - Buscar: retained heap size, dominator tree, leak suspects.

4. Patrones comunes de leak a verificar:
   - Cachés sin límite ni eviction.
   - Event listeners que no se desregistran.
   - Variables ThreadLocal que no se limpian.
   - Colecciones grandes creciendo sin control.

5. Después de identificar el leak, desplegar el fix y monitorear:
   ```
   # Verificar que el heap se estabiliza después del fix
   jstat -gcutil <PID> 5000 60
   ```

## Escalamiento

- Si el leak está en código de la aplicación, contactar al equipo de desarrollo con el análisis del heap dump.
- Si el leak está en una librería de terceros, verificar issues conocidos y parches.
- Si el restart inmediato no ayuda, considerar rollback a la última versión estable.

## Prevención

- Configurar alertas de uso de memoria al 80% del max heap.
- Habilitar logging de GC en todos los servicios Java.
- Ejecutar profiling periódico de memoria en staging.
- Implementar circuit breakers para prevenir fallos en cascada.
- Revisar tendencias de uso de memoria en revisiones operacionales semanales.
