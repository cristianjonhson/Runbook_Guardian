#!/usr/bin/env bash
# ==============================================================================
# Runbook Guardian — Validación de plantillas CloudFormation
# Ejecuta cfn-lint (estático) y validate-template (AWS API).
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATES_DIR="${SCRIPT_DIR}/../templates"

echo "============================================================"
echo "  Runbook Guardian — Validación CloudFormation"
echo "============================================================"
echo

# --- 1. Validación estática con cfn-lint ---
echo "[1/2] Ejecutando cfn-lint..."
if command -v cfn-lint &> /dev/null; then
    cfn-lint "${TEMPLATES_DIR}"/*.yaml
    echo "      ✓ cfn-lint: sin errores"
else
    echo "      ⚠ cfn-lint no instalado. Instalar con: pip install cfn-lint"
    exit 1
fi

echo

# --- 2. Validación con AWS CloudFormation API ---
echo "[2/2] Ejecutando aws cloudformation validate-template..."
for template in "${TEMPLATES_DIR}"/*.yaml; do
    template_name=$(basename "$template")
    aws cloudformation validate-template \
        --template-body "file://${template}" \
        --output text > /dev/null
    echo "      ✓ ${template_name}: válida"
done

echo
echo "============================================================"
echo "  Todas las plantillas son válidas."
echo "============================================================"
