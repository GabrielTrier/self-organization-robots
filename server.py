'''
@authors 
Rayane Bouaita
Gabriel Trier
Pierre El Anati

Groupe 21

@date 11/03/2025
'''
<<<<<<< HEAD
=======

>>>>>>> 68e3cec954814c009aa32b69dfeb381be2ca6d21
import mesa
import solara
from matplotlib.figure import Figure
from mesa.visualization import SolaraViz, make_plot_component, make_space_component
from mesa.visualization.utils import update_counter
<<<<<<< HEAD
# Import the local MoneyModel.py
from model import Model


def agent_portrayal(agent):
    size = 10
    color = "tab:red"
    if agent.wealth > 0:
        size = 50
        color = "tab:blue"
    return {"size": size, "color": color}

@solara.component
def Histogram(model):
    update_counter.get() # This is required to update the counter
    # Note: you must initialize a figure using this method instead of
    # plt.figure(), for thread safety purpose
    fig = Figure()
    ax = fig.subplots()
    wealth_vals = [agent.wealth for agent in model.agents]
    # Note: you have to use Matplotlib's OOP API instead of plt.hist
    # because plt.hist is not thread-safe.
    ax.hist(wealth_vals, bins=10)
    solara.FigureMatplotlib(fig)

model_params = {
    "n": {
        "type": "SliderInt",
        "value": 50,
        "label": "Number of agents:",
        "min": 10,
        "max": 100,
        "step": 1,
    },
    "width": 10,
    "height": 10,
}

# Create initial model instance
model1 = Model(50, 10, 10)

SpaceGraph = make_space_component(agent_portrayal)
GiniPlot = make_plot_component("Gini")

#Create the Dashboard
page = SolaraViz(
    model1,
    components=[SpaceGraph, GiniPlot, Histogram],
    model_params=model_params,
    name="Boltzmann Wealth Model",
)
# This is required to render the visualization in the Jupyter notebook
page
# to start : "solara run server.py"
=======
from model import RobotModel  # Importer le modèle corrigé avec DataCollector

# Fonction pour afficher les robots sur la grille
def agent_portrayal(agent):
    return {"size": 50, "color": "tab:blue"}

# 📌 Composant Histogramme : Affiche l'évolution des étapes de la simulation
@solara.component
def StepHistogram(model):
    update_counter.get()  # Mise à jour automatique
    fig = Figure()
    ax = fig.subplots()

    # Récupérer les données du DataCollector
    df = model.datacollector.get_model_vars_dataframe()

    # Vérifier si des données existent avant d'afficher
    if not df.empty:
        ax.plot(df.index, df["Step"], label="Step", color="blue")

    ax.set_xlabel("Itération")
    ax.set_ylabel("Nombre d'étapes")
    ax.legend()
    solara.FigureMatplotlib(fig)

# Paramètres de simulation interactifs
model_params = {
    "n": {
        "type": "SliderInt",
        "value": 5,
        "label": "Nombre de robots:",
        "min": 1,
        "max": 20,
        "step": 1,
    },
    "width": 15,
    "height": 9,
}

# Initialisation du modèle
model1 = RobotModel(5, 15, 9)

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
>>>>>>> 68e3cec954814c009aa32b69dfeb381be2ca6d21
