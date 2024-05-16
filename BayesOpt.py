import os
import time
import sys
import warnings
from skopt import gp_minimize
from skopt.space import Integer, Categorical
from generateRandomSample import generateRandomSample


class BayesOpt:
    def __init__(self, max_buildings, depth=0):
        self.max_buildings = max_buildings
        self.generator = generateRandomSample()
        warnings.filterwarnings("ignore")

        self.fitness_cost = 0
        self.depth = depth
        self.building_locations = []
        self.location_sub_tree = []

    def optimize(self):
        # TODO: define dataset based on biome and map topology (rivers/sea/etc.)
        # TODO: add context to buildings
        print("Start Optimization")
        results = []
        fitness_sub_tree = []
        self.location_sub_tree = []
        per_min_x, per_max_x, per_min_z, per_max_z = self.generator.perimeter_min_max()
        building_list = self.list_nbt_files("basic")
        for i in range(max(self.max_buildings, self.max_buildings * self.depth)):
            space = (
                [Integer(per_min_x, per_max_x)]
                + [Integer(per_min_z, per_max_z)]
                + [Categorical(building_list)]
            )

            result = gp_minimize(
                self.generate_villages,
                dimensions=space,
                n_calls=30,
                n_random_starts=10,
                random_state=0,
            )

            building_output = self.generator.generate_building(result.x)
            fitness_sub_tree.append(result.fun)
            self.location_sub_tree.append(building_output)

            if len(fitness_sub_tree) >= self.depth:
                print("Iteration: ", i)
                if self.generator.should_build(
                    self.location_sub_tree[0],
                    self.building_locations + self.location_sub_tree[1:],
                    fitness_sub_tree[0],
                ):
                    results.append(result)
                    self.building_locations.append(self.location_sub_tree[0])
                    self.fitness_cost += fitness_sub_tree[0]

                fitness_sub_tree = []
                self.location_sub_tree = []

        return results, self.fitness_cost

    def list_nbt_files(self, dataset):
        nbt_files = []
        path = os.path.join("nbtData", dataset)

        for file_name in os.listdir(path):
            if file_name.endswith(".nbt"):
                nbt_files.append(os.path.join(path, file_name))
        return nbt_files

    def generate_villages(self, params):
        fitness_cost = 0
        building = self.generator.generate_building(params)
        # params = x, y, path2nbt

        fitness_cost = self.generator.evaluate_fitness(
            building, self.building_locations + self.location_sub_tree
        )

        return fitness_cost

    def build(self, params):
        self.generator.generate_building(params, build=True)

    # Define a custom callback function to monitor the optimization process
    # Define a threshold for improvement
    # threshold = 0.01

    # # Initialize the best objective value
    # best_objective_value = float('inf')
    # def custom_callback(res):
    #     nonlocal best_objective_value

    #     # Update the best objective value if the current iteration improves it
    #     if res.fun < best_objective_value:
    #         best_objective_value = res.fun

    #     # Check if the improvement falls below the threshold
    #     if abs(res.fun - best_objective_value) < threshold:
    #         # Stop the optimization process
    #         return True

    # # Run the optimization with the custom callback
    # result = gp_minimize(objective_function, dimensions=..., callback=custom_callback)


if __name__ == "__main__":
    # Record the start time
    start_time = time.time()

    # Optimize the black box function
    optimizer = BayesOpt(15, depth=2)
    results, final_score = optimizer.optimize()

    # Calculate the elapsed time
    elapsed_time = time.time() - start_time

    for res in results:
        print("Best parameters:", res.x)
        print("Best objective:", res.fun)
        optimizer.build(res.x)

    print("Elapsed time:", elapsed_time)
