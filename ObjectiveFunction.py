import numpy as np
from nbt_reader import nbt_reader
from gdpc.vector_tools import distance
from glm import ivec2


class ObjectiveFunction:

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
        self.building_size = self.current_building[1].volume

    def check_floating(self):
        counter = 0
        building_height = self.mini_terrain[0, 0]

        mask = self.mini_terrain < building_height
        distances = np.abs(self.mini_terrain[mask] - building_height)

        counter -= np.sum(distances)
        counter -= np.sum(self.mini_water == 1)

        return counter

    def check_overlap(self):
        for building in self.placed_buildings:
            if self.current_building[1].collides(building[1]):
                return True

        return False

    def building_type_diversity(self):
        placed_cat = [self.get_category(self.current_building)]
        for building in self.placed_buildings:
            placed_cat.append(self.get_category(building))

        unique_categories = set(map(tuple, placed_cat))

        return 10 * len(unique_categories)

    def is_duplicate(self):
        if self.current_building in self.placed_buildings:
            return -7

        return 7
    
    def building_diversity(self):
        current = []
        current.append(tuple(self.current_building))  # Convert list to tuple
        all_buildings = self.placed_buildings.copy() + current

        unique_buildings = set(
            map(tuple, all_buildings)
        )  # Convert lists to tuples for uniqueness

        return 5 * len(unique_buildings)

    def total_buildings(self):
        return 5 * len(self.placed_buildings) + 1

    def break_terrain(self):
        # building = path2nbt, ivec of bot left
        counter = 0
        building_height = self.mini_terrain[0, 0]
        counter -= np.sum(self.mini_terrain > building_height)

        return counter

    def building_spacing(self, min_dist=3, max_dist=30):
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
            if smallest_dist < min_dist and smallest_dist > max_dist:
                return -10

        return 10

    def building_placement_relations(self):
        def get_closest_buildings(neighbors=3):
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

            if neighbors > len(closest_buildings) or neighbors < 0:
                neighbors = len(
                    closest_buildings
                )  # Use the full range if neighbors is out of bounds

            return [building[0] for building in closest_buildings[:neighbors]]

        counter = 0
        acceptable_relations = {
            "entertainment": ["residential", "entertainment", "water"],
            "food": ["residential", "food", "production", "water"],
            "gov": ["residential", "water", 'gov'],
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

        current_category = self.get_category(self.current_building)
        current_category_relations = acceptable_relations[current_category]

        neighbors = get_closest_buildings(2)
        for neighbor in neighbors:
            neighbor_category = self.get_category(neighbor[0])
            if neighbor_category in current_category_relations:
                counter += 5
            else:
                counter -= 5

        return counter

    def large_buildings(self):
        return 0.002 * (self.building_size)

    def underground(self):
        counter = 0
        building_height = self.mini_terrain[0, 0]
        _, max_y, _ = self.current_building[1].end

        height = building_height + max_y

        counter += np.sum(self.mini_terrain > height)

        return counter

    def get_category(self, building):
        building_category = None
        category_list = {
            "entertainment",
            "food",
            "gov",
            "residential",
            "production",
            "water",
        }
        for categories in category_list:
            if categories in building[0]:
                building_category = categories

        return building_category

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
        if self.check_overlap():
            return -10000

        total_buildings = self.total_buildings()
        break_terrain = self.break_terrain()
        floating = self.check_floating()
        spacing = self.building_spacing()
        cat_div = self.building_type_diversity()
        # diversity = self.building_diversity()
        large = self.large_buildings()
        relations = self.building_placement_relations()
        duplicate = self.is_duplicate()

        return (
            total_buildings
            + break_terrain
            + floating
            + spacing
            # + diversity
            + large
            + relations
            + cat_div
            + duplicate
        )


if __name__ == "__main__":
    pass
