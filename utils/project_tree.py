import os

def generate_project_tree_grafic(root_path):
    tree = ""
    
    for dirpath, dirnames, filenames in os.walk(root_path):
        level = dirpath.replace(root_path, '').count(os.sep)
        indent = '│   ' * level
        tree += f"{indent}├── {os.path.basename(dirpath)}/\n"
        subindent = '│   ' * (level + 1)
        for f in filenames:
            tree += f"{subindent}├── {f}\n"
    return tree