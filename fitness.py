import sys
import numpy as np
import os
from gdpc import __url__, Editor, Block
from gdpc.exceptions import InterfaceConnectionError, BuildAreaNotSetError
from gdpc.vector_tools import addY
from glm import ivec2, ivec3
from generateRandomSample import generateRandomSample


class fitness:

    def __init__(self):
        """
        Initializes the class instance.
        """
        self.editor = Editor()
        self.check_editor_connection()
        self.initialize_slice()
        self.building_locations = generateRandomSample().get_building_locations()

    def check_editor_connection(self):
        """
        Checks the connection to the GDMC HTTP interface.
        """
        try:
            self.editor.checkConnection()
        except InterfaceConnectionError:
            print(
                f"Error: Could not connect to the GDMC HTTP interface at {self.editor.host}!\n"
                'To use GDPC, you need to use a "backend" that provides the GDMC HTTP interface.\n'
                "For example, by running Minecraft with the GDMC HTTP mod installed.\n"
                f"See {__url__}/README.md for more information."
            )
            sys.exit(1)

    def initialize_slice(self):
        """
        Initializes the world slice.
        """
        try:
            self.buildArea = self.editor.getBuildArea()
        except BuildAreaNotSetError:
            print(
                "Error: failed to get the build area!\n"
                "Make sure to set the build area with the /setbuildarea command in-game.\n"
                "For example: /setbuildarea ~0 0 ~0 ~64 200 ~64"
            )
            sys.exit(1)

        print("Loading world slice...")
        self.buildRect = self.buildArea.toRect()
        self.worldSlice = self.editor.loadWorldSlice(self.buildRect)
        print("World slice loaded!")

    def check_floating(self, current_building):
        float_counter = 0
        non_solid_blocks = [
            "minecraft:air",
            "minecraft:amethyst_bud",
        ]
        _, x_pos, y_pos, z_pos, max_x, _, max_z = current_building

        for x in range(x_pos, max_x + 1):
            for z in range(z_pos, max_z + 1):
                below_block = self.editor.getBlock((x, y_pos - 1, z))

                if str(below_block) in non_solid_blocks:
                    float_counter += 1

        return float_counter

    def check_overlap(self, current_building):
        overlap_counter = 0
        _, x_pos, y_pos, z_pos, max_x, max_y, max_z = current_building

        for x in range(x_pos, max_x + 1):
            for y in range(y_pos, max_y + 1):
                for z in range(z_pos, max_z + 1):
                    # Check if the point (x, y, z) is contained within the dataset
                    if any(
                        building[1] == x and building[2] == y and building[3] == z
                        for building in self.building_locations
                    ):
                        overlap_counter += 1

        return overlap_counter

    def check_diversity(self, building_name):
        return sum(1 for item in self.building_locations if item[0] == building_name)

    def check_liquid_obstruction(self, current_building):
        liquid_counter = 0
        liquid_blocks = [
            "minecraft:water",
            "minecraft:lava",
            "minecraft:bubble",
        ]
        _, x_pos, y_pos, z_pos, max_x, max_y, max_z = current_building

        for x in range(x_pos, max_x + 1):
            for y in range(y_pos, max_y + 1):
                for z in range(z_pos, max_z + 1):
                    # Check if the current point is on the perimeter
                    if (
                        x == x_pos
                        or x == max_x
                        or y == y_pos
                        or y == max_y
                        or z == z_pos
                        or z == max_z
                    ):

                        # Check the location above
                        adjacent_blocks = [
                            self.editor.getBlock((x, y + 1, z)),
                            self.editor.getBlock((x, y - 1, z)),
                            self.editor.getBlock((x, y, z - 1)),
                            self.editor.getBlock((x, y, z + 1)),
                            self.editor.getBlock((x - 1, y, z)),
                            self.editor.getBlock((x + 1, y, z)),
                        ]

                        if any(
                            str(block) in liquid_blocks for block in adjacent_blocks
                        ):
                            liquid_counter += 1

        return liquid_counter


if __name__ == "__main__":
    test = fitness()
