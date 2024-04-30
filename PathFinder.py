import numpy as np
import math
import heapq
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
    distance2,
    Box,
)
from glm import ivec2, ivec3
from generateRandomSample import generateRandomSample
from gdpc import __url__, Editor, Block


class PathFinder:
    def __init__(self, building_locations, map):
        """
        Initializes the class instance.
        """
        # self.checkpoints = [location[1] for location in building_locations]
        self.editor = Editor()
        self.reader = nbt_reader()
        self.map = map
        self.bounds = []
        self.checkpoints = self.adjust_checkpoints(building_locations)


    class Cell:
        def __init__(self):
            self.parent = ivec3(0, 0, 0)
            self.total_cost = float("inf")
            self.current_cost = float("inf")
            self.heuristic = 0

    def adjust_checkpoints(self, building_locations):
        checkpoints = []
        for building in building_locations:
            bot_door, _ = self.reader.get_door_pos(building[0])

            if bot_door == None:
                checkpoints.append(building[1] + ivec3(0, -1, 0))
            else:
                checkpoints.append(bot_door[1] + building[1] + ivec3(0, -1, 0))

        return checkpoints

    def inbounds(self, location):
        min_x = min_z = float("inf")
        max_x = max_z = float("-inf")

        for _, (x, _, z) in self.map:
            min_x = min(min_x, x)
            max_x = max(max_x, x)
            min_z = min(min_z, z)
            max_z = max(max_z, z)

        return min_x <= location[0] <= max_x and min_z <= location[2] <= max_z

    def blocked(self, current, prev):
        return abs(current[1] - prev[1]) > 1

    def is_complete(self):
        return len(self.checkpoints) == 0

    def calc_dist(self, current, dest):
        # for now its just euclid dist^2
        return distance2(current, dest)

    def reached_checkpoint(self, current, checkpoint):
        return current == checkpoint

    def nearest_checkpoint(self, current):
        shortest = float("inf")
        dest = ivec3(0, 0, 0)
        for checkpoint in self.checkpoints:
            dist = self.calc_dist(current, checkpoint)
            if dist < shortest:
                shortest = dist
                dest = checkpoint

        return dest

    def a_star(self):
        if self.is_complete():
            return

        open_list = []
        closed_list = {(cord[1][0], cord[1][1], cord[1][2]): False for cord in self.map}

        cell_details = {
            (cord[1][0], cord[1][1], cord[1][2]): self.Cell() for cord in self.map
        }

        start = tuple(self.checkpoints[0])
        self.checkpoints.pop(0)
        cell_details[start].total_cost = 0
        cell_details[start].current_cost = 0
        cell_details[start].heuristic = 0
        cell_details[start].parent = start

        heapq.heappush(open_list, (0.0, start))

        dest = self.nearest_checkpoint(start)

        while len(open_list) > 0:
            current_smallest = heapq.heappop(open_list)
            current_loc = current_smallest[1]

            closed_list[current_loc] = True

            neighbors = [
                (1, 0, 0),
                (1, 0, 1),
                (1, 0, -1),
                (-1, 0, 0),
                (-1, 0, 1),
                (-1, 0, -1),
                (0, 0, 1),
                (0, 0, -1),
            ]

            for direction in neighbors:
                new_loc = tuple(a + b for a, b in zip(current_loc, direction))

                if (
                    self.inbounds(new_loc)
                    and not self.blocked(new_loc, current_loc)
                    and not closed_list[new_loc]
                ):
                    # calculate new costs
                    new_cost = cell_details[current_loc].current_cost + 1
                    new_heuristic = self.calc_dist(current_loc, dest)
                    new_total = new_cost + new_heuristic

                    # reached a checkpoint
                    if self.reached_checkpoint(new_loc, dest):
                        # set details
                        cell_details[new_loc].total_cost = new_total
                        cell_details[new_loc].current_cost = new_cost
                        cell_details[new_loc].heuristic = new_heuristic
                        cell_details[new_loc].parent = current_loc

                        if len(self.checkpoints) == 0:
                            self.trace_path(cell_details, dest)
                            return

                        # set new dest and remove checkpoint from list
                        dest = self.nearest_checkpoint(new_loc)
                        self.checkpoints = [
                            checkpoint
                            for checkpoint in self.checkpoints
                            if checkpoint != dest
                        ]

                    # if new total dist is smallest
                    elif cell_details[new_loc].total_cost > new_total or cell_details[
                        new_loc
                    ].total_cost == float("inf"):
                        # add to open_list and set details
                        heapq.heappush(open_list, (new_total, new_loc))

                        cell_details[new_loc].total_cost = new_total
                        cell_details[new_loc].current_cost = new_cost
                        cell_details[new_loc].heuristic = new_heuristic
                        cell_details[new_loc].parent = current_loc

    # Trace the path from source to destination
    def trace_path(self, cell_details, dest):
        print("The Path is ")
        loc = tuple(dest)
        path = []

        # Trace the path from destination to source using parent cells
        while not (cell_details[loc].parent == loc):
            path.append(loc)
            temp_loc = cell_details[loc].parent
            loc = temp_loc

        # Add the source cell to the path
        path.append(loc)
        # Reverse the path to get the path from source to destination
        path.reverse()

        # Print the path
        for i in path:
            # i = tuple(a + b for a, b in zip(i, (0,-1,0)))
            self.editor.placeBlock(i, Block("stonedw"))
            print("->", i, end=" ")
        print()


if __name__ == "__main__":
    sample = generateRandomSample()
    # sample.generate_buildings(dataset="BuildingDataSet", num_buildings=1)
    map = sample.map_to_array()
    sample.choose_generated_buildings(
        params=[2, -177, -177, 30, 34, "oak.nbt", "spruce.nbt"],
        dataset="basic",
        max_buildings=2,
    )

    path = PathFinder(sample.building_locations, map)
    print(path.a_star())
