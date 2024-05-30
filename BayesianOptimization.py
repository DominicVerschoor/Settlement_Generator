import os
import time
from bayes_opt import BayesianOptimization
import numpy as np
from generateRandomSample import generateRandomSample


class BayesOpts:
    def __init__(self, time, depth=0):
        self.generator = generateRandomSample()
        self.seed = 0

        self.time = time
        self.depth = depth
        self.building_locations = []
        self.dataset = self.list_nbt_files("normal")
        self.terrain_map, self.water_map = self.generator.map_area()
        self.per_min_x, self.per_max_x, self.per_min_z, self.per_max_z = self.generator.perimeter_min_max()

    class BuildingNode:
        def __init__(self):
            self.parent = None
            self.params = []
            self.children = None
            self.score = -float("inf")

        def __repr__(self):
            return f"Node\n\nscore={self.score}\n\nparams={self.params}\n\nparent={self.parent}\n\n"

    def optimize(self):
        print("Start Optimization")
        results = []
        building_list = len(self.dataset)
        bounds = {
            "x": (self.per_min_x, self.per_max_x),
            "z": (self.per_min_z, self.per_max_z),
            "building_id": (0, building_list - 1),
        }

        start_time = time.time()
        iteration_end = 0
        prev_score = 0
        while True:
            iteration_start = time.time()
            elapsed_time = iteration_start - start_time

            if elapsed_time >= self.time - iteration_end:
                print("Time limit reached")
                break

            starting_building = self.top_optimized_candidates(bounds)
            best_start = self.get_highest_score(starting_building)
            if best_start.score > prev_score:
                outputs = self.depth_search_optimization(starting_building, bounds)
                best_out = self.get_highest_score(outputs)
                x, z, id = self.node2building(best_out)
                best_building = self.generator.create_building(id, x, z)
                self.building_locations.append(best_building)
                prev_score = best_start.score
                results.append(best_out)

            iteration_end= time.time() - iteration_start

        return results

    def get_highest_score(self, candidates):
        initial_nodes = []
        leaf_nodes = []
        for current_node in candidates:
            if not current_node.parent:
                initial_nodes.append(current_node)
            if not current_node.children:
                leaf_nodes.append(current_node)

        highest_score_leaf = max(leaf_nodes, key=lambda node: node.score)

        def trace_ancestry(node):
            ancestors = [node]
            current_node = node
            while current_node.parent:
                current_node = current_node.parent
                ancestors.append(current_node)
            return ancestors

        highest_score_ancestry = trace_ancestry(highest_score_leaf)

        return highest_score_ancestry[-1]

    def depth_search_optimization(self, candidates, bounds, current_depth=1):

        if current_depth == self.depth:
            # Return the final top score and its ancestors
            return candidates

        # Call top_optimized_candidates on children and collect results
        results = []
        for child in candidates:
            if child.children is None:
                child_results = self.top_optimized_candidates(
                    bounds
                )  # Generate child nodes
                for result_node in child_results:
                    result_node.parent = child
                child.children = child_results
                results.extend(child_results)

        candidates.extend(results)

        return self.depth_search_optimization(candidates, bounds, current_depth + 1)

    def top_optimized_candidates(self, bounds):
        output = []
        optimizer = BayesianOptimization(
            f=self.test_building_loc,
            pbounds=bounds,
            random_state = self.seed
        )

        optimizer.maximize(
            init_points=15,
            n_iter=25,
        )
        
        self.seed += 1
        sorted_fitness = sorted(optimizer.res, key=lambda x: x["target"], reverse=True)
        top_scores = [
            (entry["target"], entry["params"]) for entry in sorted_fitness[: self.depth]
        ]

        for result in top_scores:
            result_node = self.BuildingNode()
            result_node.score = result[0]
            result_node.params = result[1]

            output.append(result_node)

        return output

    def test_building_loc(self, x, z, building_id):
        fitness_cost = 0
        
        building = self.dataset[int(building_id)]
        x_max, _, z_max = self.generator.reader.get_data(building, "size")
        x = int(min(self.per_max_x - x_max.value, x))
        z = int(min(self.per_max_z - z_max.value, z))

        terrain = self.sub_map(x, z, building)
        gradient_y, gradient_x = np.gradient(terrain)
        steepness = np.mean(np.sqrt(gradient_x**2 + gradient_y**2))

        if steepness > 0.25:
            return -10000

        building_output = self.generator.create_building(building, x, z)

        fitness_cost = self.generator.evaluate_fitness(
            building_output, self.building_locations
        )

        return fitness_cost

    def sub_map(self, x, z, current_building):
        if len(current_building) == 0:
            return None

        x0, z0 = self.cord2map(x, z)

        x_max, _, z_max = self.generator.reader.get_data(current_building, "size")

        x1 = x0 + x_max.value - 1
        z1 = z0 + z_max.value - 1

        # Use array slicing to extract the subset
        building_map = self.terrain_map[x0 : x1 + 1, z0 : z1 + 1]

        return building_map
    
    def cord2map(self, x, z):
        px = abs(self.generator.buildRect.begin[0] - x)
        pz = abs(self.generator.buildRect.begin[1] - z)

        return px, pz

    def node2building(self, node):
        id = self.dataset[int(node.params["building_id"])]
        x = int(node.params["x"])
        z = int(node.params["z"])
        return x, z, id

    def list_nbt_files(self, dataset):
        nbt_files = []
        path = os.path.join("nbtData", dataset)

        for root, _, files in os.walk(path):
            for file_name in files:
                if file_name.endswith(".nbt"):
                    nbt_files.append(os.path.join(root, file_name))
        return nbt_files

    def build(self, params):
        x, z, id = self.node2building(params)
        self.generator.create_building(id, x, z, build=True)


if __name__ == "__main__":

    # Record the start time
    start_time = time.time()

    # Optimize the black box function 
    # 600 = 10 min
    optimizer = BayesOpts(time=600, depth=1)
    results = optimizer.optimize()

    # Calculate the elapsed time
    elapsed_time = time.time() - start_time

    for res in results:
        print("Best parameters:", res.params)
        print("Best objective:", res.score)
        optimizer.build(res)

    print("Elapsed time:", elapsed_time)
