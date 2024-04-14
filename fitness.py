import sys
import numpy as np
import os
from gdpc import __url__, Editor, Block
from gdpc.exceptions import InterfaceConnectionError, BuildAreaNotSetError
from gdpc.vector_tools import addY
from glm import ivec2, ivec3
from generateRandomSample import generateRandomSample


class fitness:

    def __init__(self, building_locations):
        """
        Initializes the class instance.
        """
        self.editor = Editor()
        self.check_editor_connection()
        self.initialize_slice()
        self.building_locations = building_locations

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
        # returns number of overlapping blocks (*2 for each block because both are touching each other)
        overlap_counter = 0
        _, x_pos, y_pos, z_pos, max_x, max_y, max_z = current_building

        for building in self.building_locations:
            if (
                building != current_building
            ):  # Skip checking against the current building
                building_x, building_y, building_z = (
                    building[1],
                    building[2],
                    building[3],
                )
                building_max_x, building_max_y, building_max_z = (
                    building_x + building[4],
                    building_y + building[5],
                    building_z + building[6],
                )

                for x in range(building_x, building_max_x + 1):
                    for y in range(building_y, building_max_y + 1):
                        for z in range(building_z, building_max_z + 1):
                            if (
                                x_pos <= x <= x_pos + max_x
                                and y_pos <= y <= y_pos + max_y
                                and z_pos <= z <= z_pos + max_z
                            ):
                                overlap_counter += 1

        return overlap_counter

    def check_diversity(self, building_name):
        # each type of building count ^2 because of the loop
        return sum(1 for item in self.building_locations if item[0] == building_name)

    def check_liquid_obstruction(self, current_building):
        liquid_counter = 0
        liquid_blocks = [
            "minecraft:water",
            "minecraft:lava",
            "minecraft:bubble",
        ]
        _, x_pos, y_pos, z_pos, max_x, max_y, max_z = current_building

        for x in range(x_pos, x_pos + max_x + 1):
            for y in range(y_pos, y_pos + max_y + 1):
                for z in range(z_pos, z_pos + max_z + 1):
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

    def total_fitness(self):
        fitness, diversity, floating, liquid, overlap = (0, 0, 0, 0, 0)
        for building in self.building_locations:
            diversity += self.check_diversity(building[0])
            floating += self.check_floating(building)
            liquid += self.check_liquid_obstruction(building)
            overlap += self.check_overlap(building)
        fitness = diversity + floating + liquid + overlap
        return fitness, diversity, floating, liquid, overlap


if __name__ == "__main__":
    sample = generateRandomSample()
    sample.generate_buildings(dataset="BuildingDataSet", num_building=5)

    b_loc = sample.get_building_locations()

    fit = fitness(b_loc)
    print(fit.total_fitness())
