"""Coordinator agent entry point."""

import argparse
import asyncio
import json
import uuid

from src.schemas.request import InboundRequest, NormalizedRequest


def normalize(raw: InboundRequest) -> NormalizedRequest:
    return NormalizedRequest(
        request_id=str(uuid.uuid4()),
        channel=raw.channel,
        body=raw.body,
        subject=raw.subject,
        user_id=raw.user_id,
    )


async def run(request: NormalizedRequest, dry_run: bool = False) -> dict:
    """
    Main coordinator loop.
    In dry-run mode returns a stub result without calling the LLM,
    allowing make test / smoke-test to pass without an API key.
    """
    if dry_run:
        return {
            "request_id": request.request_id,
            "mode": "dry-run",
            "status": "ok",
            "message": "Coordinator reachable. LLM call skipped in dry-run mode.",
        }

    # TODO: implement real coordinator loop using Claude Agent SDK
    # Steps:
    #   1. classify category + priority
    #   2. enrich with user/asset context
    #   3. apply escalation rules
    #   4. route to specialist via Task tool
    #   5. validate structured output (retry loop, max 3)
    #   6. write audit log
    raise NotImplementedError("Coordinator LLM loop not yet implemented.")


def main() -> None:
    parser = argparse.ArgumentParser(description="IntakeAI coordinator agent")
    parser.add_argument("--request", help="JSON string of inbound request")
    parser.add_argument("--request-file", help="Path to JSON file")
    parser.add_argument("--dry-run", action="store_true", help="Skip LLM calls")
    parser.add_argument("--demo", action="store_true", help="Run demo with sample requests")
    parser.add_argument("--mcp", action="store_true", help="Connect to MCP server")
    args = parser.parse_args()

    if args.demo:
        raw_data = {"channel": "email", "body": "My laptop won't boot", "user_id": "u001"}
    elif args.request:
        raw_data = json.loads(args.request)
    elif args.request_file:
        with open(args.request_file) as f:
            raw_data = json.load(f)
    else:
        parser.error("Provide --request, --request-file, or --demo")

    inbound = InboundRequest(**raw_data)
    normalized = normalize(inbound)
    result = asyncio.run(run(normalized, dry_run=args.dry_run))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
