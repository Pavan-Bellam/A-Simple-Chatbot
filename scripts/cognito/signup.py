import sys
import boto3
import hmac, hashlib, base64
from app.core.settings import settings
import json
from pathlib import Path
from app.services.user import create_user
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

    params = {
        "ClientId": settings.cognito_app_client_id,
        "Username": username,  
        "Password": config["password"],
        "UserAttributes": [
            {"Name": "email", "Value": config["email"]},
            {"Name": "given_name", "Value": config["givenName"]},
            {"Name": "family_name", "Value": config["familyName"]},
        ],
    }
    if settings.cognito_app_client_secret:
        params["SecretHash"] = _secret_hash(username)

    # Step 1: Sign up
    resp = client.sign_up(**params)
    user_sub = resp['UserSub']
    print("Signup response:", resp)

    # Step 2: Prompt for confirmation code
    print("⚠️ Check your email/SMS for the confirmation code.")
    code = input("Enter confirmation code: ").strip()

    confirm_params = {
        "ClientId": settings.cognito_app_client_id,
        "Username": username,
        "ConfirmationCode": code,
    }
    if settings.cognito_app_client_secret:
        confirm_params["SecretHash"] = _secret_hash(username)

    confirm_resp = client.confirm_sign_up(**confirm_params)
    if confirm_resp['ResponseMetadata']['HTTPStatusCode'] == 200:

        create_user({
            "sub": user_sub,
            "email": config["email"],
            "first_name": config["givenName"],
            "last_name": config["familyName"]
        })

    print("User confirmed:", confirm_resp)
