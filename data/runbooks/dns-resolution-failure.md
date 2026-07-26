---
title: "Fallo en Resolución DNS"
service: "networking"
version: "1.0.0"
last_reviewed: "2026-07-07"
status: "active"
---

## Síntomas

- Servicios reportando "Name or service not known" o "DNS resolution failed".
- Conexiones a servicios externos fallando intermitentemente.
- Latencia alta en resolución de nombres (> 1 segundo).
- Aplicaciones no pueden resolver nombres de servicios internos.
- Timeouts en llamadas HTTP donde el dominio no resuelve.

## Diagnóstico

1. Verificar resolución DNS del dominio afectado:
   ```
   dig dominio.com
   nslookup dominio.com
   ```

2. Verificar contra un DNS público para comparar:
   ```
   dig @8.8.8.8 dominio.com
   dig @1.1.1.1 dominio.com
   ```

3. Verificar el resolver configurado en el sistema:
   ```
   cat /etc/resolv.conf
   resolvectl status
   ```

4. Verificar si el servicio DNS local está corriendo:
   ```
   systemctl status systemd-resolved
   # En Kubernetes
   kubectl get pods -n kube-system -l k8s-app=kube-dns
   ```

5. Verificar latencia de resolución:
   ```
   time dig dominio.com
   # Si > 1s, hay un problema de rendimiento DNS
   ```

## Resolución

1. Si el resolver local no responde, reiniciarlo:
   ```
   systemctl restart systemd-resolved
   ```

2. Si es un problema de DNS en Kubernetes (CoreDNS):
   ```
   kubectl rollout restart deployment coredns -n kube-system
   ```

3. Como mitigación temporal, usar DNS público:
   ```
   # Agregar temporalmente a /etc/resolv.conf
   echo "nameserver 8.8.8.8" >> /etc/resolv.conf
   ```

4. Si el problema es con un dominio específico (propagación):
   ```
   # Verificar propagación global
   dig +trace dominio.com
   # Puede requerir esperar hasta 48h para propagación completa
   ```

5. Si hay cache DNS corrupto:
   ```
   # Limpiar cache
   resolvectl flush-caches
   # En macOS
   sudo dscacheutil -flushcache
   ```

## Escalamiento

- Si el DNS interno (Active Directory, Route53) falla, contactar al equipo de infraestructura de red.
- Si es un problema de propagación de DNS público, contactar al registrador.
- Si CoreDNS en Kubernetes está fallando, escalar al equipo de plataforma.

## Prevención

- Monitorear latencia de resolución DNS con alertas > 500ms.
- Configurar DNS redundante (primario + secundario).
- Usar TTL cortos para servicios que cambian frecuentemente.
- Implementar health checks que incluyan resolución DNS.
- Mantener registros DNS documentados y auditar cambios.
