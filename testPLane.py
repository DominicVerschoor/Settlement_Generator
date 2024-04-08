# example of the test problem
import numpy as np
import math
import matplotlib.pyplot as plt

class Plane:
    def __init__(self):
        pass

    def definePlane(self, noise):
        # Define the range for the plot
        x_range = np.arange(0, 1, 0.01)
        y_range = np.arange(0, 1, 0.01)

        # Create a meshgrid from the ranges
        X, Y = np.meshgrid(x_range, y_range)

        # Calculate the corresponding z values for each point in the meshgrid
        Z = (X**2 * np.sin(5 * np.pi * X)**6.0) + noise

        return X,Y,Z


    
    def plot(self, points, noise=0):
        X,Y,Z = self.definePlane(noise)

        # Create a 3D plot
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')

        # Plot the plane
        ax.plot_surface(X, Y, Z, alpha=0.5)

        # Plot the point
        for point in points:
            ax.scatter(point[0], point[1], point[2], color='red', s=100)

        # Set labels and title
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        ax.set_title('2D Plane')

        # Show the plot
        plt.show()



if __name__ == "__main__":
    opt = Plane()
    points = np.array([[0, 0, 5], [1, 0, 0], [0, 3, 0]]) # x,y,z
    opt.plot(points = points)