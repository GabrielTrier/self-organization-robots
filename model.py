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
    def __init__(self, width=15, height=9, green_waste=1, yellow_waste=1, red_waste=1,
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
        self.robots = []  #liste to store agents pas sur !
        self.step_count = 0  #Add step counter (temporaire)
        
        self.setup_zones()
        self.add_initial_waste()
        self.create_robots()

        self.datacollector = DataCollector( model_reporters={"Step": lambda m: m.step_count})
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
        
        #Agents verts : zone 1
        for _ in range(self.n_green):
            x = self.random.randrange(0, zone_width)
            y = self.random.randrange(0, self.height)
            robot = GreenRobot(self, (x, y))
            self.grid.place_agent(robot, (x, y))
            self.robots.append(robot)
        
        #Agents jaunes : zones 1 et 2
        for _ in range(self.n_yellow):
            x = self.random.randrange(0, 2 * zone_width)
            y = self.random.randrange(0, self.height)
            robot = YellowRobot(self, (x, y))
            self.grid.place_agent(robot, (x, y))
            self.robots.append(robot)
        
        #Agents rouges : toutes zones
        for _ in range(self.n_red):
            x = self.random.randrange(0, self.width)
            y = self.random.randrange(0, self.height)
            robot = RedRobot(self, (x, y))
            self.grid.place_agent(robot, (x, y))
            self.robots.append(robot)


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

    def step(self):
        # Call step on each robot agent directly instead of using agents.shuffle_do
        for robot in self.robots:
            robot.step()
        
        #Increment step counter and collect data
        self.step_count += 1
        self.datacollector.collect(self)
        print(f"Step {self.step_count} completed")