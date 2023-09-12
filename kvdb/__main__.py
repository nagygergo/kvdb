"""Entrypoint for kvdb."""
import asyncio
from .server import run_from_cli_args


def main():
    """Runs kvdb."""
    asyncio.run(run_from_cli_args())


if __name__ == "__main__":
    main()
