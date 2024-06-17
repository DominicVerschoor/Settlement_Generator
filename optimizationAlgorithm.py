import os
import time
from bayes_opt import BayesianOptimization
import numpy as np
from buildingHandler import generateRandomSample


class BayesOpts:
    def __init__(self, time=600, threshold=0.5, depth=1, n_steps=40):
        """
        Initializes Bayesian Optimization Algorithm

        Parameters:
        - time: The time the algorithm will run in seconds
        - Threshold: A rejection threshold. Buildings with a score less than the threshold will not be built. 
        - Depth: The search depth to consider when evaluating a building. Depth of 1 means no search.
        - n_steps: Number of steps to complete on each iteration of Bayesian Optimization 
        """
        self.generator = generateRandomSample()
        self.seed = 0

        self.threshold = threshold
        self.depth = depth
        self.n_iterations = n_steps

        self.time = time

        self.building_locations = []
        self.dataset = self.list_nbt_files("normal")
        self.terrain_map, self.water_map = self.generator.map_area()
        self.per_min_x, self.per_max_x, self.per_min_z, self.per_max_z = (
            self.generator.perimeter_min_max()
        )

    class BuildingNode:
        def __init__(self):
            """
            Initializes Building Node, used for Limited Depth Search
            """
            self.parent = None
            self.params = []
            self.children = None
            self.score = -float("inf")

        def __repr__(self):
            return f"Node\n\nscore={self.score}\n\nparams={self.params}\n\nparent={self.parent}\n\n"

    def optimize(self):
        """
        Starts the optimization algorithm with the parameters from initialization.

        Returns:
        - List containing the outputs of each iteration of Bayesian Optimization
        """

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
        while True:
            iteration_start = time.time()
            elapsed_time = iteration_start - start_time

            if elapsed_time >= self.time - iteration_end:
                print("Time limit reached")
                break

            starting_building = self.top_optimized_candidates(bounds)
            best_start = self.get_highest_score(starting_building)
            if best_start.score > self.threshold:
                outputs = self.depth_search_optimization(starting_building, bounds)
                best_out = self.get_highest_score(outputs)
                x, z, id = self.node2building(best_out)
                best_building = self.generator.create_building(id, x, z)
                self.building_locations.append(best_building)
                results.append(best_out)

            iteration_end = time.time() - iteration_start

        return results

    def get_highest_score(self, candidates):
        """
        Starts the optimization algorithm with the parameters from initialization.

        Parameters:
        - candidates: List of buildings resulted from a iteration of BayesOpts

        Returns:
        - The building with the highest score
        """
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
        """
        Limited depth search to consider future iterations when evaluating.

        Parameters:
        - candidates: List of top n buildings resulted from a iteration of BayesOpts
        - bounds: The map bounds for the optimization
        - current_depth: The current depth being evaluated

        Returns:
        - The top candidates
        """
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
        """
        Performs an iteration of Bayesian optimization.

        Parameters:
        - bounds: The map bounds for the optimization

        Returns:
        - The top N buildings from the optimization based on target score
        """

        output = []
        optimizer = BayesianOptimization(
            f=self.test_building_loc, pbounds=bounds, random_state=self.seed
        )

        optimizer.maximize(
            n_iter=int(0.6 * self.n_iterations),
            init_points=int(0.4 * self.n_iterations),
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
        '''
        Blackbox function used in Bayesian Optimization to evaluated a building.

        Parameters:
        - x: x coordinate of building
        - z: z coordinate of building
        - building_id: the id of the building being placed

        Returns:
        - The score of the building being evaluated
        '''
        objective_score = 0

        building = self.dataset[int(building_id)]
        x_max, _, z_max = self.generator.reader.get_data(building, "size")
        x = int(min(self.per_max_x - x_max.value, x))
        z = int(min(self.per_max_z - z_max.value, z))

        terrain = self.sub_map(x, z, building)
        gradient_y, gradient_x = np.gradient(terrain)
        steepness = np.mean(np.sqrt(gradient_x**2 + gradient_y**2))

        if steepness > 0.25:
            return -100

        building_output = self.generator.create_building(building, x, z)

        objective_score = self.generator.evaluate_obj(
            building_output, self.building_locations
        )

        return objective_score

    def sub_map(self, x, z, current_building):
        '''
        Maps area within the coordinates of the building.

        Parameters:
        - x: x coordinate of building
        - z: z coordinate of building
        - current_building: the current building being placed

        Returns:
        - A array consisting of the height map which is relevant to the current building
        '''
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
        '''
        Maps game coordinates to array indicies.

        Parameters:
        - x: x coordinate of building
        - z: z coordinate of building

        Returns:
        - indicies in array
        '''
        px = abs(self.generator.buildRect.begin[0] - x)
        pz = abs(self.generator.buildRect.begin[1] - z)

        return px, pz

    def node2building(self, node):
        '''
        Converts nodes to buildings information.

        Parameters:
        - node: Building node

        Returns:
        - x, z, and building id from the node
        '''
        id = self.dataset[int(node.params["building_id"])]
        x = int(node.params["x"])
        z = int(node.params["z"])
        return x, z, id

    def list_nbt_files(self, dataset):
        '''
        Lists all the buildings from the chosen dataset.

        Parameters:
        - File path the folder containing the nbt files for the dataset

        '''
        nbt_files = []
        path = os.path.join("nbtData", dataset)

        for root, _, files in os.walk(path):
            for file_name in files:
                if file_name.endswith(".nbt"):
                    nbt_files.append(os.path.join(root, file_name))
        return nbt_files

    def build(self, params):
        '''
        Builds the buildings in game

        Parameters:
        - params: information about the building to be placed
        '''
        x, z, id = self.node2building(params)
        self.generator.create_building(id, x, z, build=True)


if __name__ == "__main__":
    outputs = []
    # Optimize the black box function
    for i in np.arange(0, 1, 1):
        # print(i)
        # if i != 40:
        optimizer = BayesOpts(time=600, threshold=0, depth=1, n_steps=40)
        results = optimizer.optimize()

        gen = generateRandomSample()
        total_ind = 0
        total_grp = 0
        fin = 0
        buildings = []
        for res in results:
            x, z, id = optimizer.node2building(res)
            buildings.append(gen.create_building(id, x, z))

        for building in buildings:
            other_results = [b for b in buildings if b != building]
            ind, semi, tot = gen.get_individual_score(building, other_results)

            total_ind += ind
            total_grp += semi
            if fin == 0:
                fin = tot

        outputs.append([i, total_ind, total_grp, fin])

    for out in outputs:
        print(
            "Crit:", out[0], "||| Ind:", out[1], "||| Grp:", out[2], "||| Tot:", out[3]
        )
