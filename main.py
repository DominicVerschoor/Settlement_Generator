import time
from optimizationAlgorithm import BayesOpts
from buildingHandler import generateRandomSample

if __name__ == "__main__":
    # Record the start time
    start_time = time.time()
    optimizer = BayesOpts(time=600, threshold=0.5, depth=1, n_steps=40)
    results = optimizer.optimize()

    # Calculate the elapsed time
    elapsed_time = time.time() - start_time

    gen = generateRandomSample()
    total_ind = 0
    for res in results:
        print("Best parameters:", res.params)
        print("Best objective:", res.score)

        optimizer.build(res)

    print("Total score:", total_ind)
    print("Total buildings:", len(results))
