import re
from pathlib import Path
import toml

def main():
    # Paths to __about__.py and pyproject.toml
    about_path = Path("src/fedfred/__about__.py")
    pyproject_path = Path("pyproject.toml")

    # Read the version from pyproject.toml
    pyproject_data = toml.load(pyproject_path)
    version = pyproject_data["tool"]["poetry"]["version"]

    # Read the __about__.py file
    about_content = about_path.read_text()

    # Update the __version__ in __about__.py
    updated_content = re.sub(
        r'(__version__\s*=\s*[\'"])([\d\.]+)([\'"])',
        lambda match: f"{match.group(1)}{version}{match.group(3)}",
        about_content
    )

    # Write the updated __about__.py file
    about_path.write_text(updated_content)

    print(f"Updated __version__ in {about_path} to {version}")

if __name__ == "__main__":
    main()
