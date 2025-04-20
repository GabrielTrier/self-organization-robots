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
from agents import GreenRobot, YellowRobot, RedRobot, GreenGather, YellowGather, AloneGreen, AloneYellow
from MessageService import MessageService
from Message import Message
from MessagePerformative import MessagePerformative

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
        
        self.message_service = MessageService(self, instant_delivery=False) #Communication 

        self.setup_zones()
        self.add_initial_waste()
        self.create_robots()

        self.datacollector = DataCollector(
            model_reporters={
                "Step": lambda m: m.step_count,
                "GreenDistance": lambda m: sum(r.distance for r in m.robots if r.type == "green"),
                "YellowDistance": lambda m: sum(r.distance for r in m.robots if r.type == "yellow"),
                "RedDistance": lambda m: sum(r.distance for r in m.robots if r.type == "red"),
                "RedDepositionStep": lambda m: m.deposition_step if m.deposition_step is not None else None,
                "GreenWasteCount": lambda m: sum(1 for a in m.grid.agents if isinstance(a, Waste) and a.waste_type == "green"),
                "YellowWasteCount": lambda m: sum(1 for a in m.grid.agents if isinstance(a, Waste) and a.waste_type == "yellow"),
                "RedWasteCount": lambda m: sum(1 for a in m.grid.agents if isinstance(a, Waste) and a.waste_type == "red")
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
        robot_id = 0
        color_configs = [
            ("green", self.n_green, GreenRobot, GreenGather, AloneGreen, 0),   # zone gauche (tiers 0)
            ("yellow", self.n_yellow, YellowRobot, YellowGather, AloneYellow, 1),  # zone centre (tiers 1)
            ("red", self.n_red + 1, RedRobot, RedRobot, RedRobot, 2),         # zone droite (tiers 2)
        ]

        for color, count, robot_cls, gather_cls, alone_cls, zone_index in color_configs:
            if count <= 0:
                continue

            zone_width = self.width // 3
            if color == 'green':
                x_min = zone_index * zone_width
                x_max = (zone_index + 1) * zone_width - 1
            elif color == 'yellow':
                x_min = zone_index * (zone_width) - 1
                x_max = (zone_index + 1) * zone_width - 1
            else:
                x_min = zone_index * (zone_width) -1
                x_max = (zone_index + 1) * zone_width - 2

            if count > 1:
                zone_height = self.height // (count - 1)
                for i in range(count - 1):
                    y_min = i * zone_height
                    y_max = (i + 1) * zone_height - 1 if i < count - 2 else self.height - 1
                    x = self.random.randrange(x_min, x_max + 1)
                    y = self.random.randrange(y_min, y_max + 1)
                    robot = robot_cls(
                        robot_id,
                        self,
                        (x, y),
                        assigned_zone=(x_min, x_max, y_min, y_max)
                    )
                    ##pour éviter que les robots prennent la dernière colonne (sauf le gather)
                    robot.ignore_last_column = True
                    robot.deposit_column = x_max
                    self.grid.place_agent(robot, (x, y))
                    self.robots.append(robot)
                    print(f"[DEBUG] {color.capitalize()}Robot créé à ({x}, {y}) | ID : {robot_id} | Zone : ({x_min}, {x_max}, {y_min}, {y_max})")
                    robot_id += 1

                if color != 'red':
                    # Ajout du robot Gather
                    y_min = 0
                    y_max = self.height - 1
                    x = x_max
                    y = self.random.randrange(y_min, y_max + 1)
                    robot = gather_cls(
                        robot_id,
                        self,
                        (x, y),
                        assigned_zone=(x_min, x_max, y_min, y_max)
                    )
                    self.grid.place_agent(robot, (x, y))
                    self.robots.append(robot)
                    print(f"[DEBUG] {color.capitalize()}Gather créé à ({x}, {y}) | ID : {robot_id} | Zone : ({x_min}, {x_max}, {y_min}, {y_max})")
                    robot_id += 1

            elif not ((color == 'red') and (count == 1)):  # un seul robot
                y_min = 0
                y_max = self.height - 1
                x = self.random.randrange(x_min, x_max + 1)
                y = self.random.randrange(y_min, y_max + 1)
                robot = alone_cls(
                    robot_id,
                    self,
                    (x, y),
                    assigned_zone=(x_min, x_max, y_min, y_max)
                )
                self.grid.place_agent(robot, (x, y))
                self.robots.append(robot)
                print(f"[DEBUG] {color.capitalize()}Robot (unique) créé à ({x}, {y}) | ID : {robot_id} | Zone : ({x_min}, {x_max}, {y_min}, {y_max})")
                robot_id += 1

    def add_initial_waste(self):
        zone_width = self.width // 3
        waste_id = 0  # ID unique pour chaque déchet
        
        #Zone 1: waste verts
        for _ in range(self.green_waste):
            x = self.random.randrange(0, zone_width)
            y = self.random.randrange(0, self.height)
            waste = Waste(self, "green")
            waste.unique_id = waste_id  # Assigner un ID unique
            waste_id += 1
            self.grid.place_agent(waste, (x, y))
        
        #Zone 2: waste jaunes
        for _ in range(self.yellow_waste):
            x = self.random.randrange(zone_width, 2 * zone_width)
            y = self.random.randrange(0, self.height)
            waste = Waste(self, "yellow")
            waste.unique_id = waste_id  # Assigner un ID unique
            waste_id += 1
            self.grid.place_agent(waste, (x, y))
        
        #Zone 3: waste rouges (en évitant la dernière colonne pour le waste disposal)
        for _ in range(self.red_waste):
            x = self.random.randrange(2 * zone_width, self.width - 1)
            y = self.random.randrange(0, self.height)
            waste = Waste(self, "red")
            waste.unique_id = waste_id  # Assigner un ID unique
            waste_id += 1
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
                if hasattr(agent, "target_waste"):
                    agent.target_waste = None
                    if hasattr(agent, "_last_notified_target"):
                        agent._last_notified_target = None
            else:
                waste = Waste(self, action["waste"])
                waste.unique_id = self.next_waste_id if hasattr(self, "next_waste_id") else 1000 # Assigner un ID unique au déchet
                self.next_waste_id = waste.unique_id + 1 if hasattr(self, "next_waste_id") else 1001
                
                # Marquer ce déchet comme "à ignorer" par l'agent qui l'a déposé
                agent.last_dropped_waste_id = waste.unique_id
                
                self.grid.place_agent(waste, agent.pos)
                agent.inventory.remove(action["waste"])

                self.notify_waste_drop(agent, action["waste"], agent.pos)
            
            agent.hasTransformed = False

        return self.grid.get_cell_list_contents(agent.pos)


    def notify_waste_drop(self, sender_agent, waste_type, position):
        if waste_type == "red" and sender_agent.type == "yellow":
            target_type = "red"
            
            content = {
                "waste_pos": position,
                "waste_type": waste_type,
                "drop_time": self.step_count
            }
            
            for agent in self.robots:
                if hasattr(agent, 'type') and agent.type == target_type:
                    try:
                        # Have the sender agent send the message directly
                        message = Message(
                            sender_agent.get_name(),
                            agent.get_name(),
                            MessagePerformative.REQUEST,
                            content
                        )
                        sender_agent.send_message(message)
                        print(f"[NOTIFY] Agent {sender_agent.get_name()} notified {agent.get_name()} about {waste_type} waste at {position}")
                    except Exception as e:
                        print(f"Error sending message: {e}")

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

        #Distribution des messages entre les agents
        self.message_service.dispatch_messages()
    
        for robot in self.robots:        
            robot.step()

        # Increment step counter and collect data
        self.step_count += 1
        self.datacollector.collect(self)
        print(f"Step {self.step_count} completed")