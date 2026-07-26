#!/usr/bin/env bash
# ==============================================================================
# Runbook Guardian — Crear Change Set (sin ejecutar)
# Crea un change set para revisión humana antes del despliegue.
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATES_DIR="${SCRIPT_DIR}/../templates"
PARAMETERS_DIR="${SCRIPT_DIR}/../parameters"

# --- Configuración ---
STACK_NAME="${STACK_NAME:-runbook-guardian-dev}"
TEMPLATE_FILE="${TEMPLATES_DIR}/main.yaml"
PARAMETERS_FILE="${PARAMETERS_FILE:-${PARAMETERS_DIR}/dev.example.json}"
CHANGE_SET_NAME="${CHANGE_SET_NAME:-changeset-$(date +%Y%m%d-%H%M%S)}"
REGION="${AWS_REGION:-us-east-1}"

echo "============================================================"
echo "  Runbook Guardian — Crear Change Set"
echo "============================================================"
echo
echo "  Stack:      ${STACK_NAME}"
echo "  Template:   ${TEMPLATE_FILE}"
echo "  Parameters: ${PARAMETERS_FILE}"
echo "  Change Set: ${CHANGE_SET_NAME}"
echo "  Región:     ${REGION}"
echo

# --- Verificar si el stack existe ---
STACK_EXISTS=$(aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}" \
    --region "${REGION}" \
    --query "Stacks[0].StackStatus" \
    --output text 2>/dev/null || echo "NO_EXIST")

if [ "${STACK_EXISTS}" = "NO_EXIST" ]; then
    CHANGE_SET_TYPE="CREATE"
    echo "  [INFO] Stack no existe. Tipo: CREATE"
else
    CHANGE_SET_TYPE="UPDATE"
    echo "  [INFO] Stack existe (${STACK_EXISTS}). Tipo: UPDATE"
fi

echo

# --- Crear Change Set ---
echo "[1/2] Creando change set..."
aws cloudformation create-change-set \
    --stack-name "${STACK_NAME}" \
    --template-body "file://${TEMPLATE_FILE}" \
    --parameters "file://${PARAMETERS_FILE}" \
    --change-set-name "${CHANGE_SET_NAME}" \
    --change-set-type "${CHANGE_SET_TYPE}" \
    --capabilities CAPABILITY_NAMED_IAM \
    --region "${REGION}" \
    --tags \
        Key=Project,Value=runbook-guardian \
        Key=Environment,Value=dev \
        Key=ManagedBy,Value=cloudformation

echo "      ✓ Change set creado: ${CHANGE_SET_NAME}"
echo

# --- Esperar que el change set esté listo ---
echo "[2/2] Esperando que el change set esté disponible..."
aws cloudformation wait change-set-create-complete \
    --stack-name "${STACK_NAME}" \
    --change-set-name "${CHANGE_SET_NAME}" \
    --region "${REGION}" 2>/dev/null || true

# --- Mostrar cambios ---
echo
echo "============================================================"
echo "  Cambios propuestos:"
echo "============================================================"
aws cloudformation describe-change-set \
    --stack-name "${STACK_NAME}" \
    --change-set-name "${CHANGE_SET_NAME}" \
    --region "${REGION}" \
    --query "Changes[].ResourceChange.{Action:Action,LogicalId:LogicalResourceId,Type:ResourceType,Replacement:Replacement}" \
    --output table

echo
echo "============================================================"
echo "  REVISAR los cambios antes de ejecutar."
echo "  Para ejecutar: CHANGE_SET_NAME=${CHANGE_SET_NAME} ./execute-change-set.sh"
echo "============================================================"
