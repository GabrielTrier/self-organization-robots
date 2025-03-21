'''
@authors 
Rayane Bouaita
Gabriel Trier
Pierre El Anati

Groupe 21

@date 11/03/2025
'''

import mesa
import solara
from matplotlib.figure import Figure
from mesa.visualization import SolaraViz, make_plot_component, make_space_component
from mesa.visualization.utils import update_counter
from model import RobotModel  
from objects import Radioactivity, WasteDisposal, Waste
from agents import GreenRobot, YellowRobot, RedRobot

# Fonction pour afficher les robots sur la grille
def agent_portrayal(agent):
    portrayal = {"color": "white","marker":"o","zorder":1}

    if isinstance(agent, GreenRobot):
        portrayal["color"] = "blue" 
    elif isinstance(agent, YellowRobot):
        portrayal["color"] = "gold"
    elif isinstance(agent, RedRobot):
        portrayal["color"] = "red" 

    elif isinstance(agent, Waste):
        portrayal["size"] = 20
        portrayal["marker"] = "x"
        if agent.waste_type == "green":
            portrayal["color"] = "blue" 
        elif agent.waste_type == "yellow":
            portrayal["color"] = "gold"
        else:  # red waste
            portrayal["color"] = "red"

    elif isinstance(agent, WasteDisposal):
        portrayal["color"] = "black"
        portrayal["marker"] = "s"
        portrayal["size"] = 700
        portrayal["zorder"] = 0
    elif isinstance(agent, Radioactivity):
        portrayal["marker"] = "s"
        portrayal["zorder"] = 0
        portrayal["size"] = 700
        if agent.zone == "z1":
            portrayal["color"] = "#B8C3F5"  
        elif agent.zone == "z2":
            portrayal["color"] = "#FFF9A3"  
        else:  
            portrayal["color"] = "#FFADAD"  
            
    return portrayal

#Composant Histogramme : Affiche l'évolution des étapes de la simulation
@solara.component
def StepHistogram(model):
    update_counter.get()
    fig = Figure()
    ax = fig.subplots()

    # Récupérer les données du DataCollector
    df = model.datacollector.get_model_vars_dataframe()

    # Vérifier si des données existent avant d'afficher et d'ajouter une légende
    if not df.empty:
        ax.plot(df.index, df["Step"], label="Step Count", color="blue")
        ax.legend()  # Only add legend if we have data

    ax.set_xlabel("Itération")
    ax.set_ylabel("Nombre d'étapes")
    solara.FigureMatplotlib(fig)

# Paramètres de simulation interactifs
model_params = {
    "width": 15,
    "height": 9,
    "green_waste": {
        "type": "SliderInt",
        "label": "Green Waste:",
        "min": 0,
        "max": 10,
        "step": 1,
    },
    "yellow_waste": {
        "type": "SliderInt",
        "label": "Yellow Waste",
        "min": 0,
        "max": 10,
        "step": 1,
    },
    "red_waste": {
        "type": "SliderInt",
        "label": "Red Waste",
        "min": 0,
        "max": 10,
        "step": 1,
    },
    "n_green": {
        "type": "SliderInt",
        "label": "Green Agents",
        "min": 0,
        "max": 20,
        "step": 1,
    },
    "n_yellow": {
        "type": "SliderInt",
        "label": "Yellow Agents",
        "min": 0,
        "max": 20,
        "step": 1,
    },
    "n_red": {
        "type": "SliderInt",
        "label": "Red Agents",
        "min": 0,
        "max": 20,
        "step": 1,
    },
}

model1 = RobotModel(width=15, height=9, green_waste=1, yellow_waste=1, red_waste=1,
                 n_green=1, n_yellow=1, n_red=1)

# Création des composants d'affichage
SpaceGraph = make_space_component(agent_portrayal)
StepPlot = make_plot_component("StepHistogram")  
# Création du Dashboard Solara
page = SolaraViz(
    model1,
    components=[SpaceGraph, StepHistogram], 
    model_params=model_params,
    name="Simulation de Robots",
)