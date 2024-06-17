# GDMC Settlement Generator
#### Dominic Verschoor


The focus of this thesis is to "design a machine-learning algorithm that can generate a functional and aesthetic settlement which can adapt to its environment in Minecraft." The idea for this thesis originates from the Generative Design in Minecraft (GDMC) competition, where the scoring criteria and competition rules are followed. Bayesian Optimization was used to generate the settlement. Several hyperparameters were optimized, including rejection threshold, number of steps per iteration, and depth (used in a tree-like structure to consider future buildings during evaluation). The hyperparameters were tested and resulted in the following: a rejection threshold of 0.5, 30 steps per iteration, and a depth of 2. This thesis concludes that using the aforementioned hyperparameters and Bayesian Optimization, it is possible to generate a functional and aesthetic settlement that can adapt to its environment.

### Requirements
- Minecraft
- GDMC-HTTP Minecraft mod version 1.4.5 or greater (installed at https://github.com/Niels-NTG/gdmc_http_interface/releases)
- Python3
- Packages from requirements.txt

### How to run
- Open minecraft and create a new world
- Type command "\setbuildarea x0 y0 z0 x1 y1 z1" in game to set build perimeter around where the settlement should be built (the y parameter can be anything)
- Run main.py
