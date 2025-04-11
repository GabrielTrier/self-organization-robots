'''
@authors 
Rayane Bouaita
Gabriel Trier
Pierre El Anati

Groupe 21

@date 11/03/2025
'''

import mesa 
from agents import RobotAgent
from mesa.datacollection import DataCollector
from objects import Radioactivity, WasteDisposal, Waste
from agents import GreenRobot, YellowRobot, RedRobot

class RobotModel(mesa.Model):
    def __init__(self, width=15, height=9, green_waste=4, yellow_waste=4, red_waste=4,
                 n_green=1, n_yellow=1, n_red=1):
        super().__init__()
        self.width = width
        self.height = height
        self.green_waste = green_waste
        self.yellow_waste = yellow_waste
        self.red_waste = red_waste
        self.n_green = n_green
        self.n_yellow = n_yellow
        self.n_red = n_red
        self.grid = mesa.space.MultiGrid(width, height, False)
        self.robots = []  
        self.step_count = 0  #Add step counter 
        self.deposition_step = None
        self.running = True  #Attribut standard de Mesa pour contrôler l'exécution
        
        self.setup_zones()
        self.add_initial_waste()
        self.create_robots()

        self.datacollector = DataCollector(
            model_reporters={
                "Step": lambda m: m.step_count,
                "GreenDistance": lambda m: sum(r.distance for r in m.robots if r.type == "green"),
                "YellowDistance": lambda m: sum(r.distance for r in m.robots if r.type == "yellow"),
                "RedDistance": lambda m: sum(r.distance for r in m.robots if r.type == "red"),
                "RedDepositionStep": lambda m: m.deposition_step if m.deposition_step is not None else None
            }
        )
        # Initial data collection
        self.datacollector.collect(self)
    
    def setup_zones(self):
        zone_width = self.width // 3

        #Place Radioactivity agents in every cell with the proper zone assignment.
        for x in range(self.width):
            for y in range(self.height):
                if x < zone_width:
                    zone = "z1"
                elif x < 2 * zone_width:
                    zone = "z2"
                else:
                    zone = "z3"
                radioactivity = Radioactivity(self, zone)
                self.grid.place_agent(radioactivity, (x, y))

        for y in range(self.height):
            disposal = WasteDisposal(self)
            self.grid.place_agent(disposal, (self.width - 1, y))

    def create_robots(self):
        zone_width = self.width // 3
        robot_id = 0

        # Agents verts : zone 1
        green_zone_width = zone_width // self.n_green if self.n_green > 0 else zone_width
        for i in range(self.n_green):
            x_min = i * green_zone_width
            x_max = (i + 1) * green_zone_width - 1
            x = self.random.randrange(x_min, x_max + 1)
            y = self.random.randrange(0, self.height)
            robot = GreenRobot(robot_id, self, (x, y), assigned_zone=(x_min, x_max, 0, self.height - 1))
            self.grid.place_agent(robot, (x, y))
            self.robots.append(robot)
            print(f"[DEBUG] Robot vert créé à la position : ({x}, {y}) avec l'ID : {robot_id} et zone assignée : ({x_min}, {x_max})")
            robot_id += 1

        # Agents jaunes : zones 1 et 2
        yellow_zone_width = (2 * zone_width) // self.n_yellow if self.n_yellow > 0 else 2 * zone_width
        for i in range(self.n_yellow):
            x_min = i * yellow_zone_width
            x_max = (i + 1) * yellow_zone_width - 1
            x = self.random.randrange(x_min, x_max + 1)
            y = self.random.randrange(0, self.height)
            robot = YellowRobot(robot_id, self, (x, y), assigned_zone=(x_min, x_max, 0, self.height - 1))
            self.grid.place_agent(robot, (x, y))
            self.robots.append(robot)
            print(f"[DEBUG] Robot jaune créé à la position : ({x}, {y}) avec l'ID : {robot_id} et zone assignée : ({x_min}, {x_max})")
            robot_id += 1

        # Agents rouges : toutes zones
        for _ in range(self.n_red):
            x = self.random.randrange(0, self.width)
            y = self.random.randrange(0, self.height)
            robot = RedRobot(robot_id, self, (x, y), assigned_zone=(0, self.width - 1, 0, self.height - 1))
            self.grid.place_agent(robot, (x, y))
            self.robots.append(robot)
            print(f"[DEBUG] Robot rouge créé à la position : ({x}, {y}) avec l'ID : {robot_id}")
            robot_id += 1

    def add_initial_waste(self):
        zone_width = self.width // 3
        
        #Zone 1: waste verts
        for _ in range(self.green_waste):
            x = self.random.randrange(0, zone_width)
            y = self.random.randrange(0, self.height)
            waste = Waste(self, "green")
            self.grid.place_agent(waste, (x, y))
        
        #Zone 2: waste jaunes
        for _ in range(self.yellow_waste):
            x = self.random.randrange(zone_width, 2 * zone_width)
            y = self.random.randrange(0, self.height)
            waste = Waste(self, "yellow")
            self.grid.place_agent(waste, (x, y))
        
        #Zone 3: waste rouges (en évitant la dernière colonne pour le waste disposal)
        for _ in range(self.red_waste):
            x = self.random.randrange(2 * zone_width, self.width - 1)
            y = self.random.randrange(0, self.height)
            waste = Waste(self, "red")
            self.grid.place_agent(waste, (x, y))

    def do(self, agent, action):
        if action["action"] == "move":
            agent.distance += 1
            if "target" in action:
                # Move agent directly to target position if provided
                target_pos = action["target"]
                cell_contents = self.grid.get_cell_list_contents(target_pos)
                zone = None
                for obj in cell_contents:
                    if hasattr(obj, "zone") and obj.__class__.__name__ == "Radioactivity":
                        zone = obj.zone
                        break
                if zone in agent.allowed_zones:
                    self.grid.move_agent(agent, target_pos)
            else:
                agent.move()

        elif action["action"] == "move_east":
            x, y = agent.pos
            new_pos = (x + 1, y)
            if new_pos[0] < self.width:
                cell_contents = self.grid.get_cell_list_contents(new_pos)
                zone = None
                for obj in cell_contents:
                    if hasattr(obj, "zone") and obj.__class__.__name__ == "Radioactivity":
                        zone = obj.zone
                        break
                if zone in agent.allowed_zones:
                    agent.distance += 1
                    self.grid.move_agent(agent, new_pos)

        elif action["action"] == "move_vertical":
            x, y = agent.pos
            possible_positions = []
            if y - 1 >= 0:
                possible_positions.append((x, y - 1))
            if y + 1 < self.height:
                possible_positions.append((x, y + 1))
            for new_pos in possible_positions:
                cell_contents = self.grid.get_cell_list_contents(new_pos)
                if not any(hasattr(obj, "waste_type") for obj in cell_contents) and not any(isinstance(obj, RobotAgent) for obj in cell_contents):
                    agent.distance += 1
                    self.grid.move_agent(agent, new_pos)
                    break

        elif action["action"] == "pickup":
            current_cell = self.grid.get_cell_list_contents(agent.pos)
            for obj in current_cell:
                if hasattr(obj, "waste_type") and obj.waste_type == action["waste"]:
                    agent.inventory.append(obj.waste_type)
                    self.grid.remove_agent(obj)
                    break

        elif action["action"] == "transform":
            # 2 green -> 1 yellow
            if action["from"] == "green" and action["to"] == "yellow":
                green_waste = [w for w in agent.inventory if w == "green"]
                if len(green_waste) >= 2:
                    for _ in range(2):
                        agent.inventory.remove("green")
                    agent.inventory.append("yellow")
                    agent.hasTransformed = True # Empeche de recolter d'autres dechets

            # 2 yellow -> 1 red
            elif action["from"] == "yellow" and action["to"] == "red":
                yellow_waste = [w for w in agent.inventory if w == "yellow"]
                if len(yellow_waste) >= 2:
                    for _ in range(2):
                        agent.inventory.remove("yellow")
                    agent.inventory.append("red")
                    agent.hasTransformed = True

        elif action["action"] == "drop":
            cell_contents = self.grid.get_cell_list_contents(agent.pos)
            if any(hasattr(obj, "waste_type") for obj in cell_contents):
                return cell_contents
            
            #si dépot dans zone de déchets
            if any(hasattr(obj, "zone") and obj.zone == "waste_zone" for obj in cell_contents):
                agent.inventory.remove(action["waste"])
            else:
                waste = Waste(self, action["waste"])
                self.grid.place_agent(waste, agent.pos)
                agent.inventory.remove(action["waste"])
            agent.hasTransformed = False

        return self.grid.get_cell_list_contents(agent.pos)


    def step(self):
        # STOp si tous les déchets ont été éliminés (grille et inventaire)
        no_waste_on_grid = all(not isinstance(a, Waste) for a in self.grid.agents)
        no_waste_in_inventory = all(len(robot.inventory) == 0 for robot in self.robots)
        
        if no_waste_on_grid and no_waste_in_inventory:
            if self.deposition_step is None:  
                self.deposition_step = self.step_count  
                print(f"Tous les déchets ont été définitivement éliminés à l'étape {self.deposition_step}")
                self.datacollector.collect(self)
            self.running = False  #Stop la simulation       
            return  

        for robot in self.robots:        
            robot.step()

        # Increment step counter and collect data
        self.step_count += 1
        self.datacollector.collect(self)
        print(f"Step {self.step_count} completed")