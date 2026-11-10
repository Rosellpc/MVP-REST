"""Negotiate ChatGPT's current CIMD methods with DOT's public-client support."""
from urllib.parse import urlsplit

from oauth2_provider.cimd import SafeMetadataFetcher


class ChatGPTMetadataFetcher(SafeMetadataFetcher):
    def fetch(self, client_id):
        # Retain DOT's HTTPS, DNS/IP checks, timeout and response-size limits.
        metadata, max_age = super().fetch(client_id)
        methods = metadata.get("token_endpoint_auth_methods_supported")
        if (urlsplit(client_id).hostname == "chatgpt.com"
                and isinstance(methods, list)
                and all(isinstance(method, str) for method in methods)
                and "none" in methods):
            # OpenAI's plural field lists supported methods without preference.
            # The legacy singular preference can be private_key_jwt, unsupported
            # by DOT's CIMD resolver. Select the mutually supported public flow.
            metadata = {**metadata, "token_endpoint_auth_method": "none"}
        return metadata, max_age
