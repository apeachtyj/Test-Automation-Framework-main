import os

from base.flask_service import api


if __name__ == "__main__":
    host = os.getenv("MOCK_HOST", "127.0.0.1")
    port = int(os.getenv("MOCK_PORT", "8787"))
    api.run(host=host, port=port, debug=False, use_reloader=False)
