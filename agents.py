'''
@authors 
Rayane Bouaita
Gabriel Trier
Pierre El Anati

Groupe 21

@date 11/03/2025
'''

import mesa
from objects import Waste

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

        print(f"[DEBUG] Percepts de l'agent {self.unique_id} à {self.pos} : {percepts}")

        return percepts

    def deliberate(self, knowledge):
        percepts = knowledge["percepts"]
        
        # Rechercher les cases contenant un déchet
        for pos, agents in percepts.items():
            for agent in agents:
                if agent.__class__.__name__ == "Waste":  # Vérifie si c'est un déchet
                    return {"action": "move", "target": pos}  # Aller vers cette case

        # Si aucun déchet détecté, continuer avec le comportement normal
        return {"action": "move"}
    
    def step_agent(self):
        percepts = self.get_percepts()
        print(f"[DEBUG] L'agent {self.unique_id} perçoit : {percepts}")

        zone_width = self.model.width // 3
        self.knowledge = {
            "percepts": percepts,
            "inventory": self.inventory.copy(),
            "pos": self.pos,
            "zone_width": zone_width
        }

        action = self.deliberate(self.knowledge)
        print(f"[DEBUG] Action décidée : {action}")

        new_percepts = None  # Initialisation pour éviter l'erreur

        if action["action"] == "move" and "target" in action:
            print(f"[DEBUG] L'agent {self.unique_id} se déplace vers {action['target']}")
            self.model.grid.move_agent(self, action["target"])
            self.knowledge["last_percepts"] = self.get_percepts()  # Mise à jour immédiate
        else:
            new_percepts = self.model.do(self, action)
            self.knowledge["last_percepts"] = new_percepts

        if action["action"] == "drop":
            self.hasTransformed = False  # Permet au robot de refaire une transformation après dépôt
            print(f"[DEBUG] L'agent {self.unique_id} a déposé un déchet et peut transformer à nouveau.")


        # Si new_percepts n'a pas été mis à jour dans le if, lui donner une valeur par défaut
        if new_percepts is None:
            new_percepts = self.get_percepts()

class GreenRobot(RobotAgent):
    def __init__(self, model,pos):
        super().__init__(model)
        self.type = "green"
        self.allowed_zones = ["z1"]
        self.hasTransformed = False

    def deliberate(self, knowledge):
        current_cell = knowledge["percepts"][knowledge["pos"]]
        inventory = knowledge["inventory"]
        pos = knowledge["pos"]
        zone_width = knowledge["zone_width"]

        waste_in_cell = any(isinstance(obj, Waste) for obj in current_cell)

        # Vérifier s'il y a un déchet adjacent
        for neighbor_pos, agents in knowledge["percepts"].items():
            for agent in agents:
                if isinstance(agent, Waste) and getattr(agent, "waste_type", None) == "green" and (not waste_in_cell) and (len([w for w in inventory if w == "green"]) < 2 and len([w for w in inventory if w == "yellow"]) == 0):  # Si un déchet est trouvé
                    print(f"[DEBUG] Déchet détecté à {neighbor_pos}, déplacement prioritaire.")
                    return {"action": "move", "target": neighbor_pos}  # Aller sur la case du déchet

        # Vérifier si l'agent est déjà sur une case contenant un déchet
        if waste_in_cell:
            green_waste = any(hasattr(obj, "waste_type") and obj.waste_type == "green" for obj in current_cell)
            if green_waste and len([w for w in inventory if w == "green"]) < 2:
                return {"action": "pickup", "waste": "green"}

        # Transformation si possible
        if not self.hasTransformed:
            if len([w for w in inventory if w == "green"]) >= 2:
                self.hasTransformed = True  # Empêche une nouvelle transformation
                return {"action": "transform", "from": "green", "to": "yellow"}


        if self.hasTransformed or len([w for w in inventory if w == "yellow"]) == 1:
            if pos[0] == zone_width - 1:  # À l'extrémité de z1
                if not waste_in_cell:
                    return {"action": "drop", "waste": "yellow"}
                else:
                    return {"action": "move_vertical"}
            else:
                return {"action": "move_east"}

        return {"action": "move"}  # Si rien d'autre à faire, continuer à bouger
        
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

        waste_in_cell = any(isinstance(obj, Waste) for obj in current_cell)

        # Vérifier s'il y a un déchet adjacent
        for neighbor_pos, agents in knowledge["percepts"].items():
            for agent in agents:
                if isinstance(agent, Waste) and getattr(agent, "waste_type", None) == "yellow" \
                        and (not waste_in_cell) and (len([w for w in inventory if w == "yellow"]) < 2 and len([w for w in inventory if w == "red"]) == 0):
                    print(f"[DEBUG] Déchet détecté à {neighbor_pos}, déplacement prioritaire.")
                    return {"action": "move", "target": neighbor_pos}  # Aller sur la case du déchet

        # Vérifier si l'agent est déjà sur une case contenant un déchet
        if waste_in_cell:
            yellow_waste = any(hasattr(obj, "waste_type") and obj.waste_type == "yellow" for obj in current_cell)
            if yellow_waste and len([w for w in inventory if w == "yellow"]) < 2:
                return {"action": "pickup", "waste": "yellow"}

        # Transformation si possible
        if not self.hasTransformed:
            if len([w for w in inventory if w == "yellow"]) >= 2:
                self.hasTransformed = True  # Empêche une nouvelle transformation
                return {"action": "transform", "from": "yellow", "to": "red"}

        # Dépôt si transformé ou si un déchet rouge est dans l'inventaire
        if self.hasTransformed or len([w for w in inventory if w == "red"]) == 1:
            if pos[0] == (2*zone_width) - 1:  # À l'extrémité de la zone
                if not waste_in_cell:
                    return {"action": "drop", "waste": "red"}
                else:
                    return {"action": "move_vertical"}
            else:
                return {"action": "move_east"}

        return {"action": "move"}  # Si rien d'autre à faire, continuer à bouger
        
class RedRobot(RobotAgent):
    def __init__(self, model, pos):
        super().__init__(model)
        self.type = "red"  
        self.allowed_zones = ["z1", "z2", "z3"]
    
    def deliberate(self, knowledge):
        current_cell = knowledge["percepts"][knowledge["pos"]]
        inventory = knowledge["inventory"]

        waste_in_cell = any(isinstance(obj, Waste) for obj in current_cell)

        for neighbor_pos, agents in knowledge["percepts"].items():
            for agent in agents:
                if isinstance(agent, Waste) and getattr(agent, "waste_type", None) == "red" \
                        and (not waste_in_cell) and (len([w for w in inventory if w == "red"]) < 2 and len([w for w in inventory if w == "red"]) == 0):
                    print(f"[DEBUG] Déchet détecté à {neighbor_pos}, déplacement prioritaire.")
                    return {"action": "move", "target": neighbor_pos}  # Aller sur la case du déchet

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