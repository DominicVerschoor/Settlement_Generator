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


class Fitness:

    def __init__(self):
        """
        Initializes the class instance.
        """
        self.reader = nbt_reader()
        self.current_building = self.placed_building = self.map = []

    def set_params(self, current, placed, map):
        self.current_building = current
        self.placed_building = placed
        self.map = map

    def check_floating(self):
        counter = 0
        liquid_blocks = [
            "minecraft:water",
            "minecraft:lava",
            "minecraft:bubble",
        ]

        max_x, _, max_z = self.reader.get_data(self.current_building[0], "size")
        max_x = max_x.value
        max_z = max_z.value

        x_pos, y_pos, z_pos = self.current_building[1].begin

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

    def check_overlap(self):
        overlap_counter = 0
        max_x, max_y, max_z = self.reader.get_data(self.current_building[0], "size")

        x_pos = int(self.current_building[1][0]) + max_x.value - 1
        y_pos = int(self.current_building[1][1]) + max_y.value - 1
        z_pos = int(self.current_building[1][2]) + max_z.value - 1

        # Box.between(fromPoint, toPoint)
        current_box = Box.between(self.current_building[1], ivec3(x_pos, y_pos, z_pos))

        for building in self.building_locations:
            max_x, max_y, max_z = self.reader.get_data(building[0], "size")

            x_pos = int(building[1][0]) + max_x.value - 1
            y_pos = int(building[1][1]) + max_y.value - 1
            z_pos = int(building[1][2]) + max_z.value - 1

            compare_box = Box.between(building[1], ivec3(x_pos, y_pos, z_pos))

            if current_box.collides(compare_box):
                overlap_counter += 1

        return overlap_counter

    def check_diversity(self):
        current = []
        current.append(tuple(self.current_building))  # Convert list to tuple
        all_buildings = self.placed_building.copy() + current

        unique_buildings = set(map(tuple, all_buildings))  # Convert lists to tuples for uniqueness

        return len(unique_buildings)


    def break_terrain(self):
        # building = path2nbt, ivec of bot left
        counter = 0
        max_x, _, max_z = self.reader.get_data(self.current_building[0], "size")
        max_x = max_x.value
        max_z = max_z.value

        x_pos = int(self.current_building[1][0])
        y_pos = int(self.current_building[1][1])
        z_pos = int(self.current_building[1][2])

        for base in loop2D((x_pos, z_pos), (x_pos + max_x, z_pos + max_z)):
            base = addY(base, y_pos - 1)
            if base not in [pos[1] for pos in self.map]:
                counter += 1

        return counter

    def blocked_doors(self):
        counter = 0
        bot_door, top_door = self.reader.get_door_pos(self.current_building[0])

        if bot_door == None and top_door == None:
            return 0

        bot_door_front = bot_door[1] + self.current_building[1].begin
        top_door_front = top_door[1] + self.current_building[1].begin

        for _, block in self.map:
            if bot_door_front == block or top_door_front == block:
                counter += 1

        return counter

    def building_spacing(self):
        # TODO
        pass

    def building_placement_relations(self):
        # TODO
        pass

    def terraformed(self):
        # TODO
        pass

    def underground(self):
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
        # floating = self.check_floating()
        # blocked_door = self.blocked_doors()
        # overlap = self.check_overlap()

        fitness = -diversity + floating + overlap + blocked_door
        return fitness


if __name__ == "__main__":
    pass