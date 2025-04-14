import tomli
import re
from pathlib import Path

def sync_conda_version():
    # Paths to the files
    pyproject_path = Path("pyproject.toml")
    meta_yaml_path = Path("conda-recipe/meta.yaml")

    # Read the version from pyproject.toml
    with pyproject_path.open("rb") as f:
        pyproject_data = tomli.load(f)
        version = pyproject_data["tool"]["poetry"]["version"]

    # Read and update the meta.yaml file
    meta_yaml_content = meta_yaml_path.read_text()
    updated_content = re.sub(
        r"(?<=version: )\d+\.\d+\.\d+",
        version,
        meta_yaml_content
    )

    # Write the updated content back to meta.yaml
    meta_yaml_path.write_text(updated_content)
    print(f"Updated version in {meta_yaml_path} to {version}")

if __name__ == "__main__":
    sync_conda_version()
