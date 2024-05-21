import numpy as np
from nbt_reader import nbt_reader
from gdpc.vector_tools import distance
from glm import ivec2


class Fitness:

    def __init__(self):
        """
        Initializes the class instance.
        """
        self.reader = nbt_reader()
        self.current_building = self.placed_buildings = self.terrain_map = (
            self.water_map
        ) = []

    def set_params(self, current, placed, map, water_map, offset_x, offset_z):
        self.offx = offset_x
        self.offz = offset_z
        self.current_building = current
        self.placed_buildings = placed
        self.terrain_map = map
        self.water_map = water_map
        self.mini_terrain, self.mini_water = self.sub_map()

    def check_floating(self):
        counter = 0
        building_height = self.mini_terrain[0, 0]
        counter -= np.sum(self.mini_terrain < building_height)
        counter -= np.sum(self.mini_water == 1)

        return counter

    def check_overlap(self):
        for building in self.placed_buildings:
            if self.current_building[1].collides(building[1]):
                return -100

        return 0

    def check_diversity(self):
        current = []
        current.append(tuple(self.current_building))  # Convert list to tuple
        all_buildings = self.placed_buildings.copy() + current

        unique_buildings = set(
            map(tuple, all_buildings)
        )  # Convert lists to tuples for uniqueness

        return len(unique_buildings)

    def total_buildings(self):
        return len(self.placed_buildings) + 1

    def break_terrain(self):
        # building = path2nbt, ivec of bot left
        counter = 0
        building_height = self.mini_terrain[0, 0]
        counter -= np.sum(self.mini_terrain > building_height)

        return counter

    def blocked_doors(self):
        door_height = self.cord2map(
            self.current_building[1].begin[0], self.current_building[1].begin[2]
        )
        door_height = self.terrain_map[door_height[0]][door_height[1]]
        bot_door, _ = self.reader.get_door_pos(self.current_building[0])

        if bot_door == None:
            return 0

        bot_door_front = bot_door[1] + self.current_building[1].begin

        bot_door_front = self.cord2map(bot_door_front[0], bot_door_front[2])
        bot_door_front_height = self.terrain_map[bot_door_front[0]][bot_door_front[1]]

        if bot_door_front_height > door_height:
            return -10
        elif bot_door_front_height < door_height:
            return -5

        return 0

    def building_spacing(self):
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
            if smallest_dist < 3 and smallest_dist > 30:
                return -5

        return 5

    def building_placement_relations(self):
        def get_category(building):
            building_category = None
            for categories in acceptable_relations:
                if categories in building:
                    building_category = categories

            return building_category

        def get_closest_buildings(neighbors=1):
            closest_buildings = []
            x_pos, _, z_pos = self.current_building[1].begin
            max_x, _, max_z = self.current_building[1].end
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

                new_min = np.min(
                    [min_min_dist, min_max_dist, max_min_dist, max_max_dist]
                )

                closest_buildings.append((building, new_min))

            # Sort the closest buildings based on their distances
            closest_buildings.sort(key=lambda x: x[1])

            # Return the first 'neighbor' number of closest buildings
            return [building[0] for building in closest_buildings[:neighbors]]

        counter = 0
        acceptable_relations = {
            "entertainment": ["residential", "entertainment", "water"],
            "food": ["residential", "food", "production", "water"],
            "gov": ["residential", "water"],
            "production": ["food", "production", "residential", "water"],
            "residential": [
                "entertainment",
                "residential",
                "food",
                "production",
                "water",
            ],
            "water": [
                "entertainment",
                "residential",
                "food",
                "production",
                "gov",
                "water",
            ],
        }

        current_category = get_category(self.current_building[0])
        current_category_relations = acceptable_relations[current_category]

        neighbors = get_closest_buildings(3)
        for neighbor in neighbors:
            neighbor_category = get_category(neighbor[0])
            if neighbor_category in current_category_relations:
                counter += 1
            else:
                counter -= 1

        return counter

    def large_buildings(self):
        return 0.001 * (self.current_building[1].volume)

    def underground(self):
        counter = 0
        building_height = self.mini_terrain[0, 0]
        _, max_y, _ = self.current_building[1].end

        height = building_height + max_y

        counter += np.sum(self.mini_terrain > height)

        return counter

    def cord2map(self, x, z):
        px = abs(self.offx - x)
        pz = abs(self.offz - z)

        return px, pz

    def sub_map(self):
        if len(self.current_building) == 0:
            return None, None

        x0, _, z0 = self.current_building[1].begin
        x0, z0 = self.cord2map(x0, z0)

        x_max, _, z_max = self.reader.get_data(self.current_building[0], "size")

        x1 = x0 + x_max.value - 1
        z1 = z0 + z_max.value - 1

        # Use array slicing to extract the subset
        building_map = self.terrain_map[x0 : x1 + 1, z0 : z1 + 1]
        building_water_map = self.water_map[x0 : x1 + 1, z0 : z1 + 1]

        return building_map, building_water_map

    def total_fitness(self):
        functionality = 0
        aesthetics = 0
        adaptability = 0


        # overlap = self.check_overlap()
        # total_buildings = self.total_buildings()
        # break_terrain = self.break_terrain()
        # floating = self.check_floating()
        # underground = self.underground()
        # spacing = self.building_spacing()
        # diversity = self.check_diversity()
        # large = self.large_buildings()
        # relations = self.building_placement_relations()

        functionality = (
            self.check_overlap() + self.total_buildings()  # self.blocked_doors() +
        )
        adaptability = (
            self.break_terrain()
            + self.check_overlap()
            + self.check_floating()
            + self.underground()
            + self.total_buildings()
        )
        aesthetics = (
            self.building_spacing()
            + self.check_diversity()
            + self.check_overlap()
            + self.total_buildings()
            + self.large_buildings()
            + self.building_placement_relations()
        )

        # return overlap + total_buildings + break_terrain + floating+ underground+spacing+diversity+large+relations
        return (
            ((1 / 3.0) * functionality)
            + ((1 / 3.0) * adaptability)
            + ((1 / 3.0) * aesthetics)
        )


if __name__ == "__main__":
    pass
