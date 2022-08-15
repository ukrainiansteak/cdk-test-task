import os

SERVICE_NAME = os.getenv("SERVICE_NAME", default="image-recognition-cdk")

ADMIN_POLICY_NAME = os.getenv(
    "ADMIN_POLICY_NAME",
    default="AdministratorAccess",
)
