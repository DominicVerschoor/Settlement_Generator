"""
Load and use a world slice.
"""

import sys

import numpy as np

from gdpc import __url__, Editor, Block
from gdpc.exceptions import InterfaceConnectionError, BuildAreaNotSetError
from gdpc.vector_tools import addY
from glm import ivec2, ivec3
import csv

# Create an editor object.
# The Editor class provides a high-level interface to interact with the Minecraft world.
editor = Editor()


# Check if the editor can connect to the GDMC HTTP interface.
try:
    editor.checkConnection()
except InterfaceConnectionError:
    print(
        f"Error: Could not connect to the GDMC HTTP interface at {editor.host}!\n"
        'To use GDPC, you need to use a "backend" that provides the GDMC HTTP interface.\n'
        "For example, by running Minecraft with the GDMC HTTP mod installed.\n"
        f"See {__url__}/README.md for more information."
    )
    sys.exit(1)


# Get the build area.
try:
    buildArea = editor.getBuildArea()
except BuildAreaNotSetError:
    print(
        "Error: failed to get the build area!\n"
        "Make sure to set the build area with the /setbuildarea command in-game.\n"
        "For example: /setbuildarea ~0 0 ~0 ~64 200 ~64"
    )
    sys.exit(1)

print("Loading world slice...")
buildRect = buildArea.toRect()
worldSlice = editor.loadWorldSlice(buildRect)
print("World slice loaded!")

heightmap = worldSlice.heightmaps["MOTION_BLOCKING_NO_LEAVES"]

data = []

# Open the CSV file for reading
with open("block_data.csv", newline="") as file:
    reader = csv.DictReader(file)  # Assuming first row contains column headers
    for row in reader:
        # Convert X, Y, Z to integers
        x = int(row["X"])
        y = int(row["Y"])
        z = int(row["Z"])
        block = row["Block"]

        # Append the data as a tuple
        data.append((x, y, z, block))

for x, y, z, block in data:
    editor.placeBlock((x + buildRect.offset[0], y,
                        z + buildRect.offset[1]), Block(block))
