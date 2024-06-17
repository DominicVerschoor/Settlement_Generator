import numpy as np
from nbt_reader import nbt_reader
from gdpc.vector_tools import distance, dropY
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
        """
        Sets parameters to evaluate the building.

        Parameters:
        - current: The building currently being evaluated
        - placed: A list of buildings already placed
        - map: The height map of the area
        - water_map: The map indicating water blocks
        - offset_x: The x-axis offset for the current building's position
        - offset_z: The z-axis offset for the current building's position
        """

        self.offx = offset_x
        self.offz = offset_z
        self.current_building = current
        self.placed_buildings = placed
        self.terrain_map = map
        self.water_map = water_map
        self.mini_terrain, self.mini_water = self.sub_map()
        self.building_base = self.get_base_area()

    def check_floating(self):
        """
        Evaluates if the building is floating above the terrain or water.

        Returns:
        - A score representing the penalty for the building being above the terrain or water.
        """
        counter = 0
        building_height = self.mini_terrain[0, 0]
        category = self.get_category(self.current_building)

        mask = self.mini_terrain < building_height
        distances = np.abs(self.mini_terrain[mask] - building_height)

        counter -= np.sum(distances)
        if category == "water":
            counter -= 3 * np.sum(self.mini_water == 0)
        else:
            counter -= 3 * np.sum(self.mini_water == 1)

        return counter

    def check_overlap(self):
        """
        Checks if the current building overlaps with any already placed buildings.

        Returns:
        - True if there is an overlap, otherwise False.
        """
        for building in self.placed_buildings:
            if self.current_building[1].collides(building[1]):
                return True

        return False

    def building_type_diversity(self):
        """
        Calculates the diversity of building types among the placed buildings, including the current building.

        Returns:
        - The number of unique building categories.
        """
        placed_cat = [self.get_category(self.current_building)]
        for building in self.placed_buildings:
            placed_cat.append(self.get_category(building))

        unique_categories = set(map(tuple, placed_cat))

        return len(unique_categories)

    def is_duplicate(self):
        """
        Checks if the current building is a duplicate of any already placed building.

        Returns:
        - -1 if the current building is a duplicate, otherwise 1.
        """
        if self.current_building in self.placed_buildings:
            return -1

        return 1

    def total_buildings(self):
        """
        Calculates the total number of buildings, including the current building.

        Returns:
        - The total number of buildings.
        """
        return len(self.placed_buildings) + 1

    def break_terrain(self):
        """
        Evaluates the impact of the building on the terrain by considering the terrain breakage.

        Returns:
        - A score representing the penalty for terrain breakage caused by the building.
        """
        counter = 0
        building_height = self.mini_terrain[0, 0]

        mask = self.mini_terrain >= building_height
        distances = np.abs(self.mini_terrain[mask] - building_height)

        counter -= np.sum(distances)

        return counter

    def building_spacing(self, min_dist=3, max_dist=30):
        """
        Checks the spacing between the current building and already placed buildings to ensure it falls within a specified range.

        Parameters:
        - min_dist: The minimum acceptable distance between buildings (default is 3).
        - max_dist: The maximum acceptable distance between buildings (default is 30).

        Returns:
        - 1 if the spacing is acceptable, otherwise -1.
        """
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

            if smallest_dist < min_dist and smallest_dist > max_dist:
                return -1

        return 1

    def building_placement_relations(self):
        """
        Evaluates the relationship of the current building with its closest neighbors based on predefined acceptable relations.

        Returns:
        - A tuple containing:
            - The relationship score of the current building with its neighbors.
            - The number of closest neighbors considered.
        """

        def get_closest_buildings(neighbors=3):
            """
            Finds the closest buildings to the current building.

            Parameters:
            - neighbors: The number of closest neighbors to consider (default is 3).

            Returns:
            - A list of the closest buildings.
            """
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
            "gov": ["residential", "water", "gov"],
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

        neighbors = get_closest_buildings()
        for neighbor in neighbors:
            neighbor_category = self.get_category(neighbor[0])
            if neighbor_category in current_category_relations:
                counter += 1
            else:
                counter -= 1

        return counter, len(neighbors)

    def large_buildings(self):
        """
        Calculates a score based on the size of the building's base area.

        Returns:
        - A score proportional to the building's base area.
        """
        return 0.05 * (self.building_base)

    def get_category(self, building):
        """
        Determines the category of a building.

        Parameters:
        - building: The building to categorize.

        Returns:
        - The category of the building as a string.
        """
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
        """
        Converts coordinates to the corresponding map indices.

        Parameters:
        - x: The x-coordinate.
        - z: The z-coordinate.

        Returns:
        - A tuple (px, pz) representing the map indices.
        """
        px = abs(self.offx - x)
        pz = abs(self.offz - z)

        return px, pz

    def sub_map(self):
        """
        Extracts a sub-map of the terrain and water for the current building.

        Returns:
        - A tuple (building_map, building_water_map) representing the terrain and water maps for the building.
        """
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

    def get_base_area(self):
        """
        Calculates the base area of the current building.

        Returns:
        - The base area of the building.
        """
        start = dropY(self.current_building[1].begin)
        end = dropY(self.current_building[1].end)

        return abs(start[0] - end[0]) * abs(start[1] - end[1])

    def total_fitness(self):
        """
        Calculates the total fitness score of the current building based on various evaluation metrics.

        Returns:
        - The total fitness score of the building.
        """
        if self.check_overlap():
            return -100

        total_buildings = self.total_buildings()
        break_terrain = self.building_base + self.break_terrain()
        floating = self.building_base + self.check_floating()
        spacing = self.building_spacing()
        cat_div = self.building_type_diversity()
        large = self.large_buildings()
        relations, max_relations = self.building_placement_relations()
        duplicate = self.is_duplicate()

        # Get the maximum scores
        max_individual_score = 2 * self.building_base + large
        max_group_score = total_buildings + cat_div
        max_relation_score = abs(spacing) + max_relations + abs(duplicate)

        # Normalize the scores
        individual_score = (break_terrain + large + floating) / max_individual_score
        relation_score = (spacing + relations + duplicate) / max_relation_score
        group_score = (
            total_buildings + spacing + cat_div + relations + duplicate
        ) / max_group_score

        # Compute the total score
        total_score = (individual_score + group_score + relation_score) / 3

        return total_score