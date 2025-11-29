import os


def fix_protobuf_imports():
    """
    Fixes the imports in the generated protobuf files to be absolute from the package root.
    """
    protobuf_dir = "cims/Protobuf"
    for root, _, files in os.walk(protobuf_dir):
        for file in files:
            if file.endswith("_pb2.py") or file.endswith("_pb2_grpc.py"):
                filepath = os.path.join(root, file)
                lines = []
                with open(filepath, "r") as f:
                    lines = f.readlines()

                new_lines = []
                for line in lines:
                    if line.startswith("from Protobuf"):
                        new_lines.append(
                            line.replace("from Protobuf", "from cims.Protobuf")
                        )
                    else:
                        new_lines.append(line)

                with open(filepath, "w") as f:
                    f.writelines(new_lines)


if __name__ == "__main__":
    fix_protobuf_imports()
