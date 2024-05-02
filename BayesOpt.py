import os
import time
import sys
from skopt import gp_minimize
from skopt.space import Integer, Categorical
from generateRandomSample import generateRandomSample


class BayesOpt:
    def __init__(self, max_buildings):
        self.max_buildings = max_buildings
        self.generator = generateRandomSample()

        self.generator.check_editor_connection()
        self.generator.initialize_slice()
        self.fitness_cost = float("inf")
        self.building_locations = []

    def optimize(self):
        # TODO: define dataset based on biome and map topology (rivers/sea/etc.)
        # TODO: add context to buildings
        per_min_x, per_max_x, per_min_z, per_max_z = self.generator.perimeter_min_max()
        building_list = self.list_nbt_files("basic")

        for _ in range(self.max_buildings):
            space = (
                [Integer(per_min_x, per_max_x)]
                + [Integer(per_min_z, per_max_z)]
                + [Categorical(building_list)]
            )

            result = gp_minimize(
                self.generate_villages,
                dimensions=space,
                n_calls=7,
                n_random_starts=3,
                random_state=0,
            )

        return result

    def list_nbt_files(self, dataset):
        nbt_files = []
        path = os.path.join("nbtData", dataset)

        for file_name in os.listdir(path):
            if file_name.endswith(".nbt"):
                nbt_files.append(os.path.join(path, file_name))
        return nbt_files

    def generate_villages(self, params):
        # params = x, y, path2nbt
        if self.generator.should_build(params, self.building_locations, self.fitness_cost):
            self.building_locations.append(
                self.generator.generate_building(params, self.max_buildings)
            )
            self.fitness_cost = self.generator.evaluate_fitness(self.building_locations)

        return self.fitness_cost

    def build(self, params):
        self.generator.choose_generated_buildings(
            params, self.max_buildings, build=True
        )

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
    # optimizer = BayesOpt(5)
    # result = optimizer.optimize()

    # # Calculate the elapsed time
    # elapsed_time = time.time() - start_time

    # optimizer.build(result.x)

    # print("Elapsed time:", elapsed_time)
    # print("Best parameters:", result.x)
    # print("Best objective:", result.fun)
