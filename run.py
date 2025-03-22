'''
@authors 
Rayane Bouaita
Gabriel Trier
Pierre El Anati

Groupe 21

@date 11/03/2025
'''

from model import RobotModel

#Paramètres de la simulation
GRID_WIDTH = 15
GRID_HEIGHT = 9
GREEN_WASTE = 4
YELLOW_WASTE = 4
RED_WASTE = 4
N_GREEN = 1
N_YELLOW = 1
N_RED = 1

model = RobotModel(
    width=GRID_WIDTH,
    height=GRID_HEIGHT,
    green_waste=GREEN_WASTE,
    yellow_waste=YELLOW_WASTE,
    red_waste=RED_WASTE,
    n_green=N_GREEN,
    n_yellow=N_YELLOW,
    n_red=N_RED,
)