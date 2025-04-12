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

        if not hasattr(self, "direction_x"):
            self.direction_x = 1  # 1 pour droite, -1 pour gauche
        if not hasattr(self, "direction_y"):
            self.direction_y = 1  # 1 pour descendre, -1 pour monter

        # Déplacement horizontal
        new_x = x + self.direction_x
        new_y = y

        if new_x < x_min or new_x > x_max:
            # On atteint un bord horizontal : on change de ligne
            self.direction_x *= -1  # On inverse le sens horizontal
            new_x = x  # On reste sur la même colonne pour ce tick
            new_y = y + self.direction_y

            # Si on atteint un bord vertical, on inverse aussi la direction verticale
            if new_y < y_min or new_y > y_max:
                self.direction_y *= -1
                new_y = y + self.direction_y

        new_pos = (new_x, new_y)
        cell_contents = self.model.grid.get_cell_list_contents(new_pos)
        if not any(isinstance(obj, RobotAgent) for obj in cell_contents):
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
        self.hasAWaste = False

    def deliberate(self, knowledge):
        current_cell = knowledge["percepts"][knowledge["pos"]]
        inventory = knowledge["inventory"]
        pos = knowledge["pos"]
        zone_width = knowledge["zone_width"]

        waste_in_cell = any(isinstance(obj, Waste) for obj in current_cell)

        # Vérifier si l'agent est déjà sur une case contenant un déchet
        if waste_in_cell and pos[0] != zone_width - 1:
            green_waste = any(hasattr(obj, "waste_type") and obj.waste_type == "green" for obj in current_cell)
            if green_waste and len([w for w in inventory if w == "green"]) < 1:
                self.hasAWaste = True
                return {"action": "pickup", "waste": "green"}

        if self.hasAWaste:
        #or len([w for w in inventory if w == "yellow"]) == 1:
            if pos[0] == zone_width - 1:  # À l'extrémité de z1
                if not waste_in_cell:
                    self.hasAWaste = False
                    return {"action": "drop", "waste": "green"}
                else:
                    return {"action": "move_vertical"}
            else:
                return {"action": "move_east"}

        return {"action": "move"}  # Si rien d'autre à faire, continuer à bouger


class GreenGather(GreenRobot):
    def __init__(self, unique_id, model,pos, assigned_zone=None):
        super().__init__(unique_id, model, pos, assigned_zone)
        self.hasTransformed = False

    def deliberate(self, knowledge):
        current_cell = knowledge["percepts"][knowledge["pos"]]
        inventory = knowledge["inventory"]
        pos = knowledge["pos"]
        zone_width = knowledge["zone_width"]

        waste_in_cell = any(isinstance(obj, Waste) for obj in current_cell)

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

    def move(self):
        if not self.assigned_zone:
            raise ValueError(f"Robot {self.unique_id} n'a pas de zone assignée.")

        x, y = self.pos
        _, _, y_min, y_max = self.assigned_zone

        if not hasattr(self, "direction_y"):
            self.direction_y = 1  # 1 pour descendre, -1 pour monter

        # Déplacement uniquement vertical
        new_y = y + self.direction_y

        # Si on atteint un bord vertical, on inverse la direction
        if new_y < y_min or new_y > y_max:
            self.direction_y *= -1
            new_y = y + self.direction_y

        new_pos = (x, new_y)
        cell_contents = self.model.grid.get_cell_list_contents(new_pos)
        if not any(isinstance(obj, RobotAgent) for obj in cell_contents):
            self.model.grid.move_agent(self, new_pos)
            self.distance += 1

class AloneGreen(GreenGather):
    def move(self):
        if not self.assigned_zone:
            raise ValueError(f"Robot {self.unique_id} n'a pas de zone assignée.")

        x, y = self.pos
        x_min, x_max, y_min, y_max = self.assigned_zone

        if not hasattr(self, "direction_x"):
            self.direction_x = 1  # 1 pour droite, -1 pour gauche
        if not hasattr(self, "direction_y"):
            self.direction_y = 1  # 1 pour descendre, -1 pour monter

        # Déplacement horizontal
        new_x = x + self.direction_x
        new_y = y

        if new_x < x_min or new_x > x_max:
            # On atteint un bord horizontal : on change de ligne
            self.direction_x *= -1  # On inverse le sens horizontal
            new_x = x  # On reste sur la même colonne pour ce tick
            new_y = y + self.direction_y

            # Si on atteint un bord vertical, on inverse aussi la direction verticale
            if new_y < y_min or new_y > y_max:
                self.direction_y *= -1
                new_y = y + self.direction_y

        new_pos = (new_x, new_y)
        cell_contents = self.model.grid.get_cell_list_contents(new_pos)
        if not any(isinstance(obj, RobotAgent) for obj in cell_contents):
            self.model.grid.move_agent(self, new_pos)
            self.distance += 1


class YellowRobot(RobotAgent):
    def __init__(self, unique_id, model,pos, assigned_zone=None):
        super().__init__(unique_id, model, pos, assigned_zone)
        self.type = "yellow"
        self.allowed_zones = ["z2"]
        self.hasAWaste = False

    def deliberate(self, knowledge):
        current_cell = knowledge["percepts"][knowledge["pos"]]
        inventory = knowledge["inventory"]
        pos = knowledge["pos"]
        zone_width = knowledge["zone_width"]

        waste_in_cell = any(isinstance(obj, Waste) for obj in current_cell)

        # Vérifier si l'agent est déjà sur une case contenant un déchet
        if waste_in_cell and pos[0] != zone_width*2 - 1:
            yellow_waste = any(hasattr(obj, "waste_type") and obj.waste_type == "yellow" for obj in current_cell)
            if yellow_waste and len([w for w in inventory if w == "yellow"]) < 1:
                self.hasAWaste = True
                return {"action": "pickup", "waste": "yellow"}

        if self.hasAWaste:
        #or len([w for w in inventory if w == "yellow"]) == 1:
            if pos[0] >= zone_width * 2 - 1:  # À l'extrémité de z2
                if not waste_in_cell:
                    self.hasAWaste = False
                    return {"action": "drop", "waste": "yellow"}
                else:
                    return {"action": "move_vertical"}
            else:
                return {"action": "move_east"}

        return {"action": "move"}  # Si rien d'autre à faire, continuer à bouger
    
class YellowGather(YellowRobot):
    def __init__(self, unique_id, model,pos, assigned_zone=None):
        super().__init__(unique_id, model, pos, assigned_zone)
        self.hasTransformed = False

    def deliberate(self, knowledge):
        current_cell = knowledge["percepts"][knowledge["pos"]]
        inventory = knowledge["inventory"]
        pos = knowledge["pos"]
        zone_width = knowledge["zone_width"]

        waste_in_cell = any(isinstance(obj, Waste) for obj in current_cell)

        # Vérifier si l'agent est déjà sur une case contenant un déchet
        if waste_in_cell:
            green_waste = any(hasattr(obj, "waste_type") and obj.waste_type == "yellow" for obj in current_cell)
            if green_waste and len([w for w in inventory if w == "yellow"]) < 2:
                return {"action": "pickup", "waste": "yellow"}

        # Transformation si possible
        if not self.hasTransformed:
            if len([w for w in inventory if w == "yellow"]) >= 2:
                self.hasTransformed = True  # Empêche une nouvelle transformation
                return {"action": "transform", "from": "yellow", "to": "red"}


        if self.hasTransformed or len([w for w in inventory if w == "red"]) == 1:
            if pos[0] == zone_width*2 - 1:  # À l'extrémité de z1
                if not waste_in_cell:
                    return {"action": "drop", "waste": "red"}
                else:
                    return {"action": "move_vertical"}
            else:
                return {"action": "move_east"}

        return {"action": "move"}  # Si rien d'autre à faire, continuer à bouger
    
    def move(self):
        if not self.assigned_zone:
            raise ValueError(f"Robot {self.unique_id} n'a pas de zone assignée.")

        x, y = self.pos
        _, _, y_min, y_max = self.assigned_zone

        if not hasattr(self, "direction_y"):
            self.direction_y = 1  # 1 pour descendre, -1 pour monter

        # Déplacement uniquement vertical
        new_y = y + self.direction_y

        # Si on atteint un bord vertical, on inverse la direction
        if new_y < y_min or new_y > y_max:
            self.direction_y *= -1
            new_y = y + self.direction_y

        new_pos = (x, new_y)
        cell_contents = self.model.grid.get_cell_list_contents(new_pos)
        if not any(isinstance(obj, RobotAgent) for obj in cell_contents):
            self.model.grid.move_agent(self, new_pos)
            self.distance += 1

class AloneYellow(YellowGather):
    def move(self):
        if not self.assigned_zone:
            raise ValueError(f"Robot {self.unique_id} n'a pas de zone assignée.")

        x, y = self.pos
        x_min, x_max, y_min, y_max = self.assigned_zone

        if not hasattr(self, "direction_x"):
            self.direction_x = 1  # 1 pour droite, -1 pour gauche
        if not hasattr(self, "direction_y"):
            self.direction_y = 1  # 1 pour descendre, -1 pour monter

        # Déplacement horizontal
        new_x = x + self.direction_x
        new_y = y

        if new_x < x_min or new_x > x_max:
            # On atteint un bord horizontal : on change de ligne
            self.direction_x *= -1  # On inverse le sens horizontal
            new_x = x  # On reste sur la même colonne pour ce tick
            new_y = y + self.direction_y

            # Si on atteint un bord vertical, on inverse aussi la direction verticale
            if new_y < y_min or new_y > y_max:
                self.direction_y *= -1
                new_y = y + self.direction_y

        new_pos = (new_x, new_y)
        cell_contents = self.model.grid.get_cell_list_contents(new_pos)
        if not any(isinstance(obj, RobotAgent) for obj in cell_contents):
            self.model.grid.move_agent(self, new_pos)
            self.distance += 1

class RedRobot(RobotAgent):
    def __init__(self, unique_id, model, pos, assigned_zone=None):
        super().__init__(unique_id, model, pos, assigned_zone)
        self.type = "red"  
        self.allowed_zones = ["z1", "z2", "z3"]

    
    def deliberate(self, knowledge):
        current_cell = knowledge["percepts"][knowledge["pos"]]
        inventory = knowledge["inventory"]

        waste_in_cell = any(isinstance(obj, Waste) for obj in current_cell)


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