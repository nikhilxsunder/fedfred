import os
import re
from ruamel.yaml import YAML

# Load the current meta.yaml
yaml = YAML()
feedstock_repo = os.getenv("FEEDSTOCK_REPO")
package_version = os.getenv("PACKAGE_VERSION")

# Clone the feedstock repository
os.system(f"git clone {feedstock_repo} feedstock")
meta_path = "feedstock/recipe/meta.yaml"

with open(meta_path, "r") as f:
    meta = yaml.load(f)

# Update the version and source URL
meta["package"]["version"] = package_version
meta["source"]["url"] = f"https://pypi.io/packages/source/f/fedfred/fedfred-{package_version}.tar.gz"

# Update the sha256 checksum
new_sha256 = os.popen(f"curl -sL {meta['source']['url']} | sha256sum").read().split()[0]
meta["source"]["sha256"] = new_sha256

# Save the updated meta.yaml
with open("updated_meta.yaml", "w") as f:
    yaml.dump(meta, f)
