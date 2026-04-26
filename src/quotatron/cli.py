"""Command-line entry point for quotatron."""
import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="quotatron")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("run", help="Run the display service (production)")
    sub.add_parser("preview", help="Run the web preview / animation tester")
    sub.add_parser("verify-sources", help="Test all configured API sources")

    args = parser.parse_args(argv)

    if args.command == "run":
        from quotatron.scheduler import run_service
        return run_service()
    if args.command == "preview":
        from quotatron.web_preview.server import run_preview
        return run_preview()
    if args.command == "verify-sources":
        from quotatron.api_refresh import verify_all_sources
        return verify_all_sources()
    return 1


if __name__ == "__main__":
    sys.exit(main())
