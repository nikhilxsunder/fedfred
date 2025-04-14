import re
from pathlib import Path
import toml

def main():
    # Paths to conf.py and pyproject.toml
    conf_path = Path("docs/source/conf.py")
    pyproject_path = Path("pyproject.toml")

    # Read the version from pyproject.toml
    pyproject_data = toml.load(pyproject_path)
    version = pyproject_data["tool"]["poetry"]["version"]

    # Read the conf.py file
    conf_content = conf_path.read_text()

    # Update the release in conf.py
    updated_content = re.sub(
    r"(release\s*=\s*['\"])([\d\.]+)(['\"])",
    lambda match: f"{match.group(1)}{version}{match.group(3)}",
    conf_content
    )

    # Write the updated conf.py file
    conf_path.write_text(updated_content)

    print(f"Updated release in {conf_path} to version {version}")

if __name__ == "__main__":
    main()
