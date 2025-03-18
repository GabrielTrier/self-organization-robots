'''
@authors 
Rayane Bouaita
Gabriel Trier
Pierre El Anati

Groupe 21

@date 11/03/2025
'''

import random
import mesa

class Radioactivity(mesa.Agent):
    def __init__(self, model, zone):
        super().__init__(model)
        self.zone = zone
        if zone == 'z1':
            self.radioactivity_level = random.uniform(0, 0.33)
        elif zone == 'z2':
            self.radioactivity_level = random.uniform(0.33, 0.66)
        else:  # zone == 'z3'
            self.radioactivity_level = random.uniform(0.66, 1)

class WasteDisposal(mesa.Agent):
    def __init__(self, model):
        super().__init__(model)
        self.radioactivity_level = 1.0 
        self.zone = 'waste_zone'  

class Waste(mesa.Agent):
    """Agent representing waste objects"""
    def __init__(self, model, waste_type):
        super().__init__(model)
        self.waste_type = waste_type  # 'green', 'yellow', or 'red'

