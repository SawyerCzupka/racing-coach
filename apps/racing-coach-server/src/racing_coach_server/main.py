"""Entry point for running the Racing Coach Server with uvicorn."""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "racing_coach_server.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
