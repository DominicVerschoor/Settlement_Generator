import sys
import numpy as np
import random
import os
from gdpc import __url__, Editor, Block
from gdpc.exceptions import InterfaceConnectionError, BuildAreaNotSetError
from gdpc.vector_tools import addY
from glm import ivec2, ivec3
from nbt import nbt
from nbt_reader import nbt_reader


class generateRandomSample:

    def __init__(self):
        """
        Initializes the class instance.
        """
        self.editor = Editor()
        self.reader = nbt_reader()
        self.check_editor_connection()
        self.initialize_slice()
        self.building_locations = []

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

    def paste_building_from_csv(self, building_data, x_pos, z_pos, build):
        """
        Pastes a building from a CSV file at the specified position.
        """
        height_map = self.worldSlice.heightmaps["MOTION_BLOCKING_NO_LEAVES"]

        # only take heigh of initial (0,0) of building and build off there
        height = height_map[tuple(ivec2(x_pos, z_pos) - self.buildRect.offset)]

        # append building name and location and dimensions to list
        position = ivec3(x_pos, height, z_pos)
        self.building_locations.append((str(building_data), position))

        if build:
            self.reader.create(building_data, position)

    # def perimeter_min_max(self):
    #     """
    #     Returns the minimum and maximum X and Z values of the build area perimeter.
    #     """
    #     x_min, z_min = self.buildRect.begin
    #     x_max, z_max = self.buildRect.end

    #     return x_min, x_max, z_min, z_max
    
    def perimeter_min_max(self):
        """
        Returns the minimum and maximum X and Z values of the build area perimeter.
        """
        outline = tuple(self.buildRect.outline)

        # Extract all x and z values separately
        x_values = [point[0] for point in outline]
        z_values = [point[1] for point in outline]

        # Find the minimum x and z values
        x_min = np.min(x_values)
        z_min = np.min(z_values)

        # Find the maximum x and z values
        x_max = np.max(x_values)
        z_max = np.max(z_values)

        return x_min, x_max, z_min, z_max

    def map_to_array(self):
        map = []
        # - "WORLD_SURFACE":             The top non-air blocks.
        # - "MOTION_BLOCKING":           The top blocks with a hitbox or fluid.
        # - "MOTION_BLOCKING_NO_LEAVES": Like MOTION_BLOCKING, but ignoring leaves.
        # - "OCEAN_FLOOR":               The top non-air solid blocks.
        heightmap = self.worldSlice.heightmaps["MOTION_BLOCKING"]
        per_min_x, per_max_x, per_min_z, per_max_z = self.perimeter_min_max()

        for x in range(per_min_x, per_max_x + 1):
            for z in range(per_min_z, per_max_z + 1):
                pt2 = ivec2(x, z)
                y = heightmap[tuple(pt2 - self.buildRect.offset)] - 1
                block = self.editor.getBlock(addY(pt2, y))
                map.append((block, ivec3(x, y, z)))

        return map

    def choose_generated_buildings(self, params, dataset, max_buildings, build=False):
        num_buildings = int(params[0])
        x = np.array(params[1 : 1 + num_buildings])
        z = np.array(params[1 + max_buildings : 1 + 2 * max_buildings])[:num_buildings]
        buildings = params[1 + 2 * max_buildings :]

        for i in range(num_buildings):
            current_building = os.path.join("nbtData", dataset, buildings[i])
            pt_x = x[i]
            pt_z = z[i]

            
            build_max_x, _, build_max_z = self.reader.get_data(current_building, "size")
            build_max_x = build_max_x.value
            build_max_z = build_max_z.value
            _, per_max_x, _, per_max_z = self.perimeter_min_max()

            if pt_x + build_max_x > per_max_x:
                pt_x = per_max_x - build_max_x
            if pt_z + build_max_z > per_max_z:
                pt_z = per_max_z - build_max_z

            self.paste_building_from_csv(current_building, pt_x, pt_z, build)


if __name__ == "__main__":
    test = generateRandomSample()
    print(test.perimeter_min_max())
