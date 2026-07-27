"""AWS Lambda handler para Runbook Guardian.

Usa Mangum para adaptar FastAPI a Lambda + API Gateway.
Mangum traduce los eventos de API Gateway a ASGI y viceversa.
"""

from mangum import Mangum

from backend.main import app

# Handler para Lambda — recibe eventos de API Gateway
handler = Mangum(app, lifespan="off")
