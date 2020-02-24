import importlib

def set_current_project(project_name):

    global current_project
    global current_project_name

    current_project = importlib.import_module('..{}'.format(project_name), 'config_files.subpkg')
    current_project_name = project_name

    return current_project, current_project_name