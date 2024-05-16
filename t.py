from bayes_opt import BayesianOptimization

class Node:
    def __init__(self):
        self.parent = None
        self.params = []
        self.children = None
        self.score = -float('inf')
    
    def __repr__(self):
        return f"Node\n\nscore={self.score}\n\nparams={self.params}\n\nparent={self.parent}\n\n"

# Bounded region of parameter space
def black_box_function(x, y):
    """Function with unknown internals we wish to maximize.

    This is just serving as an example, for all intents and
    purposes think of the internals of this function, i.e.: the process
    which generates its output values, as unknown.
    """
    return (-(x**2) - (y - 1) ** 2 + 1) * 100

def depth_search_optimization(candidates, current_depth=1):

    if current_depth == depth:
        # Return the final top score and its ancestors
        return candidates

    # Call top_optimized_candidates on children and collect results
    results = []
    for child in candidates:
        if child.children is None:
            child_results = top_optimized_candidates(pbounds)  # Generate child nodes
            for result_node in child_results:
                result_node.parent = child
            child.children = child_results
            results.extend(child_results)
    
    candidates.extend(results)
    
    return depth_search_optimization(candidates, current_depth + 1)

def get_highest_score(candidates):
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


def top_optimized_candidates(pbounds):
    output = []
    optimizer = BayesianOptimization(
        f=black_box_function,
        pbounds=pbounds,
        # random_state=1,
    )

    optimizer.maximize(
        init_points=2,
        n_iter=3,
    )

    sorted_fitness = sorted(optimizer.res, key=lambda x: x["target"], reverse=True)
    top_scores = [
        (entry["target"], entry["params"]) for entry in sorted_fitness[:depth]
    ]

    for result in top_scores:
        result_node = Node()
        result_node.score = result[0]
        result_node.params = result[1]

        output.append(result_node)

    return output

depth = 3
pbounds = {"x": (0,10), "y": (0,10)}
start = top_optimized_candidates(pbounds)
outputs = depth_search_optimization(start)

# for out in outputs:
#     print(out)
#     print('====================================================================================')
highest = get_highest_score(outputs)
