import os
import time
from bayes_opt import BayesianOptimization
from generateRandomSample import generateRandomSample


class BayesOpts:
    def __init__(self, max_buildings, depth=0):
        self.max_buildings = max_buildings
        self.generator = generateRandomSample()

        self.fitness_cost = 0
        self.depth = depth
        self.building_locations = []

    def optimization(self):
        # TODO: define dataset based on biome and map topology (rivers/sea/etc.)
        # TODO: add context to buildings
        per_min_x, per_max_x, per_min_z, per_max_z = self.generator.perimeter_min_max()
        building_list = self.list_nbt_files("basic")

        bounds = {
            "x": (per_min_x, per_max_x),
            "z": (per_min_z, per_max_z),
            "building": (building_list),
        }

        for _ in self.max_buildings:
            for _ in self.depth:
                optimal_outputs = self.top_optimized_candidates(bounds)

    def depth_search_optimization(self, candidates, current_depth=0):
        per_min_x, per_max_x, per_min_z, per_max_z = self.generator.perimeter_min_max()
        building_list = self.list_nbt_files("basic")

        bounds = {
            "x": (per_min_x, per_max_x),
            "z": (per_min_z, per_max_z),
            "building": (building_list),
        }
        
        if current_depth == self.depth:
            return []  # Stop recursion if depth limit is reached
        
        # Call top_optimized_candidates on children and collect results
        results = []
        for child in candidates:
            child_results = self.depth_search_optimization(child, current_depth + 1)
            results.extend(child_results)
        
        # Perform optimization on the current node and get top candidates
        node_candidates = self.get_optimized_candidates(bounds)  # Assuming this method exists
        top_candidates = self.get_top_candidates(node_candidates)
        
        # Add the top candidates to the results
        results.extend(top_candidates)
        
        return results

    def top_optimized_candidates(self, bounds):
        optimizer = BayesianOptimization(
            f=self.test_building_loc,
            pbounds=bounds,
            random_state=1,
        )

        optimizer.maximize(
            init_points=2,
            n_iter=3,
        )

        sorted_fitness = sorted(optimizer.res, key=lambda x: x["target"], reverse=True)
        top_scores = [
            (entry["target"], entry["params"]) for entry in sorted_fitness[: self.depth]
        ]

        return top_scores
    


    def test_building_loc(self, x, z, building):
        fitness_cost = 0
        building_output = self.generator.generate_building(x, z, building)

        fitness_cost = self.generator.evaluate_fitness(
            building_output, self.building_locations
        )

        return fitness_cost

    def list_nbt_files(self, dataset):
        nbt_files = []
        path = os.path.join("nbtData", dataset)

        for file_name in os.listdir(path):
            if file_name.endswith(".nbt"):
                nbt_files.append(os.path.join(path, file_name))
        return nbt_files

    def build(self, x, z, building):
        self.generator.generate_building(x, z, building)


if __name__ == "__main__":
    # Record the start time
    start_time = time.time()

    # Optimize the black box function
    optimizer = BayesOpts(15, depth=2)
    results, final_score = optimizer.optimize()

    # Calculate the elapsed time
    elapsed_time = time.time() - start_time

    for res in results:
        print("Best parameters:", res.x)
        print("Best objective:", res.fun)
        optimizer.build(res.x)

    print("Elapsed time:", elapsed_time)
