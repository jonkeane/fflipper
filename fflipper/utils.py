import sys
from pathlib import Path

# So that resources work inside pyinstalled and dev
def fetch_resource(resource_path):
    try:  # running as *.exe; fetch resource from temp directory
        base_path = Path(sys._MEIPASS)
    except AttributeError:  # running as script; return one up
        return resource_path.resolve().parents[0]
    else:  # return temp resource path, two up
        return base_path.joinpath(resource_path.resolve().parents[1])