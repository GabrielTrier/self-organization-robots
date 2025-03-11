'''
@authors 
Rayane Bouaita
Gabriel Trier
Pierre El Anati

Groupe 21

@date 11/03/2025
'''

from model import RobotModel

# Paramètres de la simulation
NUM_AGENTS = 5
GRID_WIDTH = 15
GRID_HEIGHT = 9
STEPS = 20

# Initialiser le modèle
model = RobotModel(NUM_AGENTS, GRID_WIDTH, GRID_HEIGHT)

# Lancer la simulation
for _ in range(STEPS):
    model.step()
    print(f"Étape {_ + 1} exécutée")
