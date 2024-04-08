# example of the test problem
from math import sin
from math import pi
from numpy import arange
from numpy import argmax
from numpy.random import normal
from matplotlib import pyplot

class BayesOpt:
    def __init__(self):
        pass

    # objective function
    def objective(self, x, noise=0.1):
        noise = normal(loc=0, scale=noise)
        return (x**2 * sin(5 * pi * x)**6.0) + noise
    
    def plot(self):
        # grid-based sample of the domain [0,1]
        X = arange(0, 1, 0.01)
        # sample the domain without noise
        y = [self.objective(x, 0) for x in X]
        # sample the domain with noise
        ynoise = [self.objective(x) for x in X]
        # find best result
        ix = argmax(y)
        print('Optima: x=%.3f, y=%.3f' % (X[ix], y[ix]))
        # plot the points with noise
        pyplot.scatter(X, ynoise)
        # plot the points without noise
        pyplot.plot(X, y)
        # show the plot
        pyplot.show()


if __name__ == "__main__":
    opt = BayesOpt()
    opt.plot()