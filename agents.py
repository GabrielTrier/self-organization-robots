'''
@authors 
Rayane Bouaita
Gabriel Trier
Pierre El Anati

Groupe 21

@date 11/03/2025
'''

import mesa

class RobotAgent(mesa.Agent):
    def __init__(self, model):
        super().__init__(model)

    def move(self):
        possible_steps = self.model.grid.get_neighborhood(
            self.pos, moore=True, include_center=False
        )
        new_position = self.random.choice(possible_steps)
        self.model.grid.move_agent(self, new_position)

    def step (self):
        self.move()