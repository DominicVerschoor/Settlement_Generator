import sys
import numpy as np
import random
import os
from gdpc import __url__, Editor, Block
from gdpc.exceptions import InterfaceConnectionError, BuildAreaNotSetError
from gdpc.vector_tools import addY, Box, loop3D
from glm import ivec2, ivec3
from nbt import nbt
from ObjectiveFunction import ObjectiveFunction
from nbt_reader import nbt_reader


class generateRandomSample:

    def __init__(self):
        """
        Initializes the class instance.
        """
        self.editor = Editor()
        self.check_editor_connection()
        self.initialize_slice()

        self.reader = nbt_reader()
        self.obj_func = ObjectiveFunction()

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

        self.buildRect = self.buildArea.toRect()
        self.worldSlice = self.editor.loadWorldSlice(self.buildRect)

    def create_building(self, building_data, x_pos, z_pos, build=False):
        """
        Pastes a building from a NBT file at the specified position.
        """
        height_map = self.worldSlice.heightmaps["MOTION_BLOCKING_NO_LEAVES"]

        # only take heigh of initial (0,0) of building and build off there
        height = height_map[tuple(ivec2(x_pos, z_pos) - self.buildRect.offset)]
        max_x, max_y, max_z = self.reader.get_data(building_data, "size")
        x_pos, z_pos = self.set_in_bounds(x_pos, z_pos, building_data)

        xw = x_pos + max_x.value - 1
        yh = height + max_y.value - 1
        zd = z_pos + max_z.value - 1

        # append building name and location and dimensions to list
        position = Box.between(ivec3(x_pos, height, z_pos), ivec3(xw, yh, zd))

        if build:
            self.add_flooring(x_pos, xw, z_pos, zd, height-1)
            self.reader.create(building_data, ivec3(x_pos, height, z_pos))

        return str(building_data), position
    
    def set_in_bounds(self, x, z, building):
        #TODO redundant
        build_max_x, _, build_max_z = self.reader.get_data(building, "size")
        build_max_x = build_max_x.value
        build_max_z = build_max_z.value
        _, per_max_x, _, per_max_z = self.perimeter_min_max()

        x = min(per_max_x - build_max_x, x)
        z = min(per_max_z - build_max_z, z)

        return x, z

    def add_flooring(self, x0, x1, z0, z1, height):
        def inclusive_range(start, end):
            step = 1 if start <= end else -1
            return range(start, end + step, step)

        for x in inclusive_range(x0, x1):
            for z in inclusive_range(z0, z1):
                pos = ivec3(x, height, z)
                self.reader.create('nbtData\\floor\\flooring.nbt', pos)

    def perimeter_min_max(self):
        """
        Returns the minimum and maximum X and Z values of the build area perimeter.
        """
        xb, zb = self.buildRect.begin
        xe, ze = self.buildRect.end - (1, 1)

        return xb, xe, zb, ze

    def map_area(self):
        """
        Get a subset of the 2D array between the specified x and y value pairs.

        Parameters:
        - array: 2D numpy array
        - x0, x1: Start and end x coordinates
        - y0, y1: Start and end y coordinates

        Returns:
        - Subset of the array between the specified coordinates
        """
        height_map = self.worldSlice.heightmaps["MOTION_BLOCKING_NO_LEAVES"]
        water_map = np.where(
            self.worldSlice.heightmaps["MOTION_BLOCKING_NO_LEAVES"]
            > self.worldSlice.heightmaps["OCEAN_FLOOR"],
            1,
            0,
        )

        return height_map, water_map

    def should_build(self, current_building, building_locations, prev_fitness):
        if len(building_locations) == 0:
            return True

        fitness = self.evaluate_fitness(current_building, building_locations)

        return fitness <= prev_fitness

    def evaluate_fitness(self, current_building, placed_buildings):
        map, water_map = self.map_area()

        self.obj_func.set_params(current_building, placed_buildings, map, water_map, self.buildRect.begin[0], self.buildRect.begin[1])

        return self.obj_func.total_fitness()


if __name__ == "__main__":
    sample = generateRandomSample()
    # sample.generate_buildings(dataset="BuildingDataSet", num_buildings=1)
    # green = -177,34
    sample.check_editor_connection()
    sample.initialize_slice()

    sample.add_flooring(360, 364, 1036, 1032, 69)

    # generated = []

    # generated.append(
    #     sample.generate_building(
    #         params=[-177, 30, "nbtData\\basic\\birch.nbt"],
    #     )
    # )

    # generated.append(
    #     sample.generate_building(
    #         params=[-177, 37, "nbtData\\basic\\oak.nbt"],
    #     )
    # )

    # print(sample.evaluate_fitness(generated[0], [generated[1]]))
