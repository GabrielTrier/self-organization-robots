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
from CommunicatingAgent import CommunicatingAgent
from MessagePerformative import MessagePerformative
from Message import Message

class RobotAgent(CommunicatingAgent):
    def __init__(self, unique_id, model, pos, assigned_zone=None):
        super().__init__(model, f"Robot_{unique_id}")
        self.knowledge = {} 
        self.inventory = []
        self.distance = 0
        self.unique_id = unique_id
        self.pos = pos
        self.assigned_zone = assigned_zone
        self.last_dropped_waste_id = None  # ID du dernier déchet déposé à ignorer
        self._last_notified_target = None  # Pour éviter des notifications dupliquées
        self.type = None  # Sera défini dans les sous-classes

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

        # Vérifier que la nouvelle position est dans les limites de la grille
        grid_width, grid_height = self.model.width, self.model.height
        if not (0 <= new_x < grid_width and 0 <= new_y < grid_height):
            # Position hors limites, rester sur place et inverser la direction
            new_x, new_y = x, y
            self.direction_x *= -1
            self.direction_y *= -1

        new_pos = (new_x, new_y)
        cell_contents = self.model.grid.get_cell_list_contents(new_pos)
        if not any(isinstance(obj, RobotAgent) for obj in cell_contents):
            self.model.grid.move_agent(self, new_pos)
            self.distance += 1

    def step(self):
        self.process_messages()
        self.step_agent()
    
    def get_percepts(self):
        percepts = {}
        neighbors = self.model.grid.get_neighborhood(self.pos, moore=False, include_center=True)
        for pos in neighbors:
            percepts[pos] = self.model.grid.get_cell_list_contents(pos)

        # print(f"[DEBUG] Percepts de l'agent {self.unique_id} à {self.pos} : {percepts}")

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
        
        # Préserver les waste_locations existantes
        waste_locations = self.knowledge.get("waste_locations", [])

        # Mise à jour des connaissances
        self.knowledge.update({
            "percepts": percepts,
            "inventory": self.inventory.copy(),
            "pos": self.pos,
            "zone_width": zone_width,
        })
        
        # Restaurer les waste_locations
        if waste_locations:
            self.knowledge["waste_locations"] = waste_locations
            
        # Délibération et action après avoir traité les messages (déjà fait dans step)
        action = self.deliberate(self.knowledge)
        new_percepts = self.model.do(self, action)
        self.knowledge["last_percepts"] = new_percepts

    def process_messages(self):
        """Méthode de base: vide simplement la boîte aux lettres sans traiter les messages"""
        self.get_new_messages()
        return 

    def send_doing_notification(self, waste_pos, waste_type):
        """Envoie une notification DOING aux autres robots du même type"""
        # Éviter d'envoyer des notifications dupliquées pour la même cible
        if self._last_notified_target == waste_pos:
            return
        
        self._last_notified_target = waste_pos
        
        content = {
            "waste_pos": waste_pos,
            "waste_type": waste_type,
            "agent_pos": self.pos
        }
        
        # Envoie le message à tous les robots du même type, sauf lui-même
        for agent in self.model.robots:
            if hasattr(agent, 'type') and agent.type == self.type and agent != self:
                message = Message(
                    self.get_name(),
                    agent.get_name(),
                    MessagePerformative.DOING,
                    content
                )
                self.send_message(message)
                print(f"[DOING] {self.get_name()} is targeting {waste_type} waste at {waste_pos}")

class GreenRobot(RobotAgent):
    def __init__(self, unique_id, model, pos, assigned_zone=None):
        super().__init__(unique_id, model, pos, assigned_zone)
        self.type = "green"
        self.allowed_zones = ["z1"]
        self.hasAWaste = False
        self.blocked_steps = 0  # Compteur de blocage

    def deliberate(self, knowledge):
        percepts = knowledge["percepts"]
        current_cell = percepts[knowledge["pos"]]
        inventory = knowledge["inventory"]
        pos = knowledge["pos"]
        zone_width = knowledge["zone_width"]
        
        # Si j'ai déjà un déchet vert, je le dépose directement sans chercher d'autres déchets
        if len([w for w in inventory if w == "green"]) > 0:
            self.hasAWaste = True
            if pos[0] == zone_width - 1:  # À l'extrémité de z1
                # Vérifier s'il y a des déchets dans la cellule actuelle
                cell_has_waste = any(hasattr(obj, "waste_type") for obj in current_cell)
                if not cell_has_waste:
                    self.hasAWaste = False
                    return {"action": "drop", "waste": "green"}
                else:
                    return {"action": "move_vertical"}
            else:
                # Vérifier si on peut se déplacer vers l'est
                east_pos = (pos[0] + 1, pos[1])
                if east_pos[0] < self.model.width:
                    east_cell = self.model.grid.get_cell_list_contents(east_pos)
                    if any(isinstance(obj, RobotAgent) for obj in east_cell):
                        return {"action": "move_vertical"}  # Alternative si bloqué
                return {"action": "move_east"}
        
        # Si je n'ai pas de déchet, j'essaie d'en ramasser un
        green_wastes = [obj for obj in current_cell if hasattr(obj, "waste_type") 
                    and obj.waste_type == "green" 
                    and obj.unique_id != self.last_dropped_waste_id]
        
        valid_waste_in_cell = len(green_wastes) > 0
        
        if valid_waste_in_cell and pos[0] != zone_width - 1:
            self.hasAWaste = True
            return {"action": "pickup", "waste": "green"}

        # Si je n'ai pas de déchet et qu'il n'y en a pas sur ma case, je cherche autour
        for nearby_pos, agents in percepts.items():
            if hasattr(self, "ignore_last_column") and nearby_pos[0] == self.deposit_column:
                continue
            if nearby_pos != pos:
                for agent in agents:
                    if hasattr(agent, "waste_type") and agent.waste_type == "green":
                        cell_contents = self.model.grid.get_cell_list_contents(nearby_pos)
                        allowed = False
                        for obj in cell_contents:
                            if hasattr(obj, "zone") and obj.zone in self.allowed_zones:
                                allowed = True
                        if allowed:
                            return {"action": "move", "target": nearby_pos}

        return {"action": "move"}

    # Surcharger pour les robots verts pour ne pas traiter les messages
    def process_messages(self):
        self.get_new_messages()  # Vider la boîte aux lettres sans traiter les messages
        return

    # Override la méthode move de RobotAgent pour gérer les blocages
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

        # S'assurer que new_x reste strictement dans la zone assignée
        if new_x < x_min or new_x > x_max:
            # On atteint un bord horizontal : on change de ligne
            self.direction_x *= -1  # On inverse le sens horizontal
            new_x = x  # On reste sur la même colonne pour ce tick
            new_y = y + self.direction_y

            # S'assurer que new_y reste strictement dans la zone assignée
            if new_y < y_min or new_y > y_max:
                self.direction_y *= -1
                new_y = y + self.direction_y
                
                # Double vérification que new_y est dans les limites
                if new_y < y_min or new_y > y_max:
                    new_y = y  # Rester sur place si toujours hors limites

        # Vérification finale que la position est dans les limites de la grille ET de la zone
        grid_width, grid_height = self.model.width, self.model.height
        if not (0 <= new_x < grid_width and 0 <= new_y < grid_height):
            new_x, new_y = x, y
            self.direction_x *= -1
            self.direction_y *= -1
            
        # Vérification supplémentaire que la position est dans la zone assignée
        if not (x_min <= new_x <= x_max and y_min <= new_y <= y_max):
            new_x, new_y = x, y  # Rester sur place si hors zone
            print(f"[WARNING] {self.get_name()} tente de sortir de sa zone: pos={new_x,new_y}, zone={x_min,x_max,y_min,y_max}")
            self.direction_x *= -1
            self.direction_y *= -1

        new_pos = (new_x, new_y)
        cell_contents = self.model.grid.get_cell_list_contents(new_pos)
        
        if not any(isinstance(obj, RobotAgent) for obj in cell_contents):
            # Déplacement effectif, réinitialiser le compteur de blocage
            self.model.grid.move_agent(self, new_pos)
            self.distance += 1
            self.blocked_steps = 0
        else:
            # Blocage détecté, incrémenter le compteur
            self.blocked_steps += 1
            print(f"[INFO] {self.get_name()} bloqué depuis {self.blocked_steps} steps à {self.pos}.")

            # Si bloqué depuis plus de 5 steps, tenter un mouvement alternatif
            if self.blocked_steps > 5:
                print(f"[INFO] {self.get_name()} tente un mouvement alternatif.")
                
                # Essayer plusieurs directions alternatives
                alternatives = []
                
                # Option 1: Reculer de 2 cases horizontalement
                alt_x = max(x_min, min(x_max, x - 2 * self.direction_x))
                alternatives.append((alt_x, y))
                
                # Option 2: Monter d'une case
                alt_y_up = max(y_min, y - 1)
                alternatives.append((x, alt_y_up))
                
                # Option 3: Descendre d'une case
                alt_y_down = min(y_max, y + 1)
                alternatives.append((x, alt_y_down))
                
                # Essayer chaque alternative dans l'ordre
                for alt_pos in alternatives:
                    # Vérifier que la position est valide (dans la grille et dans la zone)
                    if (0 <= alt_pos[0] < grid_width and 0 <= alt_pos[1] < grid_height and
                        x_min <= alt_pos[0] <= x_max and y_min <= alt_pos[1] <= y_max):
                        alt_cell_contents = self.model.grid.get_cell_list_contents(alt_pos)
                        if not any(isinstance(obj, RobotAgent) for obj in alt_cell_contents):
                            print(f"[INFO] {self.get_name()} se déplace en position alternative {alt_pos}.")
                            self.model.grid.move_agent(self, alt_pos)
                            self.distance += 1
                            self.blocked_steps = 0
                            break


class GreenGather(GreenRobot):
    def __init__(self, unique_id, model, pos, assigned_zone=None):
        super().__init__(unique_id, model, pos, assigned_zone)
        self.hasTransformed = False

    def deliberate(self, knowledge):
        current_cell = knowledge["percepts"][knowledge["pos"]]
        inventory = knowledge["inventory"]
        pos = knowledge["pos"]
        zone_width = knowledge["zone_width"]

        # Vérifier si l'agent est déjà sur une case contenant un déchet valide
        green_wastes = [obj for obj in current_cell if hasattr(obj, "waste_type") 
                       and obj.waste_type == "green" 
                       and obj.unique_id != self.last_dropped_waste_id]
        
        # Ne considérer qu'il y a un déchet valide que si la liste filtrée n'est pas vide
        valid_waste_in_cell = len(green_wastes) > 0
        
        if valid_waste_in_cell and len([w for w in inventory if w == "green"]) < 2:
            return {"action": "pickup", "waste": "green"}

        # Transformation si possible
        if not self.hasTransformed:
            if len([w for w in inventory if w == "green"]) >= 2:
                self.hasTransformed = True  # Empêche une nouvelle transformation
                return {"action": "transform", "from": "green", "to": "yellow"}

        # Vérifier s'il y a des déchets dans la cellule actuelle
        cell_has_waste = any(hasattr(obj, "waste_type") for obj in current_cell)
        
        if self.hasTransformed or len([w for w in inventory if w == "yellow"]) == 1:
            if pos[0] == zone_width - 1:  # À l'extrémité de z1
                if not cell_has_waste:
                    return {"action": "drop", "waste": "yellow"}
                else:
                    return {"action": "move_vertical"}
            else:
                return {"action": "move_east"}

        return {"action": "move"}  

    def move(self):
        if not self.assigned_zone:
            raise ValueError(f"Robot {self.unique_id} n'a pas de zone assignée.")

        x, y = self.pos
        x_min, x_max, y_min, y_max = self.assigned_zone  # Récupérer toutes les bornes de la zone

        if not hasattr(self, "direction_y"):
            self.direction_y = 1  # 1 pour descendre, -1 pour monter

        # Déplacement uniquement vertical
        new_y = y + self.direction_y

        # S'assurer que new_y reste strictement dans la zone assignée
        if new_y < y_min or new_y > y_max:
            self.direction_y *= -1
            new_y = y + self.direction_y
            
            # Double vérification
            if new_y < y_min or new_y > y_max:
                new_y = y  # Rester sur place si toujours hors limites

        # Vérification finale que la position est dans les limites de la grille
        grid_height = self.model.height
        if not (0 <= new_y < grid_height):
            new_y = y
            self.direction_y *= -1
            
        # Vérification supplémentaire que la position reste dans la colonne assignée
        if x < x_min or x > x_max:
            print(f"[CRITICAL] {self.get_name()} hors de sa colonne assignée: x={x}, zone={x_min}-{x_max}")
            # Corriger la position pour revenir dans la zone
            x = max(x_min, min(x_max, x))

        new_pos = (x, new_y)
        cell_contents = self.model.grid.get_cell_list_contents(new_pos)
        
        if not any(isinstance(obj, RobotAgent) for obj in cell_contents):
            self.model.grid.move_agent(self, new_pos)
            self.distance += 1
            self.blocked_steps = 0
        else:
            # Blocage détecté, incrémenter le compteur
            self.blocked_steps += 1
            print(f"[INFO] {self.get_name()} bloqué depuis {self.blocked_steps} steps.")

            # Si bloqué depuis plus de 5 steps, tenter un mouvement alternatif
            if self.blocked_steps > 5:
                print(f"[INFO] {self.get_name()} tente un mouvement alternatif.")
                
                # Inverser complètement la direction verticale et essayer de se déplacer
                self.direction_y *= -1
                alt_y = y + self.direction_y
                
                # Vérifier que la position alternative est valide (dans la zone et la grille)
                if y_min <= alt_y <= y_max and 0 <= alt_y < grid_height:
                    alt_pos = (x, alt_y)
                    alt_cell_contents = self.model.grid.get_cell_list_contents(alt_pos)
                    if not any(isinstance(obj, RobotAgent) for obj in alt_cell_contents):
                        print(f"[INFO] {self.get_name()} se déplace en position alternative {alt_pos}.")
                        self.model.grid.move_agent(self, alt_pos)
                        self.distance += 1
                        self.blocked_steps = 0
                    else:
                        # Si la première alternative échoue, essayer de s'arrêter temporairement
                        print(f"[INFO] {self.get_name()} reste sur place et attend.")
                        # Ne rien faire pendant ce tour pour laisser les autres se déplacer
                        # Le compteur continue d'augmenter pour une nouvelle tentative au prochain tour


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

            # S'assurer que new_y reste strictement dans la zone assignée
            if new_y < y_min or new_y > y_max:
                self.direction_y *= -1
                new_y = y + self.direction_y
                
                # Double vérification
                if new_y < y_min or new_y > y_max:
                    new_y = y  # Rester sur place si toujours hors limites

        grid_width, grid_height = self.model.width, self.model.height
        if not (0 <= new_x < grid_width and 0 <= new_y < grid_height):
            new_x, new_y = x, y
            self.direction_x *= -1
            self.direction_y *= -1
            
        if not (x_min <= new_x <= x_max and y_min <= new_y <= y_max):
            new_x, new_y = x, y  # Rester sur place si hors zone
            print(f"[WARNING] {self.get_name()} tente de sortir de sa zone: pos={new_x,new_y}, zone={x_min,x_max,y_min,y_max}")
            self.direction_x *= -1
            self.direction_y *= -1

        new_pos = (new_x, new_y)
        cell_contents = self.model.grid.get_cell_list_contents(new_pos)
        
        if not any(isinstance(obj, RobotAgent) for obj in cell_contents):
            self.model.grid.move_agent(self, new_pos)
            self.distance += 1
            self.blocked_steps = 0
        else:
            # Blocage détecté, incrémenter le compteur
            self.blocked_steps += 1
            print(f"[INFO] {self.get_name()} bloqué depuis {self.blocked_steps} steps.")

            # Si bloqué depuis plus de 5 steps, tenter un mouvement alternatif
            if self.blocked_steps > 5:
                print(f"[INFO] {self.get_name()} tente un mouvement alternatif.")
                
                # Essayer plusieurs directions alternatives
                alternatives = []
                
                # Option 1: Reculer de 2 cases horizontalement
                alt_x = max(x_min, min(x_max, x - 2 * self.direction_x))
                alternatives.append((alt_x, y))
                
                # Option 2: Monter d'une case
                alt_y_up = max(y_min, y - 1)
                alternatives.append((x, alt_y_up))
                
                # Option 3: Descendre d'une case
                alt_y_down = min(y_max, y + 1)
                alternatives.append((x, alt_y_down))
                
                # Essayer chaque alternative dans l'ordre
                for alt_pos in alternatives:
                    # Vérifier que la position est valide (dans la grille et dans la zone)
                    if (0 <= alt_pos[0] < grid_width and 0 <= alt_pos[1] < grid_height and
                        x_min <= alt_pos[0] <= x_max and y_min <= alt_pos[1] <= y_max):
                        alt_cell_contents = self.model.grid.get_cell_list_contents(alt_pos)
                        if not any(isinstance(obj, RobotAgent) for obj in alt_cell_contents):
                            print(f"[INFO] {self.get_name()} se déplace en position alternative {alt_pos}.")
                            self.model.grid.move_agent(self, alt_pos)
                            self.distance += 1
                            self.blocked_steps = 0
                            break

class YellowRobot(RobotAgent):
    def __init__(self, unique_id, model, pos, assigned_zone=None):
        super().__init__(unique_id, model, pos, assigned_zone)
        self._CommunicatingAgent__name = f"YellowRobot_{unique_id}"
        self.type = "yellow"
        self.allowed_zones = ["z2"]
        self.hasAWaste = False
        self.blocked_steps = 0  # Compteur de blocage
        # Vérifier que la position initiale est dans la zone assignée
        if assigned_zone:
            x_min, x_max, y_min, y_max = assigned_zone
            if not (x_min <= pos[0] <= x_max and y_min <= pos[1] <= y_max):
                print(f"[ERROR] YellowRobot_{unique_id} initialisé hors de sa zone: pos={pos}, zone={assigned_zone}")

    def deliberate(self, knowledge):
        percepts = knowledge["percepts"]
        current_cell = percepts[knowledge["pos"]]
        inventory = knowledge["inventory"]
        pos = knowledge["pos"]
        zone_width = knowledge["zone_width"]
        
        # Si j'ai déjà un déchet jaune, je le dépose directement sans chercher d'autres déchets
        if len([w for w in inventory if w == "yellow"]) > 0:
            self.hasAWaste = True
            if pos[0] >= zone_width * 2 - 1:  # À l'extrémité de z2
                cell_has_waste = any(hasattr(obj, "waste_type") for obj in current_cell)
                if not cell_has_waste:
                    self.hasAWaste = False
                    return {"action": "drop", "waste": "yellow"}
                else:
                    return {"action": "move_vertical"}
            else:
                # Vérifier si on peut se déplacer vers l'est
                east_pos = (pos[0] + 1, pos[1])
                # Vérifier que east_pos est dans ma zone assignée
                if self.assigned_zone:
                    x_min, x_max, y_min, y_max = self.assigned_zone
                    if not (x_min <= east_pos[0] <= x_max):
                        return {"action": "move_vertical"}  # Si hors zone, déplacement vertical

                if east_pos[0] < self.model.width:
                    east_cell = self.model.grid.get_cell_list_contents(east_pos)
                    if any(isinstance(obj, RobotAgent) for obj in east_cell):
                        return {"action": "move_vertical"}  # Alternative si bloqué
                return {"action": "move_east"}
        
        # Si je n'ai pas de déchet, j'essaie d'en ramasser un
        yellow_wastes = [obj for obj in current_cell if hasattr(obj, "waste_type") 
                        and obj.waste_type == "yellow" 
                        and obj.unique_id != self.last_dropped_waste_id]
        
        valid_waste_in_cell = len(yellow_wastes) > 0
        
        if valid_waste_in_cell and pos[0] != zone_width*2 - 1:
            self.hasAWaste = True
            return {"action": "pickup", "waste": "yellow"}

        # Si je n'ai pas de déchet et qu'il n'y en a pas sur ma case, je cherche autour
        for nearby_pos, agents in percepts.items():
            # Vérifier que la case voisine est dans ma zone assignée
            if self.assigned_zone:
                x_min, x_max, y_min, y_max = self.assigned_zone
                if not (x_min <= nearby_pos[0] <= x_max and y_min <= nearby_pos[1] <= y_max):
                    continue  # Ignorer les cases hors zone

            if hasattr(self, "ignore_last_column") and nearby_pos[0] == self.deposit_column:
                continue
            if nearby_pos != pos:
                for agent in agents:
                    if hasattr(agent, "waste_type") and agent.waste_type == "yellow":
                        cell_contents = self.model.grid.get_cell_list_contents(nearby_pos)
                        allowed = False
                        for obj in cell_contents:
                            if hasattr(obj, "zone") and obj.zone in self.allowed_zones:
                                allowed = True
                        if allowed:
                            return {"action": "move", "target": nearby_pos}

        return {"action": "move"}

    # Override la méthode move de RobotAgent pour gérer les blocages
    def move(self):
        if not self.assigned_zone:
            raise ValueError(f"Robot {self.unique_id} n'a pas de zone assignée.")

        x, y = self.pos
        x_min, x_max, y_min, y_max = self.assigned_zone

        # Vérifier que la position actuelle est dans la zone assignée
        if not (x_min <= x <= x_max and y_min <= y <= y_max):
            print(f"[ERROR] {self.get_name()} est hors de sa zone: pos={x,y}, zone={x_min,x_max,y_min,y_max}")
            # Tenter de corriger la position
            corrected_x = max(x_min, min(x_max, x))
            corrected_y = max(y_min, min(y_max, y))
            if (corrected_x, corrected_y) != (x, y):
                print(f"[CORRECTION] {self.get_name()} repositionné à {corrected_x, corrected_y}")
                self.model.grid.move_agent(self, (corrected_x, corrected_y))
                return  # Arrêter ici après correction

        if not hasattr(self, "direction_x"):
            self.direction_x = 1  # 1 pour droite, -1 pour gauche
        if not hasattr(self, "direction_y"):
            self.direction_y = 1  # 1 pour descendre, -1 pour monter

        # Calcul de la nouvelle position (horizontal)
        new_x = x + self.direction_x
        new_y = y

        # Vérification stricte des limites horizontales de la zone
        if new_x < x_min or new_x > x_max:
            # On atteint un bord horizontal : on change de ligne
            self.direction_x *= -1  # On inverse le sens horizontal
            new_x = x  # On reste sur la même colonne pour ce tick
            new_y = y + self.direction_y

            # Vérification stricte des limites verticales de la zone
            if new_y < y_min or new_y > y_max:
                self.direction_y *= -1
                new_y = y + self.direction_y
                
                # Double vérification
                if new_y < y_min or new_y > y_max:
                    new_y = y  # Rester sur place si toujours hors limites

        # Vérification que la position est dans les limites de la grille
        grid_width, grid_height = self.model.width, self.model.height
        if not (0 <= new_x < grid_width and 0 <= new_y < grid_height):
            new_x, new_y = x, y
            self.direction_x *= -1
            self.direction_y *= -1
            
        # Vérification FINALE de sécurité pour éviter toute sortie de zone
        if not (x_min <= new_x <= x_max and y_min <= new_y <= y_max):
            print(f"[WARNING] {self.get_name()} tente de sortir de sa zone: pos={new_x,new_y}, zone={x_min,x_max,y_min,y_max}")
            new_x = max(x_min, min(x_max, x))  # Forcer à rester dans la plage x
            new_y = max(y_min, min(y_max, y))  # Forcer à rester dans la plage y
            self.direction_x *= -1
            self.direction_y *= -1

        # Vérification finale que la nouvelle position est différente de la position actuelle
        if (new_x, new_y) == (x, y):
            # Essayer d'autres directions au lieu de rester immobile
            directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]  # Est, Ouest, Sud, Nord
            for dx, dy in directions:
                test_x, test_y = x + dx, y + dy
                if (x_min <= test_x <= x_max and y_min <= test_y <= y_max and 
                    0 <= test_x < grid_width and 0 <= test_y < grid_height):
                    new_x, new_y = test_x, test_y
                    break

        new_pos = (new_x, new_y)
        cell_contents = self.model.grid.get_cell_list_contents(new_pos)
        
        if not any(isinstance(obj, RobotAgent) for obj in cell_contents):
            # Déplacement effectif, réinitialiser le compteur de blocage
            self.model.grid.move_agent(self, new_pos)
            self.distance += 1
            self.blocked_steps = 0
        else:
            # Blocage détecté, incrémenter le compteur
            self.blocked_steps += 1
            print(f"[INFO] {self.get_name()} bloqué depuis {self.blocked_steps} steps à {self.pos}.")

            # Si bloqué depuis plus de 5 steps, tenter un mouvement alternatif
            if self.blocked_steps > 5:
                print(f"[INFO] {self.get_name()} tente un mouvement alternatif.")
                
                # Essayer plusieurs directions alternatives
                alternatives = []
                
                # Option 1: Reculer de 2 cases horizontalement (dans la zone)
                alt_x = max(x_min, min(x_max, x - 2 * self.direction_x))
                alternatives.append((alt_x, y))
                
                # Option 2: Monter d'une case (dans la zone)
                alt_y_up = max(y_min, min(y_max, y - 1))
                alternatives.append((x, alt_y_up))
                
                # Option 3: Descendre d'une case (dans la zone)
                alt_y_down = max(y_min, min(y_max, y + 1))
                alternatives.append((x, alt_y_down))
                
                # Essayer chaque alternative dans l'ordre
                for alt_pos in alternatives:
                    # Vérification rigoureuse que la position est valide
                    if (0 <= alt_pos[0] < grid_width and 0 <= alt_pos[1] < grid_height and
                        x_min <= alt_pos[0] <= x_max and y_min <= alt_pos[1] <= y_max):
                        alt_cell_contents = self.model.grid.get_cell_list_contents(alt_pos)
                        if not any(isinstance(obj, RobotAgent) for obj in alt_cell_contents):
                            print(f"[INFO] {self.get_name()} se déplace en position alternative {alt_pos}.")
                            self.model.grid.move_agent(self, alt_pos)
                            self.distance += 1
                            self.blocked_steps = 0
                            break


class YellowGather(YellowRobot):
    def __init__(self, unique_id, model, pos, assigned_zone=None):
        super().__init__(unique_id, model, pos, assigned_zone)
        self._CommunicatingAgent__name = f"YellowGather_{unique_id}"
        self.hasTransformed = False
        # Vérifier que la position initiale est correcte pour un YellowGather (doit être sur une colonne fixe)
        if assigned_zone:
            x_min, x_max, _, _ = assigned_zone
            if x_min != x_max:
                print(f"[WARNING] YellowGather devrait être sur une colonne fixe, mais la zone est {assigned_zone}")
    
    def deliberate(self, knowledge):
        current_cell = knowledge["percepts"][knowledge["pos"]]
        inventory = knowledge["inventory"]
        pos = knowledge["pos"]
        zone_width = knowledge["zone_width"]

        # Trouver tous les déchets jaunes dans la cellule qui ne sont pas le dernier déposé
        yellow_wastes = [obj for obj in current_cell if hasattr(obj, "waste_type") 
                        and obj.waste_type == "yellow" 
                        and obj.unique_id != self.last_dropped_waste_id]
        
        # Ne considérer qu'il y a un déchet valide que si la liste filtrée n'est pas vide
        valid_waste_in_cell = len(yellow_wastes) > 0
        
        if valid_waste_in_cell and len([w for w in inventory if w == "yellow"]) < 2:
            return {"action": "pickup", "waste": "yellow"}

        # Transformation si possible
        if not self.hasTransformed:
            if len([w for w in inventory if w == "yellow"]) >= 2:
                self.hasTransformed = True  # Empêche une nouvelle transformation
                return {"action": "transform", "from": "yellow", "to": "red"}

        # Vérifier s'il y a des déchets dans la cellule actuelle
        cell_has_waste = any(hasattr(obj, "waste_type") for obj in current_cell)

        if self.hasTransformed or len([w for w in inventory if w == "red"]) == 1:
            if pos[0] == zone_width*2 - 1:  # À l'extrémité de z1
                if not cell_has_waste:
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
        x_min, x_max, y_min, y_max = self.assigned_zone
        
        # Vérifier que la position actuelle est dans la zone assignée
        if not (x_min <= x <= x_max and y_min <= y <= y_max):
            print(f"[ERROR] {self.get_name()} est hors de sa zone: pos={x,y}, zone={x_min,x_max,y_min,y_max}")
            # Tenter de corriger la position
            corrected_x = max(x_min, min(x_max, x))
            corrected_y = max(y_min, min(y_max, y))
            if (corrected_x, corrected_y) != (x, y):
                print(f"[CORRECTION] {self.get_name()} repositionné à {corrected_x, corrected_y}")
                self.model.grid.move_agent(self, (corrected_x, corrected_y))
                return

        # Pour YellowGather, x est fixe (colonne assignée)
        if x < x_min or x > x_max:
            print(f"[CRITICAL] {self.get_name()} hors de sa colonne assignée: x={x}, zone={x_min}-{x_max}")
            # Corriger la position pour revenir dans la colonne correcte
            x = max(x_min, min(x_max, x))
            self.model.grid.move_agent(self, (x, y))
            return

        if not hasattr(self, "direction_y"):
            self.direction_y = 1  # 1 pour descendre, -1 pour monter

        new_y = y + self.direction_y

        if new_y < y_min or new_y > y_max:
            self.direction_y *= -1
            new_y = y + self.direction_y
            
            # Double vérification
            if new_y < y_min or new_y > y_max:
                new_y = y  # Rester sur place si toujours hors limites

        grid_height = self.model.height
        if not (0 <= new_y < grid_height):
            new_y = y
            self.direction_y *= -1
            
        if new_y < y_min or new_y > y_max:
            print(f"[WARNING] {self.get_name()} tente de sortir des limites verticales: new_y={new_y}, limites={y_min}-{y_max}")
            new_y = max(y_min, min(y_max, y))
            self.direction_y *= -1

        new_pos = (x, new_y)
        cell_contents = self.model.grid.get_cell_list_contents(new_pos)
        
        if not any(isinstance(obj, RobotAgent) for obj in cell_contents):
            self.model.grid.move_agent(self, new_pos)
            self.distance += 1
            self.blocked_steps = 0
        else:
            # Blocage détecté, incrémenter le compteur
            self.blocked_steps += 1
            print(f"[INFO] {self.get_name()} bloqué depuis {self.blocked_steps} steps.")

            # Si bloqué depuis plus de 5 steps, tenter un mouvement alternatif
            if self.blocked_steps > 5:
                print(f"[INFO] {self.get_name()} tente un mouvement alternatif.")
                
                # Inverser complètement la direction verticale et essayer de se déplacer
                self.direction_y *= -1
                alt_y = y + self.direction_y
                
                # Vérifier que la position alternative est valide (dans la zone et la grille)
                if y_min <= alt_y <= y_max and 0 <= alt_y < grid_height:
                    alt_pos = (x, alt_y)
                    alt_cell_contents = self.model.grid.get_cell_list_contents(alt_pos)
                    if not any(isinstance(obj, RobotAgent) for obj in alt_cell_contents):
                        print(f"[INFO] {self.get_name()} se déplace en position alternative {alt_pos}.")
                        self.model.grid.move_agent(self, alt_pos)
                        self.distance += 1
                        self.blocked_steps = 0
                    else:
                        # Si la première alternative échoue, essayer de s'arrêter temporairement
                        print(f"[INFO] {self.get_name()} reste sur place et attend.")
                        # Ne rien faire pendant ce tour pour laisser les autres se déplacer
                        # Le compteur continue d'augmenter pour une nouvelle tentative au prochain tour


class AloneYellow(YellowGather):
    def __init__(self, unique_id, model, pos, assigned_zone=None):
        super().__init__(unique_id, model, pos, assigned_zone)
        self._CommunicatingAgent__name = f"AloneYellow_{unique_id}"
    
    def deliberate(self, knowledge):
        current_cell = knowledge["percepts"][knowledge["pos"]]
        inventory = knowledge["inventory"]
        pos = knowledge["pos"]
        zone_width = knowledge["zone_width"]
        
        yellow_wastes = [obj for obj in current_cell if hasattr(obj, "waste_type") 
                        and obj.waste_type == "yellow" 
                        and obj.unique_id != self.last_dropped_waste_id]
        
        # Ne considérer qu'il y a un déchet valide que si la liste filtrée n'est pas vide
        valid_waste_in_cell = len(yellow_wastes) > 0
        
        if valid_waste_in_cell and len([w for w in inventory if w == "yellow"]) < 2:
            return {"action": "pickup", "waste": "yellow"}

        # Transformation si possible
        if not self.hasTransformed:
            if len([w for w in inventory if w == "yellow"]) >= 2:
                self.hasTransformed = True  # Empêche une nouvelle transformation
                return {"action": "transform", "from": "yellow", "to": "red"}

        # Vérifier s'il y a des déchets dans la cellule actuelle
        cell_has_waste = any(hasattr(obj, "waste_type") for obj in current_cell)

        if self.hasTransformed or len([w for w in inventory if w == "red"]) == 1:
            if pos[0] == zone_width*2 - 1:  # À l'extrémité de z1
                if not cell_has_waste:
                    return {"action": "drop", "waste": "red"}
                else:
                    return {"action": "move_vertical"}
            else:
                return {"action": "move_east"}

        return {"action": "move"}
     
    def move(self):
        if not self.assigned_zone:
            raise ValueError(f"Robot {self.unique_id} n'a pas de zone assignée.")

        x, y = self.pos
        x_min, x_max, y_min, y_max = self.assigned_zone

        # Vérifier que la position actuelle est dans la zone assignée
        if not (x_min <= x <= x_max and y_min <= y <= y_max):
            print(f"[ERROR] {self.get_name()} est hors de sa zone: pos={x,y}, zone={x_min,x_max,y_min,y_max}")
            # Tenter de corriger la position
            corrected_x = max(x_min, min(x_max, x))
            corrected_y = max(y_min, min(y_max, y))
            if (corrected_x, corrected_y) != (x, y):
                print(f"[CORRECTION] {self.get_name()} repositionné à {corrected_x, corrected_y}")
                self.model.grid.move_agent(self, (corrected_x, corrected_y))
                return  

        if not hasattr(self, "direction_x"):
            self.direction_x = 1  # 1 pour droite, -1 pour gauche
        if not hasattr(self, "direction_y"):
            self.direction_y = 1  # 1 pour descendre, -1 pour monter

        new_x = x + self.direction_x
        new_y = y

        if new_x < x_min or new_x > x_max:
            # On atteint un bord horizontal : on change de ligne
            self.direction_x *= -1  # On inverse le sens horizontal
            new_x = x  # On reste sur la même colonne pour ce tick
            new_y = y + self.direction_y

            if new_y < y_min or new_y > y_max:
                self.direction_y *= -1
                new_y = y + self.direction_y
                
                # Double vérification pour s'assurer que la nouvelle position reste dans la zone
                if new_y < y_min or new_y > y_max:
                    new_y = y  # Rester sur place si toujours hors limites

        grid_width, grid_height = self.model.width, self.model.height
        if not (0 <= new_x < grid_width and 0 <= new_y < grid_height):
            new_x, new_y = x, y
            self.direction_x *= -1
            self.direction_y *= -1

        if not (x_min <= new_x <= x_max and y_min <= new_y <= y_max):
            print(f"[WARNING] {self.get_name()} tente de sortir de sa zone: pos={new_x,new_y}, zone={x_min,x_max,y_min,y_max}")
            new_x = max(x_min, min(x_max, x))  # Forcer à rester dans la plage x
            new_y = max(y_min, min(y_max, y))  # Forcer à rester dans la plage y
            self.direction_x *= -1
            self.direction_y *= -1

        # Vérification finale que la nouvelle position est différente de la position actuelle
        if (new_x, new_y) == (x, y):
            # Essayer d'autres directions au lieu de rester immobile
            directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]  # Est, Ouest, Sud, Nord
            for dx, dy in directions:
                test_x, test_y = x + dx, y + dy
                if (x_min <= test_x <= x_max and y_min <= test_y <= y_max and 
                    0 <= test_x < grid_width and 0 <= test_y < grid_height):
                    new_x, new_y = test_x, test_y
                    break

        new_pos = (new_x, new_y)
        cell_contents = self.model.grid.get_cell_list_contents(new_pos)
        
        if not any(isinstance(obj, RobotAgent) for obj in cell_contents):
            self.model.grid.move_agent(self, new_pos)
            self.distance += 1
            self.blocked_steps = 0
        else:
            # Blocage détecté, incrémenter le compteur
            self.blocked_steps += 1
            print(f"[INFO] {self.get_name()} bloqué depuis {self.blocked_steps} steps à {self.pos}.")

            # Si bloqué depuis plus de 5 steps, tenter un mouvement alternatif
            if self.blocked_steps > 5:
                print(f"[INFO] {self.get_name()} tente un mouvement alternatif.")
                
                # Essayer plusieurs directions alternatives, toutes strictement dans la zone
                alternatives = []
                
                # Option 1: Reculer de 2 cases horizontalement (dans la zone)
                alt_x = max(x_min, min(x_max, x - 2 * self.direction_x))
                alternatives.append((alt_x, y))
                
                # Option 2: Monter d'une case (dans la zone)
                alt_y_up = max(y_min, min(y_max, y - 1))
                alternatives.append((x, alt_y_up))
                
                # Option 3: Descendre d'une case (dans la zone)
                alt_y_down = max(y_min, min(y_max, y + 1))
                alternatives.append((x, alt_y_down))
                
                # Ajout d'options diagonales (toujours dans la zone)
                alt_diag1 = (max(x_min, min(x_max, x - 1)), max(y_min, min(y_max, y - 1)))
                alt_diag2 = (max(x_min, min(x_max, x - 1)), max(y_min, min(y_max, y + 1)))
                alt_diag3 = (max(x_min, min(x_max, x + 1)), max(y_min, min(y_max, y - 1)))
                alt_diag4 = (max(x_min, min(x_max, x + 1)), max(y_min, min(y_max, y + 1)))
                alternatives.extend([alt_diag1, alt_diag2, alt_diag3, alt_diag4])
                
                # Essayer chaque alternative dans l'ordre
                for alt_pos in alternatives:
                    # Vérification rigoureuse que la position est valide
                    if (alt_pos != (x, y) and  # Différent de la position actuelle
                        0 <= alt_pos[0] < grid_width and 0 <= alt_pos[1] < grid_height and
                        x_min <= alt_pos[0] <= x_max and y_min <= alt_pos[1] <= y_max):
                        alt_cell_contents = self.model.grid.get_cell_list_contents(alt_pos)
                        if not any(isinstance(obj, RobotAgent) for obj in alt_cell_contents):
                            print(f"[INFO] {self.get_name()} se déplace en position alternative {alt_pos}.")
                            self.model.grid.move_agent(self, alt_pos)
                            self.distance += 1
                            self.blocked_steps = 0
                            break

class RedRobot(RobotAgent):
    def __init__(self, unique_id, model, pos, assigned_zone=None):
        super().__init__(unique_id, model, pos, assigned_zone)
        self._CommunicatingAgent__name = f"RedRobot_{unique_id}"
        self.type = "red"  
        self.allowed_zones = ["z1", "z2", "z3"]
        self.target_waste = None
        self._processed_notifications = set()  # Pour éviter de traiter deux fois le même message

    def deliberate(self, knowledge):
        percepts = knowledge["percepts"]
        current_cell = percepts[knowledge["pos"]]
        inventory = knowledge["inventory"]
        pos = knowledge["pos"]

        # PRIORITÉ 1: Vérifier D'ABORD la case actuelle pour un déchet rouge
        if len([w for w in inventory if w == "red"]) < 1:
            # Trouver tous les déchets rouges dans la cellule qui ne sont pas le dernier déposé
            red_wastes = [obj for obj in current_cell if hasattr(obj, "waste_type") 
                         and obj.waste_type == "red" 
                         and obj.unique_id != self.last_dropped_waste_id]
            
            # Ne considérer qu'il y a un déchet valide que si la liste filtrée n'est pas vide
            if red_wastes:
                if self.target_waste and self.target_waste["waste_pos"] == pos:
                    print(f"[INFO] {self.get_name()} picking up target waste at {pos}")
                self.target_waste = None  # Clear any target as we're picking up waste here
                return {"action": "pickup", "waste": "red"}

        # PRIORITÉ 2: Suivre un déchet ciblé si on en a un
        if self.target_waste and len([w for w in inventory if w == "red"]) < 1:
            waste_pos = self.target_waste["waste_pos"]
            
            # Si nous sommes sur la position du déchet mais qu'il n'y a pas de déchet, annuler la cible
            if pos == waste_pos:
                if not any(hasattr(obj, "waste_type") and obj.waste_type == "red" for obj in current_cell):
                    print(f"[INFO] {self.get_name()} at target position {waste_pos} but no waste found")
                    self.target_waste = None
                    self._last_notified_target = None  # Réinitialiser pour permettre de nouvelles notifications
                else:
                    return {"action": "pickup", "waste": "red"}
            
            # Si nous avons toujours une cible, se déplacer vers elle
            if self.target_waste:
                # Éviter d'envoyer des notifications répétées à chaque étape
                if self._last_notified_target != waste_pos:
                    self.send_doing_notification(waste_pos, "red")
                
                # Pathfinding simple vers le déchet
                dx = waste_pos[0] - pos[0]
                dy = waste_pos[1] - pos[1]
                
                # Prioriser le mouvement sur l'axe le plus éloigné
                if abs(dx) > abs(dy):
                    # Mouvement horizontal
                    step_x = 1 if dx > 0 else -1
                    target_pos = (pos[0] + step_x, pos[1])
                else:
                    # Mouvement vertical
                    step_y = 1 if dy > 0 else -1
                    target_pos = (pos[0], pos[1] + step_y)
                
                # Vérifier si la position est valide
                if 0 <= target_pos[0] < self.model.width and 0 <= target_pos[1] < self.model.height:
                    cell_contents = self.model.grid.get_cell_list_contents(target_pos)
                    if not any(isinstance(obj, RobotAgent) for obj in cell_contents):
                        print(f"[INFO] {self.get_name()} moving toward target waste at {waste_pos}, next step: {target_pos}")
                        return {"action": "move", "target": target_pos}

        # PRIORITÉ 2.5: Vérifier waste_locations
        if not self.target_waste and "waste_locations" in knowledge and knowledge["waste_locations"] and len([w for w in inventory if w == "red"]) < 1:
            for waste_info in knowledge["waste_locations"][:]:
                waste_pos = waste_info["waste_pos"]
                waste_type = waste_info["waste_type"]
                if waste_type == "red":
                    # Set as target and send notification
                    self.target_waste = waste_info
                    self.send_doing_notification(waste_pos, waste_type)
                    
                    # Calculate path to waste
                    dx = waste_pos[0] - pos[0]
                    dy = waste_pos[1] - pos[1]
                    
                    if abs(dx) > abs(dy):
                        step_x = 1 if dx > 0 else -1
                        target_pos = (pos[0] + step_x, pos[1])
                    else:
                        step_y = 1 if dy > 0 else -1
                        target_pos = (pos[0], pos[1] + step_y)
                    
                    print(f"[DEBUG] {self.get_name()} moving toward waste at {waste_pos}, next step: {target_pos}")
                    return {"action": "move", "target": target_pos}

        # PRIORITÉ 3: Vérifier les cases voisines s'il n'y a pas de cible
        if not self.target_waste and len([w for w in inventory if w == "red"]) < 1:
            for nearby_pos, agents in percepts.items():
                if nearby_pos != pos:  # On ne vérifie pas la cellule actuelle
                    for agent in agents:
                        if hasattr(agent, "waste_type") and agent.waste_type == "red":
                            # On vérifie si la position est dans une zone autorisée
                            cell_contents = self.model.grid.get_cell_list_contents(nearby_pos)
                            allowed = False
                            for obj in cell_contents:
                                if hasattr(obj, "zone") and obj.zone in self.allowed_zones:
                                    allowed = True
                            if allowed:
                                # Définir comme cible et envoyer une notification
                                self.target_waste = {"waste_pos": nearby_pos, "waste_type": "red"}
                                self.send_doing_notification(nearby_pos, "red")
                                return {"action": "move", "target": nearby_pos}

        # PRIORITÉ 4: Déposer un déchet si on en a un
        if len([w for w in inventory if w == "red"]) > 0:
            # Vérifier s'il y a des déchets dans la cellule actuelle
            cell_has_waste = any(hasattr(obj, "waste_type") for obj in current_cell)
            disposal_present = any(hasattr(obj, "zone") and obj.zone == "waste_zone" for obj in current_cell)
            if disposal_present and not cell_has_waste:
                # Effacer complètement les informations de cible lors du dépôt
                self.target_waste = None
                self._last_notified_target = None  # Réinitialiser
                if "waste_locations" in self.knowledge:
                    self.knowledge["waste_locations"] = []
                print(f"[INFO] {self.get_name()} depositing waste and clearing target")
                return {"action": "drop", "waste": "red"}
            else:
                return {"action": "move_east"}  # Aller vers la zone de dépôt

        # PRIORITÉ 5: Déplacement par défaut - MODIFICATION POUR DÉPLACEMENT ALÉATOIRE
        # Vérifier s'il y a plusieurs robots rouges
        red_robots = [agent for agent in self.model.robots 
                     if isinstance(agent, RedRobot)]
        
        if len(red_robots) > 1:
            # Mouvement aléatoire quand il y a plusieurs robots rouges
            import random
            possible_moves = []
            x, y = pos
            zone_width = self.model.width // 3
            last_yellow_column = 2*zone_width-1
            
            # Générer toutes les positions adjacentes possibles
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nx, ny = x + dx, y + dy
                if (0 <= nx < self.model.width and 0 <= ny < self.model.height):
                    if nx >= 2*zone_width or nx == last_yellow_column:
                        possible_moves.append((nx, ny))
            
            # Choisir une position aléatoire parmi celles disponibles
            if possible_moves:
                target_pos = random.choice(possible_moves)
                cell_contents = self.model.grid.get_cell_list_contents(target_pos)
                
                # Vérifier que la position n'est pas occupée par un autre robot
                if not any(isinstance(obj, RobotAgent) for obj in cell_contents):
                    return {"action": "move", "target": target_pos}
        
        # Fallback: mouvement standard si le mouvement aléatoire échoue
        return {"action": "move"}

    def process_messages(self):
        """Process all new messages in the mailbox - seule implémentation spécifique conservée"""
        new_messages = self.get_new_messages()
        waste_claimed = False  # Pour savoir si un déchet a été revendiqué
        
        # 1. Traiter d'abord les messages DOING pour éviter les conflits
        for message in [m for m in new_messages if m.get_performative() == MessagePerformative.DOING]:
            content = message.get_content()
            if isinstance(content, dict) and "waste_pos" in content:
                waste_pos = content["waste_pos"]
                
                # Génère un identifiant unique pour ce message pour éviter les doublons
                msg_id = f"{message.get_exp()}:{waste_pos}"
                if msg_id in self._processed_notifications:
                    continue  # Sauter ce message s'il a déjà été traité
                self._processed_notifications.add(msg_id)
                
                # Si ce robot a la même cible, comparer les distances
                if hasattr(self, "target_waste") and self.target_waste and self.target_waste["waste_pos"] == waste_pos:
                    # Calculer ma distance à la cible
                    my_pos = self.pos
                    my_distance = abs(my_pos[0] - waste_pos[0]) + abs(my_pos[1] - waste_pos[1])
                    
                    # Obtenir la position de l'expéditeur et calculer sa distance
                    sender_pos = content.get("agent_pos")
                    if sender_pos:
                        sender_distance = abs(sender_pos[0] - waste_pos[0]) + abs(sender_pos[1] - waste_pos[1])
                        
                        # Extraire l'ID du robot émetteur pour départager en cas d'égalité
                        try:
                            sender_id = int(message.get_exp().split('_')[1])
                        except (IndexError, ValueError):
                            sender_id = 0
                        
                        # Règle de décision - Abandonner la cible si:
                        # 1. Je suis plus loin, OU
                        # 2. Distances égales mais mon ID est plus grand (priorité au plus petit ID)
                        if my_distance > sender_distance or (my_distance == sender_distance and self.unique_id > sender_id):
                            print(f"[INFO] {self.get_name()} abandoning target at {waste_pos} - distance:{my_distance} vs {message.get_exp()}:{sender_distance}")
                            self.target_waste = None
                            waste_claimed = True
                        else:
                            print(f"[INFO] {self.get_name()} keeping target at {waste_pos} - distance:{my_distance} vs {message.get_exp()}:{sender_distance}")
                    else:
                        # Si pas de position d'expéditeur, utiliser l'ancien comportement
                        print(f"[INFO] {self.get_name()} received DOING notification for waste at {waste_pos}")
                
                # Supprimer de waste_locations si présent, qu'on abandonne ou non
                if "waste_locations" in self.knowledge:
                    self.knowledge["waste_locations"] = [
                        loc for loc in self.knowledge["waste_locations"] 
                        if loc["waste_pos"] != waste_pos
                    ]
        
        # Limiter la taille de l'ensemble des messages traités
        if len(self._processed_notifications) > 100:
            self._processed_notifications.clear()
        
        # 2. Traiter les messages REQUEST uniquement si on n'a pas de cible
        if not self.target_waste:
            for message in [m for m in new_messages if m.get_performative() == MessagePerformative.REQUEST]:
                content = message.get_content()
                if isinstance(content, dict) and "waste_pos" in content:
                    waste_pos = content["waste_pos"]
                    waste_type = content["waste_type"]
                    print(f"[REQUEST] Agent {self.get_name()} received info about {waste_type} waste at {waste_pos}")
                    
                    # Stocker l'info seulement si on n'a pas déjà une cible et que l'inventaire est vide
                    if waste_type == "red" and len(self.inventory) == 0:
                        self.target_waste = content
                        print(f"[INFO] {self.get_name()} setting target to {waste_pos}")
                        
                        # Informer les autres robots rouges qu'on s'occupe de ce déchet
                        self.send_doing_notification(waste_pos, waste_type)
                    else:
                        # Si on n'est pas disponible, on stocke quand même l'info pour plus tard
                        if "waste_locations" not in self.knowledge:
                            self.knowledge["waste_locations"] = []
                        if not any(loc.get("waste_pos") == waste_pos for loc in self.knowledge["waste_locations"]):
                            self.knowledge["waste_locations"].append(content)