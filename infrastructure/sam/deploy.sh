#!/usr/bin/env bash
# ==============================================================================
# Runbook Guardian — Deploy completo (Lambda + API Gateway + Frontend)
# Requiere: AWS SAM CLI, AWS CLI, perfil con permisos admin
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${SCRIPT_DIR}/../.."
TEMPLATE="${SCRIPT_DIR}/template.yaml"
STACK_NAME="${STACK_NAME:-runbook-guardian-api-dev}"
REGION="${AWS_REGION:-us-east-1}"
S3_DEPLOY_BUCKET="${S3_DEPLOY_BUCKET:-}"

echo "============================================================"
echo "  Runbook Guardian — Deploy Cloud"
echo "============================================================"
echo
echo "  Stack:    ${STACK_NAME}"
echo "  Región:   ${REGION}"
echo "  Template: ${TEMPLATE}"
echo

# --- Verificar SAM CLI ---
if ! command -v sam &> /dev/null; then
    echo "[ERROR] SAM CLI no instalada."
    echo "  Instalar: brew install aws-sam-cli"
    echo "  O:        pip install aws-sam-cli"
    exit 1
fi

# --- Build ---
echo "[1/4] Building Lambda package..."
cd "${PROJECT_ROOT}"
sam build \
    --template-file "${TEMPLATE}" \
    --build-dir "${SCRIPT_DIR}/.aws-sam/build" \
    --use-container || sam build \
    --template-file "${TEMPLATE}" \
    --build-dir "${SCRIPT_DIR}/.aws-sam/build"

echo "      ✓ Build completado"
echo

# --- Deploy ---
echo "[2/4] Desplegando stack..."
sam deploy \
    --template-file "${SCRIPT_DIR}/.aws-sam/build/template.yaml" \
    --stack-name "${STACK_NAME}" \
    --region "${REGION}" \
    --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND \
    --resolve-s3 \
    --no-confirm-changeset \
    --tags Project=runbook-guardian Environment=dev ManagedBy=sam

echo "      ✓ Stack desplegado"
echo

# --- Obtener outputs ---
echo "[3/4] Obteniendo URLs..."
API_URL=$(aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}" \
    --region "${REGION}" \
    --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" \
    --output text)

FRONTEND_BUCKET=$(aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}" \
    --region "${REGION}" \
    --query "Stacks[0].Outputs[?OutputKey=='FrontendBucketName'].OutputValue" \
    --output text)

FRONTEND_URL=$(aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}" \
    --region "${REGION}" \
    --query "Stacks[0].Outputs[?OutputKey=='FrontendUrl'].OutputValue" \
    --output text)

echo "  API URL:      ${API_URL}"
echo "  Frontend URL: ${FRONTEND_URL}"
echo "  Bucket:       ${FRONTEND_BUCKET}"
echo

# --- Deploy frontend estático ---
echo "[4/4] Subiendo frontend estático..."

# Generar config.js con la URL de la API
cat > "${PROJECT_ROOT}/frontend/static/config.js" << EOF
// Auto-generado por deploy.sh
window.API_BASE_URL = "${API_URL}";
EOF

# Subir archivos al bucket
aws s3 sync "${PROJECT_ROOT}/frontend/static/" "s3://${FRONTEND_BUCKET}/" \
    --region "${REGION}" \
    --delete

echo "      ✓ Frontend desplegado"
echo
echo "============================================================"
echo "  Despliegue completado!"
echo "============================================================"
echo
echo "  API:      ${API_URL}/api/v1/health"
echo "  Frontend: ${FRONTEND_URL}"
echo
echo "  Probar:"
echo "    curl ${API_URL}/api/v1/health"
echo "    curl -X POST ${API_URL}/api/v1/query -H 'Content-Type: application/json' -d '{\"query\":\"nginx no responde\"}'"
echo
