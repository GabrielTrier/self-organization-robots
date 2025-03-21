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
        self.knowledge = {} 
        self.inventory = []
    def move(self):
        possible_steps = self.model.grid.get_neighborhood(
        self.pos, moore=False, include_center=False)
        allowed_steps = []
        for pos in possible_steps:
            # Récupérer le contenu de la cellule
            cell_contents = self.model.grid.get_cell_list_contents(pos)
            #Chercher l'agent Radioactivity dans la cellule
            zone = None
            for agent in cell_contents:
                #On vérifie que l'agent est une instance de Radioactivity
                if hasattr(agent, "zone") and agent.__class__.__name__ == "Radioactivity":
                    zone = agent.zone
                    break
            
            #Vérifier si la zone de la cellule est autorisée pour cet agent
            if zone in self.allowed_zones:
                allowed_steps.append(pos)
                
        #Effectuer le déplacement vers une case autorisée si disponible
        if allowed_steps:
            new_position = self.random.choice(allowed_steps)
            self.model.grid.move_agent(self, new_position)

    def step(self):
        self.step_agent()

    def get_percepts(self):
        percepts = {}
        neighbors = self.model.grid.get_neighborhood(self.pos, moore=False, include_center=False)
        for pos in neighbors:
            percepts[pos] = self.model.grid.get_cell_list_contents(pos)
        return percepts

    def deliberate(self, knowledge):
        return {"action": "move"}

    def step_agent(self):
        # Phase de perception
        percepts = self.get_percepts()
        self.knowledge["percepts"] = percepts

        # Phase de délibération : l'agent décide de l'action à effectuer
        action = self.deliberate(self.knowledge)

        # Phase d'action : le modèle exécute l'action et renvoie les percepts mis à jour
        new_percepts = self.model.do(self, action)
        self.knowledge["last_percepts"] = new_percepts

class GreenRobot(RobotAgent):
    def __init__(self, model,pos):
        super().__init__(model)
        self.type = "green"
        self.allowed_zones = ["z1"]

    def deliberate(self, knowledge):

        # Récupérer les objets dans la cellule courante
        current_cell = self.model.grid.get_cell_list_contents(self.pos)
        green_present = any(hasattr(obj, "waste_type") and obj.waste_type == "green" for obj in current_cell)

        if len([w for w in self.inventory if w == "green"]) < 2 and green_present:
            return {"action": "pickup", "waste": "green"}
        elif len([w for w in self.inventory if w == "green"]) >= 2:
            return {"action": "transform", "from": "green", "to": "yellow"}
        elif "yellow" in self.inventory:
            return {"action": "move_east"}
        else:
            return {"action": "move"}
        
class YellowRobot(RobotAgent):
    def __init__(self, model, pos):
        super().__init__(model)
        self.type = "yellow" 
        self.allowed_zones = ["z1", "z2"]

class RedRobot(RobotAgent):
    def __init__(self, model, pos):
        super().__init__(model)
        self.type = "red"  
        self.allowed_zones = ["z1", "z2", "z3"]