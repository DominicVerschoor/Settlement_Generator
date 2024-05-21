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
        self.dataset = self.list_nbt_files("normal")

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
        per_min_x, per_max_x, per_min_z, per_max_z = self.generator.perimeter_min_max()
        building_list = len(self.dataset)
        bounds = {
            "x": (per_min_x, per_max_x),
            "z": (per_min_z, per_max_z),
            "building_id": (0, building_list - 1),
        }

        prev_score = -float('inf')
        fail_counter = 0
        for _ in range(self.max_buildings):
            starting_building = self.top_optimized_candidates(bounds)
            outputs = self.depth_search_optimization(starting_building, bounds)
            best_out = self.get_highest_score(outputs)

            if best_out.score > prev_score:
                prev_score = best_out.score
                x, z, id = self.node2building(best_out)
                best_building = self.generator.generate_building(x, z, id)
                self.building_locations.append(best_building)
                results.append(best_out)
            else:
                fail_counter += 1
            
            if fail_counter == 5:
                print('Max capacity reached')
                break

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
        )

        optimizer.maximize(
            init_points=15,
            n_iter=25,
        )

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
        x = int(x)
        z = int(z)
        building_id = int(building_id)
        building = self.dataset[building_id]
        building_output = self.generator.generate_building(x, z, building)

        fitness_cost = self.generator.evaluate_fitness(
            building_output, self.building_locations
        )

        return fitness_cost

    def node2building(self, node):
        id = self.dataset[int(node.params["building_id"])]
        x = int(node.params["x"])
        z = int(node.params["z"])
        return x, z, id

    def building2node(self):
        pass

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
        self.generator.generate_building(x, z, id, build=True)


if __name__ == "__main__":
    # Record the start time
    start_time = time.time()

    # Optimize the black box function
    optimizer = BayesOpts(30, depth=2)
    results = optimizer.optimize()

    # Calculate the elapsed time
    elapsed_time = time.time() - start_time

    for res in results:
        print("Best parameters:", res.params)
        print("Best objective:", res.score)
        optimizer.build(res)

    print("Elapsed time:", elapsed_time)
