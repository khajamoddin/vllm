import argparse
import sys
import httpx
from vllm.entrypoints.cli.types import CLISubcommand
from vllm.utils.argparse_utils import FlexibleArgumentParser

class AdminSubcommand(CLISubcommand):
    name = "admin"

    @staticmethod
    def cmd(args: argparse.Namespace) -> None:
        if not hasattr(args, "admin_subcmd") or not args.admin_subcmd:
            print("No admin command specified. Use --help for usage.")
            sys.exit(1)
        
        base_url = f"http://{args.host}:{args.port}/v1/admin"
        
        try:
            if args.admin_subcmd == "status":
                resp = httpx.get(f"{base_url}/health")
                resp.raise_for_status()
                print(resp.json())
            elif args.admin_subcmd == "models":
                resp = httpx.get(f"{base_url}/models")
                resp.raise_for_status()
                print(resp.json())
            elif args.admin_subcmd == "queue":
                resp = httpx.get(f"{base_url}/queue")
                resp.raise_for_status()
                print(resp.json())
            elif args.admin_subcmd == "drain":
                resp = httpx.post(f"{base_url}/drain")
                resp.raise_for_status()
                print(resp.json())
            elif args.admin_subcmd == "reload":
                resp = httpx.post(f"{base_url}/reload_model")
                resp.raise_for_status()
                print(resp.json())
        except httpx.HTTPError as e:
            print(f"HTTP error communicating with admin API: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Error communicating with admin API: {e}")
            sys.exit(1)

    def validate(self, args: argparse.Namespace) -> None:
        pass

    def subparser_init(
        self, subparsers: argparse._SubParsersAction
    ) -> FlexibleArgumentParser:
        admin_parser = subparsers.add_parser(
            self.name,
            help="Admin control plane CLI",
            description="CLI for vLLM Admin Control Plane",
        )
        admin_parser.add_argument("--host", default="localhost", help="Admin API host")
        admin_parser.add_argument("--port", type=int, default=8001, help="Admin API port")
        
        admin_subparsers = admin_parser.add_subparsers(dest="admin_subcmd", help="Admin commands")
        admin_subparsers.add_parser("status", help="Check health/status")
        admin_subparsers.add_parser("models", help="List loaded models")
        admin_subparsers.add_parser("queue", help="Get queue statistics")
        admin_subparsers.add_parser("drain", help="Drain the server (pause generation)")
        admin_subparsers.add_parser("reload", help="Reload the model (experimental)")
        
        return admin_parser

def cmd_init() -> list[CLISubcommand]:
    return [AdminSubcommand()]
