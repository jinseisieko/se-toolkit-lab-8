"""Entry point for running mcp_obs as a module."""

from mcp_obs.server import main

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
