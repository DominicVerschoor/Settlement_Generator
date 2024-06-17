import sys
import numpy as np
from gdpc import __url__, Editor
from gdpc.exceptions import InterfaceConnectionError, BuildAreaNotSetError
from gdpc.vector_tools import Box
from glm import ivec2, ivec3
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
        self.per_min_x, self.per_max_x, self.per_min_z, self.per_max_z = (
            self.perimeter_min_max()
        )
        self.terrain_map, self.water_map = self.map_area()

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
        Packages building information.

        Parameters:
        - building_data: file path to the nbt file
        - x_pos: x position of the building
        - z_pos: z position of the building
        - build: if True the building will be placed in game
        """
        # only take heigh of initial (0,0) of building and build off there
        height = self.terrain_map[tuple(ivec2(x_pos, z_pos) - self.buildRect.offset)]
        max_x, max_y, max_z = self.reader.get_data(building_data, "size")

        x_pos = min(self.per_max_x - max_x.value, x_pos)
        z_pos = min(self.per_max_z - max_z.value, z_pos)

        xw = x_pos + max_x.value - 1
        yh = height + max_y.value - 1
        zd = z_pos + max_z.value - 1

        # append building name and location and dimensions to list
        position = Box.between(ivec3(x_pos, height, z_pos), ivec3(xw, yh, zd))

        if build:
            # self.add_flooring(x_pos, xw, z_pos, zd, height-1)
            self.reader.create(building_data, ivec3(x_pos, height, z_pos))

        return str(building_data), position

    def add_flooring(self, x0, x1, z0, z1, height):
        '''
        Creates a basic flooring.

        Parameters:
        - x0: Starting x coordinate for flooring
        - x1: Ending x coordinate for flooring
        - z0: Starting z coordinate for flooring
        - z1: Ending z coordinate for flooring
        - height: The y coordinate for flooring
        '''

        def inclusive_range(start, end):
            step = 1 if start <= end else -1
            return range(start, end + step, step)

        for x in inclusive_range(x0, x1):
            for z in inclusive_range(z0, z1):
                pos = ivec3(x, height, z)
                self.reader.create("nbtData\\floor\\flooring.nbt", pos)

    def perimeter_min_max(self):
        """
        Returns the minimum and maximum X and Z values of the build area perimeter.
        """
        xb, zb = self.buildRect.begin
        xe, ze = self.buildRect.end - (1, 1)

        return xb, xe, zb, ze

    def map_area(self):
        """
        Get a 2D arrays of maps on the build area.

        Returns:
        - 2D array height map of the entire build area
        - 2D array water map detailing which blocks are water or not
        """
        height_map = self.worldSlice.heightmaps["MOTION_BLOCKING_NO_LEAVES"]
        water_map = np.where(
            self.worldSlice.heightmaps["MOTION_BLOCKING_NO_LEAVES"]
            > self.worldSlice.heightmaps["OCEAN_FLOOR"],
            1,
            0,
        )

        return height_map, water_map

    def evaluate_obj(self, current_building, placed_buildings):
        """
        Evaluates the current building based its location and already placed buildings.

        Parameters:
        - current_building: The current building being evaluated
        - placed_buildings: A list of buildings already placed

        Returns:
        - The total score of the building 
        """

        self.obj_func.set_params(
            current_building,
            placed_buildings,
            self.terrain_map,
            self.water_map,
            self.buildRect.begin[0],
            self.buildRect.begin[1],
        )

        return self.obj_func.total_fitness()


if __name__ == "__main__":
    sample = generateRandomSample()
    sample.check_editor_connection()
    sample.initialize_slice()

    # sample.add_flooring(360, 364, 1036, 1032, 69)

    generated = []

    generated.append(
        sample.create_building(
            "nbtData\\normal\\food\carrot_field.nbt", 665, 533, build=False
        )
    )

    # generated.append(
    #     sample.create_building(
    #         "nbtData\\normal\\food\\barn.nbt", 452, 1355, build=False
    #     )
    # )

    # print(sample.get_individual_score('nbtData\\normal\\food\carrot_field.nbt', 433, 1339))
    print(sample.evaluate_obj(generated[0], []))
