import numpy as np
from nbt_reader import nbt_reader
from gdpc import __url__, Block
from gdpc.exceptions import InterfaceConnectionError, BuildAreaNotSetError
from gdpc.vector_tools import (
    X,
    Y,
    Z,
    XZ,
    addY,
    dropY,
    loop2D,
    loop3D,
    perpendicular,
    toAxisVector2D,
    Box,
)
from glm import ivec2, ivec3
from generateRandomSample import generateRandomSample


class Fitness:

    def __init__(self, building_locations, map):
        """
        Initializes the class instance.
        """
        self.building_locations = building_locations
        self.reader = nbt_reader()
        self.map = map

    def check_floating(self, current_building):
        counter = 0
        liquid_blocks = [
            "minecraft:water",
            "minecraft:lava",
            "minecraft:bubble",
        ]

        max_x, _, max_z = self.reader.get_data(current_building[0], "size")
        max_x = max_x.value
        max_z = max_z.value

        x_pos = int(current_building[1][0])
        y_pos = int(current_building[1][1])
        z_pos = int(current_building[1][2])

        for base in loop2D((x_pos, z_pos), (x_pos + max_x, z_pos + max_z)):
            base = addY(base, y_pos - 1)
            for block, pos in self.map:
                if base == pos and any(
                    liquid_block in str(block) for liquid_block in liquid_blocks
                ):
                    counter += 1

            if base not in [pos[1] for pos in self.map]:
                counter += 1

        return counter

    def check_overlap(self, current_index, current_building):
        overlap_counter = 0
        max_x, max_y, max_z = self.reader.get_data(current_building[0], "size")

        x_pos = int(current_building[1][0]) + max_x.value - 1
        y_pos = int(current_building[1][1]) + max_y.value - 1
        z_pos = int(current_building[1][2]) + max_z.value - 1

        # Box.between(fromPoint, toPoint)
        current_box = Box.between(current_building[1], ivec3(x_pos, y_pos, z_pos))

        for index, building in enumerate(self.building_locations):
            if index > current_index:  # Skip checking against the current building
                max_x, max_y, max_z = self.reader.get_data(building[0], "size")

                x_pos = int(building[1][0]) + max_x.value - 1
                y_pos = int(building[1][1]) + max_y.value - 1
                z_pos = int(building[1][2]) + max_z.value - 1

                compare_box = Box.between(building[1], ivec3(x_pos, y_pos, z_pos))

                if current_box.collides(compare_box):
                    overlap_counter += 1

        return overlap_counter

    def check_diversity(self):
        unique_buildings = set(
            self.building_locations[0][: len(self.building_locations)]
        )
        return len(unique_buildings)

    def break_terrain(self, current_building):
        # building = path2nbt, ivec of bot left
        counter = 0
        max_x, _, max_z = self.reader.get_data(current_building[0], "size")
        max_x = max_x.value
        max_z = max_z.value

        x_pos = int(current_building[1][0])
        y_pos = int(current_building[1][1])
        z_pos = int(current_building[1][2])

        for base in loop2D((x_pos, z_pos), (x_pos + max_x, z_pos + max_z)):
            base = addY(base, y_pos - 1)
            if base not in [pos[1] for pos in self.map]:
                counter += 1

        return counter

    def blocked_doors(self, current_building):
        counter = 0
        bot_door, top_door = self.reader.get_door_pos(current_building[0])

        if bot_door == None and top_door == None:
            return 0

        bot_door_front = bot_door[1] + current_building[1]
        top_door_front = top_door[1] + current_building[1]

        for _, block in self.map:
            if bot_door_front == block or top_door_front == block:
                counter += 1

        return counter

    def building_spacing(self):
        # TODO
        pass

    def contains_farm(self):
        # TODO
        pass

    def building_placement_relations(self):
        # TODO
        pass

    def terraformed(self):
        # TODO
        pass

    def total_fitness(self):
        fitness = 0
        diversity = 0
        floating = 0
        overlap = 0
        blocked_door = 0

        # diversity = self.check_diversity()
        # building = path2nbt, ivec of bot left
        for index, building in enumerate(self.building_locations):
            # floating += self.check_floating(building)
            blocked_door += self.blocked_doors(building)
            # overlap += self.check_overlap(index, building)
        print(blocked_door)
        fitness = -diversity + floating + overlap + blocked_door
        return fitness


if __name__ == "__main__":
    sample = generateRandomSample()
    # sample.generate_buildings(dataset="BuildingDataSet", num_buildings=1)
    map = sample.map_to_array()
    sample.choose_generated_buildings(
        params=[2, -177, -177, 30, 34, "oak.nbt", "spruce.nbt"],
        dataset="basic",
        max_buildings=2
    )

    fit = Fitness(sample.building_locations, map)
    print(fit.total_fitness())
