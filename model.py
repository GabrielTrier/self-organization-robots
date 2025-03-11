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
from agents import Agent
from mesa import Model
from mesa.space import MultiGrid
from agents import RedAgent, YellowAgent, GreenAgent

def compute_gini(model):
    agent_wealths = [agent.wealth for agent in model.agents]
    x = sorted(agent_wealths)
    N = model.num_agents
    B = sum(xi * (N - i) for i, xi in enumerate(x)) / (N * sum(x))
    return 1 + (1 / N) - 2 * B

class RobotMission(Model):
    def __init__(self, width, height, num_green, num_yellow, num_red):
        super().__init__()
        self.grid = MultiGrid(width, height, True)
        self.agent_list = []  # Liste pour stocker les agents (évite le conflit avec Mesa)
        
        # Ajouter des robots verts
        for i in range(num_green):
            agent = GreenAgent(i, self)
            self.agent_list.append(agent)
            x, y = self.grid.find_empty()
            self.grid.place_agent(agent, (x, y))
        
        # Ajouter des robots jaunes
        for i in range(num_green, num_green + num_yellow):
            agent = YellowAgent(i, self)
            self.agent_list.append(agent)
            x, y = self.grid.find_empty()
            self.grid.place_agent(agent, (x, y))
        
        # Ajouter des robots rouges
        for i in range(num_green + num_yellow, num_green + num_yellow + num_red):
            agent = RedAgent(i, self)
            self.agent_list.append(agent)
            x, y = self.grid.find_empty()
            self.grid.place_agent(agent, (x, y))

    def step(self):
        """Avance d'un pas de simulation en activant chaque agent"""
        for agent in self.agent_list:
            agent.step()

    def do(self, agent, action):
        """Exécute une action pour un agent donné"""
        percepts = {}
        
        if action["type"] == "MOVE":
            new_position = action["position"]
            if self.grid.is_cell_empty(new_position):  # Vérification de la faisabilité
                self.grid.move_agent(agent, new_position)
                percepts[new_position] = self.grid.get_cell_list_contents(new_position)
            else:
                percepts["error"] = "Move not possible"
        
        elif action["type"] == "PICK":
            objects = self.grid.get_cell_list_contents(agent.pos)
            if objects:
                agent.pick(objects[0])
                percepts[agent.pos] = self.grid.get_cell_list_contents(agent.pos)
            else:
                percepts["error"] = "Nothing to pick"

        elif action["type"] == "DROP":
            agent.drop()
            percepts[agent.pos] = self.grid.get_cell_list_contents(agent.pos)
        
        return percepts

class Model2(mesa.Model):
    
    """A model with some number of agents."""

    def __init__(self, n=10, width=10, height=10, seed=None):
        """Initialize a MoneyModel instance.

        Args:
            N: The number of agents.
            width: width of the grid.
            height: Height of the grid.
        """
        super().__init__(seed=seed)
        self.num_agents = n
        self.grid = mesa.space.MultiGrid(width, height, True)

        # Create agents
        agents = Agent.create_agents(model=self, n=n)
        # Create x and y positions for agents
        x = self.rng.integers(0, self.grid.width, size=(n,))
        y = self.rng.integers(0, self.grid.height, size=(n,))
        for a, i, j in zip(agents, x, y):
            # Add the agent to a random grid cell
            self.grid.place_agent(a, (i, j))

        self.datacollector = mesa.DataCollector(
            model_reporters={"Gini": compute_gini}, agent_reporters={"Wealth": "wealth"}
        )
        self.datacollector.collect(self)

    def step(self):
        """do one step of the model"""
        self.agents.shuffle_do("step")
        self.datacollector.collect(self)