'''
@authors 
Rayane Bouaita
Gabriel Trier
Pierre El Anati

Groupe 21

@date 11/03/2025
'''
import mesa
import networkx

class Agent(mesa.Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.knowledge = {"position": None, "percepts": {}}
    
    def percepts(self):
        """Récupère les perceptions de l'environnement."""
        self.knowledge["position"] = self.pos
        self.knowledge["percepts"] = self.model.do(self, {"type": "SENSE"})
    
    def deliberate(self, knowledge):
        """Prend une décision basée sur la connaissance actuelle."""
        # Exemple de logique : se déplacer aléatoirement si aucune autre action n'est nécessaire
        import random
        possible_moves = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # Haut, droite, bas, gauche
        move = random.choice(possible_moves)
        new_position = (self.pos[0] + move[0], self.pos[1] + move[1])
        return {"type": "MOVE", "position": new_position}
    
    def do(self):
        """Exécute l'action choisie et met à jour les perceptions."""
        action = self.deliberate(self.knowledge)
        self.knowledge["percepts"] = self.model.do(self, action)
    
    def step(self):
        """Cycle de vie de l'agent."""
        self.percepts()
        self.do()

class GreenAgent(Agent):
    def deliberate(self, knowledge):
        """Délibération spécifique au GreenAgent."""
        if "waste" in knowledge["percepts"].get(self.pos, []):
            return {"type": "PICK"}
        return super().deliberate(knowledge)

class YellowAgent(Agent):
    def deliberate(self, knowledge):
        """Délibération spécifique au YellowAgent."""
        if "recyclable" in knowledge["percepts"].get(self.pos, []):
            return {"type": "PICK"}
        return super().deliberate(knowledge)

class RedAgent(Agent):
    def deliberate(self, knowledge):
        """Délibération spécifique au RedAgent."""
        if "dangerous" in knowledge["percepts"].get(self.pos, []):
            return {"type": "PICK"}
        return super().deliberate(knowledge)
