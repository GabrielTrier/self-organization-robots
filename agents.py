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
        self.distance = 0

    def move(self):
        possible_steps = self.model.grid.get_neighborhood(
        self.pos, moore=False, include_center=False)
        allowed_steps = []
        for pos in possible_steps:
            cell_contents = self.model.grid.get_cell_list_contents(pos)

            if any(isinstance(obj, RobotAgent) for obj in cell_contents): #éviter collision
                continue

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
        neighbors = self.model.grid.get_neighborhood(self.pos, moore=False, include_center=True)
        for pos in neighbors:
            percepts[pos] = self.model.grid.get_cell_list_contents(pos)
        return percepts

    def deliberate(self, knowledge):
        return {"action": "move"}

    def step_agent(self):
        #Mise à jour knowledge avec les percepts, l'inventaire et la position
        percepts = self.get_percepts()
        zone_width = self.model.width // 3
        self.knowledge = {
            "percepts": percepts,
            "inventory": self.inventory.copy(),
            "pos": self.pos,
            "zone_width": zone_width
        }
        #Phase de délibération n'utilise QUE self.knowledge
        action = self.deliberate(self.knowledge)
        #modèle exécute l'action et renvoie les percepts mis à jour
        new_percepts = self.model.do(self, action)
        self.knowledge["last_percepts"] = new_percepts

class GreenRobot(RobotAgent):
    def __init__(self, model,pos):
        super().__init__(model)
        self.type = "green"
        self.allowed_zones = ["z1"]
        self.hasTransformed = False

    def deliberate(self, knowledge):
        current_cell = knowledge["percepts"] [knowledge["pos"]]
        inventory = knowledge["inventory"]
        pos = knowledge["pos"]
        zone_width = knowledge["zone_width"]

        if not self.hasTransformed:
            green_present = any(hasattr(obj, "waste_type") and obj.waste_type == "green" for obj in current_cell)
            if len([w for w in inventory if w == "green"]) < 2 and green_present:
                return {"action": "pickup", "waste": "green"}
            elif len([w for w in inventory if w == "green"]) >= 2:
                return {"action": "transform", "from": "green", "to": "yellow"}

        if self.hasTransformed or len([w for w in inventory if w == "yellow"]) == 1:
            waste_in_cell = any(hasattr(obj, "waste_type") for obj in current_cell)
            if pos[0] == zone_width - 1:  # À l'extrémité de z1
                if not waste_in_cell:
                    return {"action": "drop", "waste": "yellow"}
                else:
                    return {"action": "move_vertical"}
            else:
                return {"action": "move_east"}
            
        return {"action": "move"}
        
class YellowRobot(RobotAgent):
    def __init__(self, model, pos):
        super().__init__(model)
        self.type = "yellow" 
        self.allowed_zones = ["z1", "z2"]
        self.hasTransformed = False

    def deliberate(self, knowledge):
        current_cell = knowledge["percepts"][knowledge["pos"]]
        inventory = knowledge["inventory"]
        pos = knowledge["pos"]
        zone_width = knowledge["zone_width"]

        if not self.hasTransformed:
            yellow_present = any(hasattr(obj, "waste_type") and obj.waste_type == "yellow" for obj in current_cell)
            
            if len([w for w in inventory if w == "yellow"]) < 2 and yellow_present:
                return {"action": "pickup", "waste": "yellow"}
            
            elif len([w for w in inventory if w == "yellow"]) >= 2:
                return {"action": "transform", "from": "yellow", "to": "red"}
        
        if self.hasTransformed or len([w for w in inventory if w == "red"]) == 1:
            if pos[0] == 2 * zone_width - 1:
                waste_in_cell = any(hasattr(obj, "waste_type") for obj in current_cell)
                if not waste_in_cell:
                    return {"action": "drop", "waste": "red"}
                else:
                    return {"action": "move_vertical"}
            else:
                return {"action": "move_east"}
        return {"action": "move"}
        
class RedRobot(RobotAgent):
    def __init__(self, model, pos):
        super().__init__(model)
        self.type = "red"  
        self.allowed_zones = ["z1", "z2", "z3"]
    
    def deliberate(self, knowledge):
        current_cell = knowledge["percepts"][knowledge["pos"]]
        inventory = knowledge["inventory"]

        if len([w for w in inventory if w == "red"]) < 1:
            red_present = any(hasattr(obj, "waste_type") and obj.waste_type == "red" for obj in current_cell)
            if red_present:
                return {"action": "pickup", "waste": "red"}
            else:
                return {"action": "move"}
        else:
            waste_in_cell = any(hasattr(obj, "waste_type") for obj in current_cell)
            disposal_present = any(hasattr(obj, "zone") and obj.zone == "waste_zone" for obj in current_cell)
            if disposal_present and not waste_in_cell:
                return {"action": "drop", "waste": "red"}
            else:
                return {"action": "move_east"}