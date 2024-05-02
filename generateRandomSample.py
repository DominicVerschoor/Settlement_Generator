import sys
import numpy as np
import random
import os
from gdpc import __url__, Editor, Block
from gdpc.exceptions import InterfaceConnectionError, BuildAreaNotSetError
from gdpc.vector_tools import addY, Box, loop3D
from glm import ivec2, ivec3
from nbt import nbt
from Fitness import Fitness
from nbt_reader import nbt_reader


class generateRandomSample:

    def __init__(self):
        """
        Initializes the class instance.
        """
        self.editor = Editor()

        self.reader = nbt_reader()
        self.fitness = Fitness()

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

    def create_building(self, building_data, x_pos, z_pos, build=False):
        """
        Pastes a building from a NBT file at the specified position.
        """
        height_map = self.worldSlice.heightmaps["MOTION_BLOCKING_NO_LEAVES"]

        # only take heigh of initial (0,0) of building and build off there
        height = height_map[tuple(ivec2(x_pos, z_pos) - self.buildRect.offset)]
        max_x, max_y, max_z = self.reader.get_data(building_data, "size")

        xw = x_pos + max_x.value - 1
        yh = height + max_y.value - 1
        zd = z_pos + max_z.value - 1

        # append building name and location and dimensions to list
        position = Box.between(ivec3(x_pos, height, z_pos), ivec3(xw, yh, zd))

        if build:
            self.reader.create(building_data, position)

        return [str(building_data), position]

    def perimeter_min_max(self):
        """
        Returns the minimum and maximum X and Z values of the build area perimeter.
        """
        xb, zb = self.buildRect.begin
        xe, ze = self.buildRect.end - (1, 1)

        return xb, xe, zb, ze

    def map_area(self, building, neighborhood=(1, 1, 1)):
        # - "WORLD_SURFACE":             The top non-air blocks.
        # - "MOTION_BLOCKING":           The top blocks with a hitbox or fluid.
        # - "MOTION_BLOCKING_NO_LEAVES": Like MOTION_BLOCKING, but ignoring leaves.
        # - "OCEAN_FLOOR":               The top non-air solid blocks.
        map = []
        max_x, max_y, max_z = self.reader.get_data(building[0], "size")

        start = building[1].begin
        max_pos = ivec3(start + tuple((max_x.value, max_y.value, max_z.value)))

        for loc in loop3D(start - neighborhood, max_pos + neighborhood):
            block = self.editor.getBlock(loc)
            if block.id != "minecraft:air":
                map.append((block, loc))

        return map

    def generate_building(self, params, build=False):
        x = np.array(params[0])
        z = np.array(params[1])
        building = params[2]

        build_max_x, _, build_max_z = self.reader.get_data(building, "size")
        build_max_x = build_max_x.value
        build_max_z = build_max_z.value
        _, per_max_x, _, per_max_z = self.perimeter_min_max()

        x = min(per_max_x - build_max_x, x)
        z = min(per_max_z - build_max_z, z)

        return self.create_building(building, x, z, build)

    def should_build(self, params, building_locations, prev_fitness):
        x = np.array(params[0])
        z = np.array(params[1])
        building_path = params[2]

        building = self.create_building(building_path, x, z, build=False)
        placed_locs = building_locations.copy()

        placed_locs.append(building)

        fitness = self.evaluate_fitness(placed_locs)

        return fitness < prev_fitness

    def evaluate_fitness(self, building_locations):
        current_building = building_locations[-1]
        placed_buildings = building_locations[:-1]
        map = self.map_area(current_building)

        self.fitness.set_params(current_building, placed_buildings, map)

        return self.fitness.total_fitness()


if __name__ == "__main__":
    sample = generateRandomSample()
    # sample.generate_buildings(dataset="BuildingDataSet", num_buildings=1)
    # green = -177,34
    sample.check_editor_connection()
    sample.initialize_slice()
    generated = []

    generated.append(
        sample.generate_building(
            params=[-177, 34, "nbtData\\basic\\birch.nbt"],
        )
    )

    generated.append(
        sample.generate_building(
            params=[-177, 30, "nbtData\\basic\\oak.nbt"],
        )
    )

    print(sample.evaluate_fitness(generated))
