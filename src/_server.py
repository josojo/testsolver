"""
This is the project's Entry point.
"""
from __future__ import annotations

import argparse
import decimal
import logging
import json
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from pydantic import BaseSettings

from src.models.batch_auction import BatchAuction
from src.models.settlement import Settlement
from src.oneinch.oneinch import OneInchExchange
from src.models.solver_args import SolverArgs
from src.util.schema import (
    BatchAuctionModel,
    SettledBatchAuctionModel,
)

# Set decimal precision.
decimal.getcontext().prec = 100

# Holds parameters passed on the command line when invoking the server.
# These will be merged with request solver parameters
SERVER_ARGS = None


# ++++ Interface definition ++++


# Server settings: Can be overridden by passing them as env vars or in a .env file.
# Example: PORT=8001 python -m src._server
class ServerSettings(BaseSettings):
    """Basic Server Settings"""

    host: str = "0.0.0.0"
    port: int = 8000


server_settings = ServerSettings()

# ++++ Endpoints: ++++


app = FastAPI(title="Batch auction solver")


@app.get("/health", status_code=200)
def health() -> bool:
    """Convenience endpoint to check if server is alive."""
    return True


@app.post("/solve", response_model=SettledBatchAuctionModel)
async def solve(problem: BatchAuctionModel, request: Request):  # type: ignore
    """API POST solve endpoint handler"""
    logging.debug(f"Received solve request {await request.json()}")
    solver_args = SolverArgs.from_request(request=request, meta=problem.metadata)

    batch = BatchAuction.from_dict(problem.dict(), solver_args.instance_name)

    print("Parameters Supplied", solver_args)

    # 1. Solve BatchAuction: update batch_auction with
    print("auction content", batch.orders[1])

    oneinch = OneInchExchange('0x4e3fbd56cd56c3e72c1403e103b45db9da5b9d2b')

    order = batch.orders[0]
    result = oneinch.get_swap(order.sell_token, order.buy_token, order.sell_amount)
    print("quote result", result)
    settlement = Settlement(batch.ref_token.value)
    if settlement.insert_prices(order, result):
        settlement.add_order(order)
        settlement.add_payload(result['tx']['to'], result['tx']['data'])
    print(settlement.as_dict())

    return settlement.as_dict()


# ++++ Server setup: ++++


if __name__ == "__main__":
    load_dotenv()

    parser = argparse.ArgumentParser(
        fromfile_prefix_chars="@",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    # TODO - enable flag to write files to persistent storage
    # parser.add_argument(
    #     "--write_auxiliary_files",
    #     type=bool,
    #     default=False,
    #     help="Write auxiliary instance and optimization files, or not.",
    # )

    parser.add_argument(
        "--log-level",
        type=str,
        default="info",
        help="Log level",
    )

    SERVER_ARGS = parser.parse_args()
    uvicorn.run(
        "__main__:app",
        host=server_settings.host,
        port=server_settings.port,
        log_level=SERVER_ARGS.log_level,
    )
