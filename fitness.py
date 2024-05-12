import itertools
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
    distance,
    Box,
)
from glm import ivec2, ivec3


class Fitness:

    def __init__(self):
        """
        Initializes the class instance.
        """
        self.reader = nbt_reader()
        self.current_building = self.placed_buildings = self.terrain_map = []

    def set_params(self, current, placed, map, water_map):
        self.current_building = current
        self.placed_buildings = placed
        self.terrain_map = map
        self.water_map = water_map

    # def check_floating(self):
    #     counter = 0
    #     liquid_blocks = [
    #         "minecraft:water",
    #         "minecraft:lava",
    #         "minecraft:bubble",
    #     ]

    #     max_x, _, max_z = self.current_building[1].end
    #     x_pos, y_pos, z_pos = self.current_building[1].begin

    #     for base in loop2D((x_pos, z_pos), (max_x, max_z)):
    #         base = addY(base, y_pos - 1)
    #         for block, pos in self.map:
    #             if base == pos and any(
    #                 liquid_block in str(block) for liquid_block in liquid_blocks
    #             ):
    #                 counter += 1

    #         if base not in [pos[1] for pos in self.map]:
    #             counter += 1

    #     return counter

    def check_floating(self):
        counter = 0
        building_height = self.terrain_map[0, 0]
        counter += np.sum(self.terrain_map < building_height)
        counter += np.sum(self.water_map == 1)

        return counter

    def check_overlap(self):
        for building in self.placed_buildings:
            if self.current_building[1].collides(building[1]):
                return 100

        return 0

    def check_diversity(self):
        current = []
        current.append(tuple(self.current_building))  # Convert list to tuple
        all_buildings = self.placed_buildings.copy() + current

        unique_buildings = set(
            map(tuple, all_buildings)
        )  # Convert lists to tuples for uniqueness

        return -1 * len(unique_buildings)

    def total_buildings(self):
        return -1 * (len(self.placed_buildings) + 1)

    # def break_terrain(self):
    #     # building = path2nbt, ivec of bot left
    #     counter = 0

    #     x_pos, y_pos, z_pos = self.current_building[1].begin
    #     x_end, y_end, z_end = self.current_building[1].end

    #     for pos in loop3D(ivec3(x_pos, y_pos, z_pos), ivec3(x_end, y_end, z_end)):
    #         if pos in [map_loc[1] for map_loc in self.terrain_map]:
    #             counter += 1

    #     return counter
    
    def break_terrain(self):
        # building = path2nbt, ivec of bot left
        counter = 0
        building_height = self.terrain_map[0, 0]
        counter += np.sum(self.terrain_map > building_height)
        
        return counter

    def blocked_doors(self):
        counter = 0
        bot_door, top_door = self.reader.get_door_pos(self.current_building[0])

        if bot_door == None and top_door == None:
            return 0

        bot_door_front = bot_door[1] + self.current_building[1].begin
        top_door_front = top_door[1] + self.current_building[1].begin

        for _, block in self.terrain_map:
            if bot_door_front == block or top_door_front == block:
                counter += 10

        return counter
    
    def on_cliff(self):
        pass

    def building_spacing(self):
        counter = 0
        max_x, _, max_z = self.current_building[1].end
        x_pos, _, z_pos = self.current_building[1].begin

        original_min = ivec2(x_pos, z_pos)
        original_max = ivec2(max_x, max_z)

        for building in self.placed_buildings:
            max_x2, _, max_z2 = building[1].end
            x_pos2, _, z_pos2 = building[1].begin

            alt_min = ivec2(x_pos2, z_pos2)
            alt_max = ivec2(max_x2, max_z2)

            min_min_dist = distance(original_min, alt_min)
            min_max_dist = distance(original_min, alt_max)
            max_min_dist = distance(original_max, alt_min)
            max_max_dist = distance(original_max, alt_max)

            smallest_dist = np.min(
                [min_min_dist, min_max_dist, max_min_dist, max_max_dist]
            )

            # TODO: decide on distances
            # too close or too far
            if smallest_dist < 7 and smallest_dist > 30:
                counter += 1

        return counter

    def building_placement_relations(self):
        # TODO
        pass

    # def underground(self):
    #     counter = 0

    #     max_x, max_y, max_z = self.current_building[1].end
    #     x_pos, _, z_pos = self.current_building[1].begin

    #     for roof in loop2D((x_pos, z_pos), (max_x, max_z)):
    #         roof = addY(roof, max_y - 1)
    #         if roof not in [pos[1] for pos in self.terrain_map]:
    #             counter += 1

    #     return counter
    
    def underground(self):
        counter = 0
        building_height = self.terrain_map[0, 0]
        _, max_y, _ = self.current_building[1].end

        height = building_height + max_y
        
        counter += np.sum(self.terrain_map > height)

        return counter

    def total_fitness(self):
        functionality = 0
        aesthetics = 0
        adaptability = 0

        # functionality = (
        #     self.blocked_doors() + self.check_overlap() + self.total_buildings()
        # )
        # adaptability = (
        #     self.break_terrain()
        #     + self.check_overlap()
        #     + self.check_floating()
        #     + self.underground()
        #     + self.total_buildings()
        # )
        # aesthetics = (
        #     self.building_spacing()
        #     + self.check_diversity()
        #     + self.check_overlap()
        #     + self.total_buildings()
        # )

        # return (
        #     ((1 / 3.0) * functionality)
        #     + ((1 / 3.0) * adaptability)
        #     + ((1 / 3.0) * aesthetics)
        # )
        return self.total_buildings()


if __name__ == "__main__":
    pass
