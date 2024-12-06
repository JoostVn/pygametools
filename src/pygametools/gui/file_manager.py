import json
from importlib.resources import files


def load_theme(theme_name):
    """
    Loads a JSON theme and return as dict.

    Parameters
    ----------
    theme_name : string
        Theme name, corresponding to a theme in the "themes" module.

    Returns
    -------
    theme : dict
        The theme dictionary
    """
    theme_path = files("pygametools.gui.themes").joinpath(f"{theme_name}.json")

    with theme_path.open() as file:
        theme = json.load(file)
    return theme


def save_theme(theme_dict, theme_path):
    """
    Saves a JSON theme to the given themes folder with a given filename.

    Parameters
    ----------
    theme_dict : dict
        The theme dictionary.
    theme_name : string
        The thame filename without path or file extension.

    """
    # Make sure file ends in one .json extension
    split_path = theme_path.split('.')
    if split_path[-2] == 'json':
        theme_path = '.'.join(split_path[:-1])
    elif split_path[-1] != 'json':
        theme_path += 'json'

    # Save JSON file
    with open(theme_path, "w") as file:
        json.dump(theme_dict, file, indent=4)


