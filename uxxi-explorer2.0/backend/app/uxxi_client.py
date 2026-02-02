import os
import requests
from typing import List
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

class UXXIClient:
    ENDPOINTS = ["/ac/api_sql/v1/_/sql", "/ress/api_sql/v1/_/sql"]

    def __init__(self):
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
            raise RuntimeError("Faltan UXXI_CLIENT_ID / UXXI_CLIENT_SECRET en variables de entorno.")

        url = f"{self.base_url}/sta/apipr/oauth2/v1/oauth/token"
        r = self._session.post(
            url,
            data={"grant_type": "client_credentials"},
            auth=(self.client_id, self.client_secret),
            timeout=15
        )
        if r.status_code >= 400:
            raise RuntimeError(f"Auth falló ({r.status_code}): {r.text[:300]}")
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

        last_err = None
        for ep in self.ENDPOINTS:
            try:
                self._probe(ep)
                self._valid_endpoint = ep
                return
            except Exception as e:
                last_err = e

        raise RuntimeError(f"No se detectó endpoint SQL válido. Último error: {last_err}")

    def _probe(self, ep: str) -> None:
        url = f"{self.base_url}{ep}"
        r = self._session.post(url, data="SELECT 1 FROM DUAL", headers=self._headers(), timeout=15)
        ct = (r.headers.get("content-type") or "").lower()

        # Si devuelve HTML, casi siempre es gateway/login/denegado.
        if "text/html" in ct:
            raise RuntimeError(f"Probe devolvió HTML ({r.status_code}). Posible bloqueo/red/permisos.")

        if r.status_code >= 400:
            raise RuntimeError(f"Probe falló ({r.status_code}): {r.text[:300]}")

        # Debe ser JSON
        _ = r.json()

    def sql(self, query: str) -> Dict[str, Any]:
        self.auth()
        self.detect_endpoint()

        url = f"{self.base_url}{self._valid_endpoint}"
        r = self._session.post(url, data=query, headers=self._headers(), timeout=self.timeout)
        ct = (r.headers.get("content-type") or "").lower()

        if "text/html" in ct:
            raise RuntimeError(f"SQL devolvió HTML ({r.status_code}). Posible permisos/red.")
        if r.status_code >= 400:
            raise RuntimeError(f"SQL error ({r.status_code}): {r.text[:300]}")
        return r.json()

    @staticmethod
    def to_rows(payload: Dict[str, Any]) -> List[Dict[str, Any]]:

        items = payload.get("items", [])
        if not items:
            return []
        rs = items[0].get("resultSet", {})
        return rs.get("items", []) or []

