import sys
import numpy as np
import csv
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

    def paste_building_from_csv(self, building_name, x_pos, z_pos, build):
        """
        Pastes a building from a CSV file at the specified position.
        """
        heightmap = self.worldSlice.heightmaps["MOTION_BLOCKING"]
        data = []

        # Open the CSV file for reading
        csv_path = os.path.join("BuildingDataSet", building_name)
        with open(csv_path, newline="") as file:
            reader = csv.DictReader(file)  # Assuming first row contains column headers
            for row in reader:
                # Convert X, Y, Z to integers
                x = int(row["X"])
                y = int(row["Y"])
                z = int(row["Z"])
                block = row["Block"]

                # Append the data as a tuple
                data.append((x, y, z, block))

        # only take heigh of initial (0,0) of building and build off there
        height = heightmap[tuple(ivec2(x_pos, z_pos) - self.buildRect.offset)]

        # append building name and location and dimensions to list
        build_max_x, build_max_y, build_max_z = self.get_building_size(building_name)
        self.building_locations.append(
            (
                building_name,
                int(x_pos),
                int(height),
                int(z_pos),
                int(build_max_x),
                int(build_max_y),
                int(build_max_z),
            )
        )

        if build:
            for x, y, z, block in data:
                point = ivec2(x + x_pos, z + z_pos)
                self.editor.placeBlock(addY(point, height + y), Block(block))

    def get_building_size(self, building_name):
        """
        Returns the minimum and maximum X and Z values of a building from a CSV file.
        """
        # Load X and Z values from the CSV file into NumPy arrays
        csv_path = os.path.join("BuildingDataSet", building_name)
        with open(csv_path, newline="") as file:
            reader = csv.DictReader(file)  # Assuming first row contains column headers

            # Read all values into memory
            data = list(reader)

            # Reset the file pointer to the beginning of the file
            file.seek(0)
            X_values = np.array([float(row["X"]) for row in data])
            Y_values = np.array([float(row["Y"]) for row in data])
            Z_values = np.array([float(row["Z"]) for row in data])

        # Find the maximum X and Z values
        max_X_value = np.max(X_values)
        max_Y_value = np.max(Y_values)
        max_Z_value = np.max(Z_values)

        return max_X_value, max_Y_value, max_Z_value

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

    def generate_buildings(self, dataset, num_buildings=5):
        """
        Generates buildings randomly within the build area perimeter.
        """

        # Create Perimeter
        for point in self.buildRect.outline:
            self.editor.placeBlock(addY(point, -61), Block("red_concrete"))

        buildings = [file for file in os.listdir(dataset) if file.endswith(".csv")]

        for i in range(num_buildings):
            random_building = random.choice(buildings)

            build_max_x, _, build_max_z = self.get_building_size(random_building)
            per_min_x, per_max_x, per_min_z, per_max_z = self.perimeter_min_max()

            rand_x = random.randint(per_min_x, per_max_x - build_max_x)
            rand_z = random.randint(per_min_z, per_max_z - build_max_z)

            self.paste_building_from_csv(random_building, rand_x, rand_z, build=False)

    def clear_area(self):
        for building in self.building_locations:
            _, x_pos, y_pos, z_pos, max_x, max_y, max_z = building

            for x in range(x_pos, x_pos + max_x + 1):
                for y in range(y_pos, y_pos + max_y + 1):
                    for z in range(z_pos, z_pos + max_z + 1):
                        self.editor.placeBlock(ivec3(x, y, z), Block("minecraft:air"))

        self.building_locations = []

    def map_to_array(self):
        map = []
        heightmap = self.worldSlice.heightmaps["MOTION_BLOCKING"]
        per_min_x, per_max_x, per_min_z, per_max_z = self.perimeter_min_max()

        for x in range(per_min_x, per_max_x + 1):
            for z in range(per_min_z, per_max_z + 1):
                pt2 = ivec2(x, z)
                y = heightmap[tuple(pt2 - self.buildRect.offset)] - 1
                block = self.editor.getBlock(addY(pt2, y))
                map.append(
                    (
                        block,
                        int(x),
                        int(y),
                        int(z),
                    )
                )

        return map

    def choose_generated_buildings(self, params, max_buildings, build=False):
        num_buildings = int(params[0])
        x = np.array(params[1 : 1 + num_buildings])
        z = np.array(params[1 + max_buildings : 1 + 2 * max_buildings])[:num_buildings]
        buildings = params[1 + 2 * max_buildings :]

        for i in range(num_buildings):
            cur_build = buildings[i]
            pt_x = x[i]
            pt_z = z[i]

            build_max_x, _, build_max_z = self.get_building_size(cur_build)
            _, per_max_x, _, per_max_z = self.perimeter_min_max()

            if pt_x + build_max_x > per_max_x:
                pt_x = per_max_x - build_max_x
            if pt_z + build_max_z > per_max_z:
                pt_z = per_max_z - build_max_z

            self.paste_building_from_csv(cur_build, pt_x, pt_z, build)


if __name__ == "__main__":
    test = generateRandomSample()
    # test.map_to_array()
    test.clear_area()
    # test.choose_generated_buildings([1, -190, 180, 107, 97, 'acacia.csv', 'birch.csv'], 2, build=True)
    # test.generate_buildings(dataset="BuildingDataSet", num_buildings=30)
