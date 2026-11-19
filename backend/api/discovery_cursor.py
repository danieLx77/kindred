"""Authenticated encryption for public discovery cursors."""

import base64
import json
import secrets

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from projects.models import Continuation, DiscoveryQuery

MAX_CURSOR_LENGTH = 6144
_NONCE_SIZE = 12


class InvalidCursor(ValueError):
    pass


class DiscoveryCursors:
    def __init__(self) -> None:
        self._cipher = AESGCM(AESGCM.generate_key(bit_length=256))

    @staticmethod
    def _context(query: DiscoveryQuery) -> bytes:
        return json.dumps(
            ["kindred-discovery-v1", query.text, query.page_size]
        ).encode()

    def encode(
        self, continuation: Continuation, page: int, query: DiscoveryQuery
    ) -> str:
        nonce = secrets.token_bytes(_NONCE_SIZE)
        payload = json.dumps([page, continuation.token]).encode()
        encrypted = self._cipher.encrypt(nonce, payload, self._context(query))
        return base64.urlsafe_b64encode(nonce + encrypted).decode()

    def decode(self, cursor: str, query: DiscoveryQuery) -> tuple[int, Continuation]:
        try:
            encoded = cursor.encode("ascii")
            raw = base64.b64decode(encoded, altchars=b"-_", validate=True)
            if base64.urlsafe_b64encode(raw) != encoded:
                raise ValueError
            payload = self._cipher.decrypt(
                raw[:_NONCE_SIZE], raw[_NONCE_SIZE:], self._context(query)
            )
        except (ValueError, InvalidTag):
            raise InvalidCursor from None

        # The authenticated payload was constructed by encode in this lifecycle.
        page, token = json.loads(payload)
        return page, Continuation(token)
