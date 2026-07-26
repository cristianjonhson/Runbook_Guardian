#!/usr/bin/env bash
# ==============================================================================
# Runbook Guardian — Eliminar Stack de Desarrollo
# SOLO para entorno dev. Requiere confirmación explícita.
# Nota: recursos con DeletionPolicy=Retain NO se eliminan automáticamente.
# ==============================================================================
set -euo pipefail

# --- Configuración ---
STACK_NAME="${STACK_NAME:-runbook-guardian-dev}"
REGION="${AWS_REGION:-us-east-1}"

echo "============================================================"
echo "  Runbook Guardian — Eliminar Stack"
echo "============================================================"
echo
echo "  Stack:  ${STACK_NAME}"
echo "  Región: ${REGION}"
echo

# --- Verificar que el stack existe ---
STACK_STATUS=$(aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}" \
    --region "${REGION}" \
    --query "Stacks[0].StackStatus" \
    --output text 2>/dev/null || echo "NO_EXIST")

if [ "${STACK_STATUS}" = "NO_EXIST" ]; then
    echo "  [INFO] El stack no existe. Nada que eliminar."
    exit 0
fi

echo "  Estado actual: ${STACK_STATUS}"
echo

# --- Listar recursos ---
echo "  Recursos en el stack:"
aws cloudformation list-stack-resources \
    --stack-name "${STACK_NAME}" \
    --region "${REGION}" \
    --query "StackResourceSummaries[].{Type:ResourceType,LogicalId:LogicalResourceId,Status:ResourceStatus}" \
    --output table

echo
echo "  ⚠️  ADVERTENCIA:"
echo "  - Recursos con DeletionPolicy=Retain NO se eliminarán."
echo "  - El bucket S3 quedará retenido (eliminar manualmente si necesario)."
echo "  - Esta acción NO es reversible para recursos sin Retain."
echo

# --- Confirmación ---
read -p "  ¿Eliminar el stack '${STACK_NAME}'? Escribe 'DELETE' para confirmar: " CONFIRM
if [ "${CONFIRM}" != "DELETE" ]; then
    echo "  Cancelado. Debe escribir 'DELETE' exactamente."
    exit 0
fi

echo

# --- Eliminar stack ---
echo "[1/2] Eliminando stack..."
aws cloudformation delete-stack \
    --stack-name "${STACK_NAME}" \
    --region "${REGION}"

echo "      ✓ Eliminación iniciada"
echo

# --- Esperar ---
echo "[2/2] Esperando eliminación completa..."
aws cloudformation wait stack-delete-complete \
    --stack-name "${STACK_NAME}" \
    --region "${REGION}"

echo "      ✓ Stack eliminado"
echo

echo "============================================================"
echo "  Stack eliminado exitosamente."
echo "  Recursos retenidos (verificar manualmente):"
echo "    - Bucket S3: runbook-guardian-source-*-dev"
echo "  Para eliminar el bucket retenido:"
echo "    aws s3 rm s3://<bucket-name> --recursive"
echo "    aws s3 rb s3://<bucket-name>"
echo "============================================================"
