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

printA = []
# ivec2 (x, z)
bot_cor = tuple(buildRect.corners)[0]
top_cor = tuple(buildRect.corners)[3]

# Heightmap is the air block above the block so use -1 to get the exact block
highest = np.min(heightmap)

for x in range(bot_cor[0], top_cor[0]+1):
    for z in range(bot_cor[1], top_cor[1]+1):
        point = ivec2(x, z)
        # height = heightmap[tuple(point - buildRect.offset)]

        # not including 'height' so dont need to -1
        # -60 is floor level
        for y in range(-61, highest):
            current_block = editor.getBlock(tuple(addY(point, y)))
            if (str(current_block) != 'minecraft:air'):
                printA.append([x - buildRect.offset[0], y+61, 
                                z - buildRect.offset[1], current_block])


# Write data to CSV file
with open("BuildingDataSet/acacia.csv", mode="w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["X", "Y", "Z", "Block"])  # Write header
    for point_data in printA:
        writer.writerow(point_data)
