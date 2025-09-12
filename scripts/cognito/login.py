import boto3
import hmac, hashlib, base64
from app.core.settings import settings
import json
from pathlib import Path
from botocore.exceptions import ClientError

client = boto3.client("cognito-idp", region_name=settings.cognito_region)

def _secret_hash(username: str) -> str:
    msg = username + settings.cognito_app_client_id
    dig = hmac.new(
        settings.cognito_app_client_secret.encode("utf-8"),
        msg.encode("utf-8"),
        hashlib.sha256
    ).digest()
    return base64.b64encode(dig).decode()

if __name__ == "__main__":
    config_path = Path(__file__).parent / "config.json"

    if not config_path.exists():
        raise FileNotFoundError(
            f"Missing config file: {config_path}. "
            "Please create it from config.template.json or follow the README instructions."
        )

    with config_path.open() as f:
        config = json.load(f)

    username = config["username"]
    password = config["password"]

    params = {
        "ClientId": settings.cognito_app_client_id,
        "AuthFlow": "USER_PASSWORD_AUTH",
        "AuthParameters": {
            "USERNAME": username,
            "PASSWORD": password,
        },
    }
    if settings.cognito_app_client_secret:
        params["AuthParameters"]["SECRET_HASH"] = _secret_hash(username)

    try:
        resp = client.initiate_auth(**params)
        tokens = resp["AuthenticationResult"]

        print("Login successful!")
        # print("ID Token:", tokens["IdTokena])
        print("Access Token:", tokens["AccessToken"])
        # print("Refresh Token:", tokens["RefreshToken"])
    except ClientError as e:
        print("Login failed:", e.response["Error"]["Message"])
