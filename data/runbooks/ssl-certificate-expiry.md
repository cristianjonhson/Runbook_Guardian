---
title: "Expiración de Certificado SSL/TLS"
service: "security"
version: "1.0.0"
last_reviewed: "2026-07-13"
status: "active"
---

## Síntomas

- Navegadores mostrando "Your connection is not private" o "NET::ERR_CERT_DATE_INVALID".
- Clientes API recibiendo errores de verificación SSL.
- Health checks fallando por certificado inválido.
- Alertas de monitoreo por certificado próximo a expirar o ya expirado.
- Logs mostrando "SSL certificate has expired".

## Diagnóstico

1. Verificar fecha de expiración del certificado:
   ```
   echo | openssl s_client -connect dominio.com:443 2>/dev/null | openssl x509 -noout -dates
   ```

2. Verificar el certificado localmente:
   ```
   openssl x509 -in /etc/ssl/certs/dominio.crt -noout -enddate
   ```

3. Verificar la cadena completa del certificado:
   ```
   openssl verify -CAfile /etc/ssl/certs/ca-bundle.crt /etc/ssl/certs/dominio.crt
   ```

4. Verificar si el certificado en el servidor coincide con la clave privada:
   ```
   openssl x509 -noout -modulus -in cert.crt | md5sum
   openssl rsa -noout -modulus -in key.pem | md5sum
   ```

5. Verificar todos los certificados que expiran en los próximos 30 días:
   ```
   find /etc/ssl/certs -name "*.crt" -exec openssl x509 -noout -enddate -in {} \; | sort
   ```

## Resolución

1. Si usa Let's Encrypt, renovar el certificado:
   ```
   certbot renew --force-renewal
   systemctl reload nginx
   ```

2. Si usa certificado comercial, instalar el nuevo certificado:
   ```
   cp nuevo-certificado.crt /etc/ssl/certs/dominio.crt
   cp nuevo-certificado.key /etc/ssl/private/dominio.key
   nginx -t && systemctl reload nginx
   ```

3. Verificar que el nuevo certificado es válido:
   ```
   echo | openssl s_client -connect dominio.com:443 2>/dev/null | openssl x509 -noout -dates
   curl -vI https://dominio.com 2>&1 | grep "expire date"
   ```

4. Si el certificado intermedio falta (chain incompleta):
   ```
   # Descargar el certificado intermedio de la CA
   # Concatenar: cert + intermediate + root
   cat dominio.crt intermediate.crt > fullchain.crt
   ```

5. Reiniciar todos los servicios que usan el certificado:
   ```
   systemctl reload nginx
   systemctl reload haproxy
   ```

## Escalamiento

- Si no se tiene acceso para renovar el certificado, contactar al equipo de seguridad.
- Si el certificado es wildcard y afecta múltiples servicios, coordinar el reemplazo con cada equipo.
- Si la CA reporta problemas, considerar cambiar de proveedor.

## Prevención

- Configurar alertas de expiración a 30, 14 y 7 días antes.
- Automatizar renovación con certbot o similar.
- Mantener inventario de todos los certificados y sus fechas de expiración.
- Usar certificados con vigencia corta (90 días) y renovación automática.
- Verificar semanalmente que los cron de renovación funcionan.
