import time
from skopt import gp_minimize
from skopt.space import Integer, Categorical
import numpy as np
from generateRandomSample import generateRandomSample
from Fitness import Fitness

class BayesOpt:
    def __init__(self, max_buildings):
        self.max_buildings = max_buildings
        self.generator = generateRandomSample()
        self.map = self.generator.map_to_array()

    def optimize(self):
        #TODO: define dataset based on biome and map topology (rivers/sea/etc.)
        per_min_x, per_max_x, per_min_z, per_max_z = self.generator.perimeter_min_max()
        space = [Integer(1, self.max_buildings)] + \
                [Integer(per_min_x, per_max_x) for _ in range(self.max_buildings)] + \
                [Integer(per_min_z, per_max_z) for _ in range(self.max_buildings)] + \
                [Categorical(['acacia.nbt', 'birch.nbt', 'oak.nbt', 'spruce.nbt']) for _ in range(self.max_buildings)]

        result = gp_minimize(
            self.black_box_function,
            dimensions=space,
            n_calls=1,
            n_random_starts=1,
            random_state=0
        )

        return result


    def black_box_function(self, params):
        dataset = 'basic'
        self.generator.choose_generated_buildings(params, dataset, self.max_buildings)
        fitness = Fitness(self.generator.building_locations, self.map)
        total_cost = fitness.total_fitness()
        self.generator.building_locations = []
        return total_cost
    
    def build(self, params):
        self.generator.choose_generated_buildings(params, self.max_buildings, build=True)

if __name__ == "__main__":
    # Record the start time
    start_time = time.time()

    # Optimize the black box function
    optimizer = BayesOpt(5)
    result = optimizer.optimize()

    # Calculate the elapsed time
    elapsed_time = time.time() - start_time

    optimizer.build(result.x)

    print("Elapsed time:", elapsed_time)
    print("Best parameters:", result.x)
    print("Best objective:", result.fun)
