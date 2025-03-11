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
