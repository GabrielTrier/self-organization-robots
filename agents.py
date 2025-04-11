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
    def __init__(self, unique_id, model, pos, assigned_zone=None):
        super().__init__(model)
        self.knowledge = {} 
        self.inventory = []
        self.distance = 0
        self.unique_id = unique_id
        self.pos = pos
        self.assigned_zone = assigned_zone

    def move(self):
        if not self.assigned_zone:
            raise ValueError(f"Robot {self.unique_id} n'a pas de zone assignée.")

        x, y = self.pos
        x_min, x_max, y_min, y_max = self.assigned_zone

        # Vérifier si le robot doit changer de ligne
        if not hasattr(self, "direction"):
            self.direction = 1  # 1 pour aller à droite, -1 pour aller à gauche

        # Déplacement horizontal
        new_x = x + self.direction
        if new_x < x_min or new_x > x_max:  # Si on atteint la limite horizontale
            new_x = x  # Rester sur la même colonne
            new_y = y + 1 if y + 1 <= y_max else y_min  # Passer à la ligne suivante ou revenir en haut
            self.direction *= -1  # Changer de direction
        else:
            new_y = y

        # Vérifier si la nouvelle position est libre
        new_pos = (new_x, new_y)
        cell_contents = self.model.grid.get_cell_list_contents(new_pos)
        if not any(isinstance(obj, RobotAgent) for obj in cell_contents):  # Éviter les collisions
            self.model.grid.move_agent(self, new_pos)
            self.distance += 1

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
        # Mise à jour knowledge avec les percepts, l'inventaire et la position
        percepts = self.get_percepts()
        zone_width = self.model.width // 3
        self.knowledge = {
            "percepts": percepts,
            "inventory": self.inventory.copy(),
            "pos": self.pos,
            "zone_width": zone_width,
        }
        action = self.deliberate(self.knowledge)
        new_percepts = self.model.do(self, action)
        self.knowledge["last_percepts"] = new_percepts

class GreenRobot(RobotAgent):
    def __init__(self, unique_id, model,pos, assigned_zone=None):
        super().__init__(unique_id, model, pos, assigned_zone)
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
    def __init__(self, unique_id, model, pos, assigned_zone=None):
        super().__init__(unique_id, model, pos, assigned_zone)
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
    def __init__(self, unique_id, model, pos, assigned_zone=None):
        super().__init__(unique_id, model, pos, assigned_zone)
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