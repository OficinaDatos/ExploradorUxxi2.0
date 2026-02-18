import os
import requests
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

class UXXIClient:
    ENDPOINTS = ["/ac/api_sql/v1/_/sql", "/ress/api_sql/v1/_/sql"]

    def __init__(self):
        # Render inyectará estas variables automáticamente
        self.client_id = os.getenv("UXXI_CLIENT_ID", "")
        self.client_secret = os.getenv("UXXI_CLIENT_SECRET", "")
        self.base_url = os.getenv("UXXI_BASE_URL", "https://utec.universitasxxi.cloud/api/uxxi")
        self.timeout = int(os.getenv("UXXI_TIMEOUT", "60"))

        self._session = requests.Session()
        self._access_token: Optional[str] = None
        self._token_expires: Optional[datetime] = None
        self._valid_endpoint: Optional[str] = None

    def close(self):
        self._session.close()

    @property
    def token_ok(self) -> bool:
        return self._access_token and self._token_expires and datetime.now() < self._token_expires

    def auth(self) -> None:
        if self.token_ok:
            return
        if not self.client_id or not self.client_secret:
            raise RuntimeError("Faltan credenciales UXXI_CLIENT_ID / UXXI_CLIENT_SECRET.")

        url = f"{self.base_url}/sta/apipr/oauth2/v1/oauth/token"
        r = self._session.post(
            url,
            data={"grant_type": "client_credentials"},
            auth=(self.client_id, self.client_secret),
            timeout=15
        )
        if r.status_code >= 400:
            raise RuntimeError(f"Error de Auth ({r.status_code}): Verifica tus credenciales.")
        
        data = r.json()
        self._access_token = data["access_token"]
        expires_in = int(data.get("expires_in", 3600))
        self._token_expires = datetime.now() + timedelta(seconds=expires_in - 60)

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/sql",
            "Accept": "application/json",
        }

    def detect_endpoint(self) -> None:
        if self._valid_endpoint:
            return
        self.auth()
        for ep in self.ENDPOINTS:
            try:
                url = f"{self.base_url}{ep}"
                r = self._session.post(url, data="SELECT 1 FROM DUAL", headers=self._headers(), timeout=15)
                if r.status_code == 200 and "text/html" not in r.headers.get("content-type", "").lower():
                    self._valid_endpoint = ep
                    return
            except:
                continue
        raise RuntimeError("No se pudo conectar con el motor SQL de UXXI.")

    def sql(self, query: str) -> Dict[str, Any]:
        self.auth()
        self.detect_endpoint()
        url = f"{self.base_url}{self._valid_endpoint}"
        r = self._session.post(url, data=query, headers=self._headers(), timeout=self.timeout)
        if r.status_code >= 400:
            raise RuntimeError(f"Error SQL: {r.status_code}")
        return r.json()

    @staticmethod
    def to_rows(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        items = payload.get("items", [])
        if not items: return []
        return items[0].get("resultSet", {}).get("items", []) or []

