# Robot Mission 21 

**Auteurs**: 
- Rayane Bouaita
- Gabriel Trier
- Pierre El Anati

L'objectif du projet est de modéliser et simuler un système multi-agents où des robots ont pour but de collecter, transformer et déposer des déchets dans un environnement. L'environnement est divisé en trois zones de radioactivité croissante. Chaque type de robot a des capacités de collecte et de transformation différentes. Les déchets collectés doivent être déposés dans une zone de dépôt située tout à droite de la grille. 

## Représeantation de l'environnement

L'environnement est représenté par une grille 2D de 9x15. Chaque cellule de la grille est caractérisée par un niveau de radioactivité. Le niveau de radioactivité est généré aléatoirement selon la zone (z1: 0-0.33, z2: 0.33-0.66, z3: 0.66-1). Chaque cellule peut contenir un déceht ou un robot. La zone de dépôt est située sur la colonne à toute la droite de la grille.
Deux déchets bleues peuvent être transformés en un déchet jaune, deux déchets jeune peuvent être transformés en un déchet rouge. Seul les déchets rouges doivent être déposés dans la zone de dépôt.

## Structure du projet

Le projet est organisé en plusieurs fichiers principaux :

### 1. model.py

Ce fichier contient la classe principale du modèle, RobotModel, qui gère l'environnement et la simulation.

On initialise la grille et les paramètres de la simulation dans la méthode `__init__`:
- On crée la grille avec ses trois zones de radioactivité.
- On place les déchets verts, jaunes et rouges aléatoirement dans la grille.
- On place les robots verts, jaunes et rouges dans leurs zones respectives.

La méthode `step` est appelée à chaque étape de la simulation. Elle démande à chaque robot d'éxécuter une action via sa propre méthode `step`. La méthode permet également de vérifier si la simulation est terminée (tous les déchets sont collectés et déposés). 

La méthode `do` permet d'éxécuter les actions des robots en mettent à jour l'état de la grille et des agents en conséquence.

---

### 2. agents.py

Ce fichier contient les classes des agents de la simulation. 

Tous les robots héritent de la classe `RobotAgent`. On définit les attributs et méthodes communs à tous les robots:
- Dans la fonction __init__, on initialise les attributs de chaque robot: 
    - `knowledge` : dictionnaire contenant les informations collectées par le robot sur son environnement.
    - `inventory` : liste contenant les déchets collectés par le robot.
    - `distance` : distance parcourue par le robot.

- La méthode `move` permet au robot de se déplacer vers une cellule voisine. Le déplacement est aléatoire et limité en fonction du type de robot et de la zone de radioactivité. 

- La méthode `deliberate` permet au robot de prendre une décision sur l'action à effectuer:
    - Le robot commence par vérifier s'il y a un déchet dans sa cellule actuelle. Si c'est le cas, il collecte le déchet en retournant `pickup`.
    - Si ce n'est pas le cas, le robot vérifie s'il y a un déchet dans une cellule voisine. Si c'est le cas, il se déplace vers la cellule contenant le déchet en retournant `move` dans la direction.
    - Si le robot a un déchet dans son inventaire, il vérifie s'il peut le transformer. Si c'est le cas, il transforme le déchet en retournant `transform` et se dirige vers la zone de dépôt. Sinon il se déplace aléatoirement en retournant `move` pour collecter un autre déchet et permettre la transformation.
    - Ensuite le robot vérifie s'il est dans la zone de dépôt. Si c'est le cas, il dépose le déchet en retournant `drop`. Sinon, il se déplace vers la zone de dépôt en retournant `move_east`.
    - Si aucune action n'est possible, le robot se déplace aléatoirement en retournant `move`.

- La méthode `get_percepts` permet au robot de collecter des informations sur son environnement. 

- Enfin, la méthode `step` est appelée à chaque étape de la simulation: 
    - Le robot collecte des informations sur son environnement via `get_percepts`.
    - On prépare les connaissances du robot dans `knowledge`. (ce qu'il percoit, ce qu'il a dans son inventaire, sa position, sa zone)
    - Le robot prend une décision sur l'action à effectuer via `deliberate`.
    - La méthode `do` du robot est appelée pour effectuer l'action choisie.

Les classes `GreenRobot`, `YellowRobot` et `RedRobot` héritent de la classe `RobotAgent` et redéfinissent la méthode `deliberate` pour prendre en compte les spécificités de chaque type de robot.

---

### 3. objects.py

Le fichier contient les classes des objets statiques de l'environnement:
- `RadioActivity` : classe représentant les zones de radioactivité de la grille. 
- `WasteDisposal` : classe représentant la zone de dépôt des déchets.
- `Waste` : classe représentant les déchets collectés par les robots.

---

### 4. Simulation

La simulation est lancée dans le fichier `server.py` fournissant une interface graphique pour visualiser la simulation. Pour lancer la simulation, il suffit d'exécuter le fichier `server.py`:

```bash
solara run server.py
```

---

## Evaluation

L'évaluation de la simulation se fait en mesurant le nombre de pas nécessaires pour que tous les déchets soient collectés et déposés dans la zone de dépôt. On peut également mesurer la distance parcourue par chaque type de robot pour collecter et déposer les déchets. Pour cette première partie du projet sans communication entre les robots, on obtient en moyenne (sur 10 simulations) les résultats suivants:

Paramètres de la simulation:
- 4 déchets verts, 4 déchets jaunes, 4 déchets rouges
- 1 GreenRobot, 1 YellowRobot, 3 RedRobot

- 305 steps en moyenne
- GreenRobot: 297 de distance moyenne
- YellowRobot: 293 de distance moyenne
- RedRobot: 901 de distance moyenne

---

## Perspectives

Actuellement les robots ne coordonnent pas leurs actions. Ainsi, si il y a plusieurs robots dans la même zone, il y a des cas de figure où la simulation ne peut pas se terminer. Pour la suite du projet, il faudra implémenter un système de communication entre les robots pour qu'ils puissent coordonner leurs actions et éviter les blocages. On pourrait penser à: 
- Les robots partagent leurs connaissances. 
- Un robot 'chef' qui coordonne les actions des autres robots.
- Optimiser les déplacements des robots pour minimiser la distance parcourue si ils ont connaissance de la position des déchets. 

## Stratégie de collecte

Diviser chaque zone en plusieurs sous-zones et assigner un robot à chaque sous-zone. Chaque robot doit se déplacer dans sa sous-zone pour récupérer les informations sur les déchets. On evite les cases déjà visitées par un autre robot.
- Chaque robot doit se déplacer dans sa sous-zone pour récupérer les informations sur les déchets.
- Une fois qu'un robot a collecté un déchet, il doit se déplacer vers la zone de dépôt pour le déposer.
- Une fois qu'un robot a déposé un déchet, il doit se déplacer vers sa sous-zone pour continuer à collecter des déchets.
- Une fois les déchets transformés, le robot communique aux robots de la couleur suivante pour qu'ils viennent les chercher. 
- Ils les déplacent sur la colonne de droite pour les déposer.

### Stratégie de communication

Deux types de messages (performatifs) sont utilisés dans notre système :

1. **REQUEST** : Message de demande qui signale la présence d'un déchet à collecter
   - Utilisé principalement par les robots jaunes pour signaler aux robots rouges qu'un déchet rouge a été déposé
   - Contient la position du déchet, son type et l'horodatage du dépôt

2. **DOING** : Message d'information qui signale qu'un robot est en train de traiter un déchet
   - Utilisé par les robots rouges pour informer les autres robots rouges qu'ils prennent en charge un déchet spécifique
   - Permet d'éviter que plusieurs robots ne ciblent le même déchet
   - Contient la position du déchet, son type et la position actuelle du robot émetteur

La stratégie de communication mise en place est la suivante :

1. **Notification de dépôt** : Lorsqu'un robot jaune dépose un déchet rouge transformé, il envoie un message REQUEST à tous les robots rouges pour signaler la présence de ce déchet.

2. **Coordination des robots rouges** : Quand un robot rouge décide de cibler un déchet, il envoie un message DOING aux autres robots rouges. Ce message permet d'éviter que plusieurs robots ne se dirigent vers le même déchet.

3. **Résolution des conflits** : Si plusieurs robots rouges ciblent le même déchet, une règle de priorité est appliquée :
   - Le robot le plus proche du déchet a la priorité
   - En cas d'égalité de distance, le robot avec l'ID le plus petit a la priorité
   - Les robots qui abandonnent un déchet ciblé continuent leur exploration ou cherchent un autre déchet

4. **Mémorisation des informations** : Les robots rouges mémorisent les informations sur les déchets signalés dans leur base de connaissances (`knowledge`) pour les traiter plus tard s'ils ne sont pas disponibles immédiatement.

Cette stratégie de communication permet d'optimiser la collecte des déchets rouges en évitant les déplacements inutiles et en répartissant efficacement le travail entre les robots rouges. Elle contribue significativement à la réduction du nombre d'étapes nécessaires pour nettoyer l'environnement.

### Implémentation technique

Le système de communication est implémenté grâce à :
- Une classe `MessageService` qui gère l'envoi et la réception des messages
- Une classe `Mailbox` pour chaque robot qui stocke les messages reçus
- Une méthode `process_messages()` dans chaque robot qui traite les messages selon leur type
- Une méthode `send_doing_notification()` qui permet aux robots de signaler leur activité

Les robots verts n'utilisent pas la communication car ils n'ont pas besoin de se coordonner avec d'autres types de robots pour leur tâche de collecte des déchets verts.