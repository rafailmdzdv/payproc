# Copyright © 2026 Rafail Medzhidov <rafayt323@gmail.com>
# SPDX-License-Identifier: MIT

import uvicorn

from infrastructure.config import settings


def run() -> None:
    """Run uvicorn server with application configuration."""
    uvicorn.run(
        'server.api.app:app',
        host=settings.app_host,
        port=settings.app_port,
        reload=False,
    )


if __name__ == '__main__':
    run()
