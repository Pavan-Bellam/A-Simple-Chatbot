from app.main import app
from fastapi.openapi.utils import get_openapi
import yaml
from pathlib import Path

schema = get_openapi(
    title=app.title,
    version=app.version,
    description=app.description,
    routes=app.routes,
)

out = Path("docs/openapi.yaml")
out.parent.mkdir(exist_ok=True)
out.write_text(yaml.safe_dump(schema, sort_keys=False), encoding="utf-8")
print(f"✅ Wrote {out.resolve()}")
