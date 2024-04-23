import sys
import numpy as np
import os
import time
from gdpc import __url__, Block
from gdpc.exceptions import InterfaceConnectionError, BuildAreaNotSetError
from gdpc.vector_tools import addY
from glm import ivec2, ivec3
from generateRandomSample import generateRandomSample
from nbtlib import nbt


class Fitness:

    def __init__(self, building_locations, map):
        """
        Initializes the class instance.
        """
        self.building_locations = building_locations
        self.map = map

    def check_floating(self, current_building):
        _, x_pos, y_pos, z_pos, max_x, _, max_z = current_building
        x_values, y_values, z_values = zip(*[(x, y, z) for _, x, y, z in self.map])
        map_coords = list(zip(x_values, y_values, z_values))

        for x in range(x_pos, x_pos + max_x + 1):
            for z in range(z_pos, z_pos + max_z + 1):
                if (x, y_pos - 1, z) not in map_coords:
                    return 1

        return 0

    def check_overlap(self, current_index, current_building):
        # returns +1 for each overlapping building
        # returns number of overlapping blocks (*2 for each block because both are touching each other)
        overlap_counter = 0
        _, x_pos, y_pos, z_pos, max_x, max_y, max_z = current_building

        for index, building in enumerate(self.building_locations):
            if index != current_index:  # Skip checking against the current building
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

                #### ALTERNATIVE ONLY CHECK OVERLAP REGION###
                # Determine the overlapping region
                # overlap_x_min = max(x_pos, building_x)
                # overlap_x_max = min(x_pos + max_x, building_max_x)
                # overlap_y_min = max(y_pos, building_y)
                # overlap_y_max = min(y_pos + max_y, building_max_y)
                # overlap_z_min = max(z_pos, building_z)
                # overlap_z_max = min(z_pos + max_z, building_max_z)

                # # Check for overlap in the overlapping region
                # for x in range(overlap_x_min, overlap_x_max + 1):
                #     for y in range(overlap_y_min, overlap_y_max + 1):
                #         for z in range(overlap_z_min, overlap_z_max + 1):
                #             overlap_counter += 1

                # Check for overlap
                if (
                    x_pos <= building_max_x
                    and x_pos + max_x >= building_x
                    and y_pos <= building_max_y
                    and y_pos + max_y >= building_y
                    and z_pos <= building_max_z
                    and z_pos + max_z >= building_z
                ):
                    overlap_counter += 1
        return overlap_counter

    def check_diversity(self, building_name):
        # each type of building count ^2 because of the loop
        return sum(1 for item in self.building_locations if item[0] == building_name)

    def check_liquid_obstruction(self, current_building):
        liquid_blocks = [
            "minecraft:water",
            "minecraft:lava",
            "minecraft:bubble",
        ]
        _, x_pos, y_pos, z_pos, max_x, max_y, max_z = current_building
        x_values = []
        y_values = []
        z_values = []

        for name, x, y, z in self.map:
            if any(liquid_block in str(name) for liquid_block in liquid_blocks):
                x_values.append(x)
                y_values.append(y)
                z_values.append(z)

        map_coords = list(zip(x_values, y_values, z_values))

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

                        # # Check the surrounding blocks
                        adjacent_blocks = [
                            (x, y, z),
                            (x, y + 1, z),
                            (x, y - 1, z),
                            (x, y, z - 1),
                            (x, y, z + 1),
                            (x - 1, y, z),
                            (x + 1, y, z),
                        ]

                        for current_block in adjacent_blocks:
                            if current_block in map_coords:
                                return 1

        return 0

    def total_fitness(self):
        fitness, diversity, floating, liquid, overlap = (0, 0, 0, 0, 0)
        for index, building in enumerate(self.building_locations):
            diversity += self.check_diversity(building[0])
            floating += self.check_floating(building)
            liquid += self.check_liquid_obstruction(building)
            overlap += self.check_overlap(index, building)
        fitness = -diversity + floating + liquid + overlap
        return fitness


if __name__ == "__main__":
    sample = generateRandomSample()
    # sample.generate_buildings(dataset="BuildingDataSet", num_buildings=1)
    map = sample.map_to_array()
    sample.choose_generated_buildings(
        [2, 56, 56, -205, -205, "spruce.csv", "spruce.csv"], 2
    )

    fit = Fitness(sample.building_locations, map)
    print(fit.total_fitness())
