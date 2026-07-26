#!/usr/bin/env bash
# ==============================================================================
# Runbook Guardian — Ejecutar Change Set (requiere aprobación previa)
# Solo ejecutar DESPUÉS de revisar el change set con create-change-set.sh
# ==============================================================================
set -euo pipefail

# --- Configuración ---
STACK_NAME="${STACK_NAME:-runbook-guardian-dev}"
CHANGE_SET_NAME="${CHANGE_SET_NAME:?ERROR: Debes especificar CHANGE_SET_NAME}"
REGION="${AWS_REGION:-us-east-1}"

echo "============================================================"
echo "  Runbook Guardian — Ejecutar Change Set"
echo "============================================================"
echo
echo "  Stack:      ${STACK_NAME}"
echo "  Change Set: ${CHANGE_SET_NAME}"
echo "  Región:     ${REGION}"
echo

# --- Confirmación ---
read -p "  ¿Confirmas la ejecución del change set? (yes/no): " CONFIRM
if [ "${CONFIRM}" != "yes" ]; then
    echo "  Cancelado por el usuario."
    exit 0
fi

echo

# --- Ejecutar Change Set ---
echo "[1/3] Ejecutando change set..."
aws cloudformation execute-change-set \
    --stack-name "${STACK_NAME}" \
    --change-set-name "${CHANGE_SET_NAME}" \
    --region "${REGION}"

echo "      ✓ Change set en ejecución"
echo

# --- Esperar finalización ---
echo "[2/3] Esperando finalización del stack..."

# Determinar si es CREATE o UPDATE
STACK_STATUS=$(aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}" \
    --region "${REGION}" \
    --query "Stacks[0].StackStatus" \
    --output text)

if [[ "${STACK_STATUS}" == *"CREATE"* ]]; then
    aws cloudformation wait stack-create-complete \
        --stack-name "${STACK_NAME}" \
        --region "${REGION}"
else
    aws cloudformation wait stack-update-complete \
        --stack-name "${STACK_NAME}" \
        --region "${REGION}"
fi

echo "      ✓ Stack completado"
echo

# --- Mostrar outputs ---
echo "[3/3] Outputs del stack:"
echo
aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}" \
    --region "${REGION}" \
    --query "Stacks[0].Outputs[].{Key:OutputKey,Value:OutputValue}" \
    --output table

echo
echo "============================================================"
echo "  Despliegue completado exitosamente."
echo "  Ejecutar smoke tests para verificar."
echo "============================================================"
