'''
@authors 
Rayane Bouaita
Gabriel Trier
Pierre El Anati

Groupe 21

@date 11/03/2025
'''

import mesa 
from agents import RobotAgent
from mesa.datacollection import DataCollector

class RobotModel (mesa.Model):
    def __init__(self, n=5, width=15, height=9):
        super().__init__()
        self.grid = mesa.space.MultiGrid(width, height, True)
        self.datacollector = DataCollector(
            model_reporters={"Step": lambda m: m.schedule.time}
        )
        agents = RobotAgent.create_agents(model=self, n=n)
        x = self.rng.integers(0, self.grid.width, size=(n,))
        y = self.rng.integers(0, self.grid.height, size=(n,))
        for a, i, j in zip(agents, x, y):
            self.grid.place_agent(a, (i, j))

    def step(self):
        self.agents.shuffle_do("step")
        print("ici")