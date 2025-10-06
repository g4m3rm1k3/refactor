import os

# Define your project structure here
# Keys are folder names; values are either:
#   - dict: subfolders/files inside
#   - list: just files
#   - None: empty folder
structure = {
    "mastercam-pdm": {
        "backend": {
            "app": {
                "__init__.py": None,
                "main.py": None,
                "api": {
                    "__init__.py": None,
                    "dependencies.py": None,
                    "routers": {
                        "__init__.py": None,
                        "files.py": None,
                        "auth.py": None,
                    },
                },
                "core": {
                    "__init__.py": None,
                    "config.py": None,
                    "security.py": None,
                },
                "models": {
                    "__init__.py": None,
                    "schemas.py": None,
                },
                "services": {
                    "__init__.py": None,
                    "git_service.py": None,
                    "lock_service.py": None,
                },
            },
            "run.py": None,
            "requirements.txt": None,
        }
    }
}


def create_structure(base_path, structure):
    """Recursively create folders and files based on structure dict."""
    for name, content in structure.items():
        path = os.path.join(base_path, name)
        if isinstance(content, dict):
            # It's a folder
            os.makedirs(path, exist_ok=True)
            create_structure(path, content)
        elif content is None:
            # It's a file
            if not os.path.exists(path):
                open(path, "w").close()


if __name__ == "__main__":
    base_dir = os.getcwd()  # or change to desired root path
    create_structure(base_dir, structure)
    print("✅ Project structure created successfully.")
