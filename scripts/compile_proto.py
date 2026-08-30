"""Script to compile .proto files in proto/ to Python modules in src/agent/proto/."""

import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent


def compile_proto():
    proto_dir = ROOT_DIR / "proto"
    output_dir = ROOT_DIR / "src" / "agent" / "proto"
    output_dir.mkdir(parents=True, exist_ok=True)

    proto_files = list(proto_dir.glob("*.proto"))
    if not proto_files:
        print("No .proto files found in proto/")
        return

    for proto_file in proto_files:
        cmd = [
            sys.executable,
            "-m",
            "grpc_tools.protoc",
            f"-I{proto_dir}",
            f"--python_out={output_dir}",
            str(proto_file),
        ]
        print(f"Compiling {proto_file.name} -> {output_dir}")
        res = subprocess.run(cmd, check=False)
        if res.returncode != 0:
            print(f"Error compiling {proto_file.name}")
            sys.exit(res.returncode)


if __name__ == "__main__":
    compile_proto()
