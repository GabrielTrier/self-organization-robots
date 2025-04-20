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

### Schéma UML


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

## Stratégie de collecte

## Stratégie sans communication

Cette section détaille la stratégie de collecte et de transformation des déchets mise en œuvre lorsque les robots n'ont pas la capacité de communiquer entre eux. La coordination est implicite, basée sur des rôles et des zones d'opération distincts, en particulier lorsqu'il y a plusieurs robots d'une même couleur (vert ou jaune).

### Découpage des zones et rôles spécifiques (Cas Multi-Agents)

L'environnement de la grille (9x15) est divisé en trois zones verticales principales : z1 (vert), z2 (jaune), z3 (rouge). La gestion des zones z1 et z2 s'adapte au nombre de robots :

- **Un seul robot (`AloneGreen`, `AloneYellow`)**:
    - **Zone**: Le robot est responsable de l'intégralité de sa zone principale (z1 ou z2).
    - **Rôle**: Il explore toute la zone (mouvement en serpentin), collecte les déchets de sa couleur, les transforme lui-même (2 verts -> 1 jaune ou 2 jaunes -> 1 rouge), se déplace vers la colonne la plus à droite de sa zone, et y dépose le déchet *transformé*.

- **Plusieurs robots (`GreenGather`, `YellowGather` - N > 1)**:
    - **Division des Rôles et Zones**:
        - **1 Robot "Transformeur"**: Un des robots est assigné à la colonne la plus à droite de la zone principale (colonne `width // 3 - 1` pour z1, colonne `2 * width // 3 - 1` pour z2).
            - **Rôle**: Ce robot ne collecte pas dans la zone principale. Il patrouille verticalement dans sa colonne assignée. Sa tâche est de ramasser les déchets *non transformés* déposés par les autres robots, de les transformer (2 verts -> 1 jaune ou 2 jaunes -> 1 rouge), puis de déposer le déchet *transformé* dans cette même colonne.
        - **N-1 Robots "Collecteurs"**: Les autres N-1 robots se partagent le reste de la zone principale (colonnes 0 à `width // 3 - 2` pour z1, colonnes `width // 3` à `2 * width // 3 - 2` pour z2). Cette aire est divisée horizontalement en N-1 sous-zones (bandes).
            - **Rôle**: Chaque collecteur explore sa sous-zone assignée (mouvement en serpentin ou similaire). Dès qu'il ramasse un déchet de sa couleur, il *ne le transforme pas*. Il se dirige directement vers la colonne du "Transformeur" (la colonne la plus à droite de la zone principale) et y dépose le déchet *non transformé*.

### Types d’agents et comportements détaillés

- **`AloneGreen` / `AloneYellow`**:
    - **Comportement**: Implémentent le cycle complet : exploration (serpentin via `move`), collecte (`deliberate`), transformation (`deliberate` retourne `transform`), déplacement vers la colonne de droite (`move_east`), et dépôt du déchet transformé (`deliberate` retourne `drop`).
- **`GreenGather` / `YellowGather` (selon leur rôle assigné)**:
    - **Robot "Transformeur" (1 par zone)**:
        - **Zone Assignée**: La colonne la plus à droite de z1 ou z2.
        - **Comportement `move`**: Déplacement principalement vertical dans cette colonne.
        - **Comportement `deliberate`**: Cherche les déchets non transformés de sa couleur sur sa case. S'il en trouve deux, il retourne `{"action": "pickup", ...}` pour les ramasser (potentiellement sur plusieurs étapes). Une fois deux déchets en inventaire, il retourne `{"action": "transform", ...}`. Ensuite, il retourne `{"action": "drop", ...}` pour déposer le déchet transformé sur sa case (si vide).
    - **Robots "Collecteurs" (N-1 par zone)**:
        - **Zone Assignée**: Une sous-zone horizontale dans la partie gauche de z1 ou z2.
        - **Comportement `move`**: Exploration de type serpentin ou similaire dans la sous-zone assignée.
        - **Comportement `deliberate`**: Cherche un déchet de sa couleur sur sa case. S'il en trouve un et que l'inventaire est vide, il retourne `{"action": "pickup", ...}`. S'il a un déchet non transformé en inventaire, il retourne `{"action": "move_east"}` pour se diriger vers la colonne du Transformeur. Arrivé dans cette colonne, il retourne `{"action": "drop", ...}` pour déposer le déchet *non transformé*.
- **`RedRobot`**:
    - **Rôle**: Collecter les déchets rouges (initiaux en z3 ou ceux transformés et déposés par les `YellowRobot` Transformeurs dans la colonne `2 * width // 3 - 1`) et les amener à la zone de dépôt finale (dernière colonne).
    - **Comportement spécifique (sans communication)**: Déplacement aléatoire pour chercher les déchets rouges. Se dirige vers la zone de dépôt (`move_east`) lorsqu'il transporte un déchet.

### Déplacement

- **`AloneGreen` / `AloneYellow` / Robots Collecteurs (`Gather`)**: Leur méthode `move` implémente un déplacement en serpentin ou exploratoire pour couvrir leur zone/sous-zone assignée.
- **Robot Transformeur (`Gather`)**: Sa méthode `move` implémente un déplacement principalement vertical dans la colonne la plus à droite de z1 ou z2.
- **`RedRobot` (sans communication)**: Déplacement aléatoire contrôlé par défaut. `deliberate` peut initier un `move_east` ciblé.
- **Évitement**: Tous les robots vérifient l'occupation de la case cible avant de bouger.


---

## Stratégie avec communication

Cette section décrit la stratégie améliorée où les robots rouges utilisent la communication pour coordonner plus efficacement la collecte des déchets rouges déposés par les robots Transformeurs jaunes.

### Ajouts par rapport à la version sans communication

La communication impacte principalement les `RedRobot` :
- **Notification de dépôt**: Le `RobotModel` notifie les `RedRobot` (`REQUEST`) lorsqu'un Transformeur `YellowGather` (ou `AloneYellow`) dépose un déchet rouge dans la colonne `2 * width // 3 - 1`.
- **Prise en charge ciblée**: Les `RedRobot` ciblent un déchet spécifique (`self.target_waste`) et s'y dirigent (pathfinding simple).
- **Résolution de conflits (`DOING`)**: Un `RedRobot` ciblant un déchet notifie les autres. Le plus proche (ou plus petit ID) garde la cible, les autres abandonnent.
- **Partage d'informations**: Évite les efforts redondants.
- **Mémorisation**: Mémorisation des déchets signalés mais non ciblés (`knowledge["waste_locations"]`).

### Types de messages et Performatifs

- **`REQUEST`**: Diffusé par `RobotModel` lors d'un dépôt de déchet rouge par un `YellowRobot` (Transformeur ou Alone). Contient `{"waste_pos": (x, y), "waste_type": "red"}`. Destiné aux `RedRobot`.
- **`DOING`**: Envoyé par un `RedRobot` prenant en charge un déchet. Contient `{"waste_pos": (x, y), "waste_type": "red", "agent_pos": self.pos}`. Destiné aux autres `RedRobot`.

### Processus de communication et Coordination (`RedRobot`)

1.  **Notification (`REQUEST`)**: Dépôt Rouge -> `RobotModel.notify_waste_drop` -> `MessageService` -> `REQUEST` aux `RedRobot`.
2.  **Traitement (`RedRobot.process_messages`)**:
    - Traite `DOING` (résolution conflits via distance/ID). Met à jour `self.target_waste`.
    - Traite `REQUEST` (si pas de cible et vide) -> stocke dans `knowledge["waste_locations"]`.
3.  **Décision (`RedRobot.deliberate`)**:
    - Priorités: Pickup local -> Suivre `target_waste` (envoyer `DOING` si besoin) -> Choisir cible depuis `knowledge["waste_locations"]` (définir `target_waste`, envoyer `DOING`) -> Déposer si plein et zone dépôt -> Exploration.
4.  **Notification d'intention (`RedRobot.send_doing_notification`)**: Envoie `DOING`.

### Implémentation Technique

- **`CommunicatingAgent`**, **`Mailbox`**, **`MessageService`**, **`Message`**: Infrastructure.
- **`RedRobot.process_messages`**: Logique de traitement.
- **`RedRobot.send_doing_notification`**: Envoi `DOING`.
- **`RobotModel.notify_waste_drop`**: Déclencheur `REQUEST`.
- **`RedRobot.deliberate`**: Intègre ciblage et pathfinding simple.

### Cas Particuliers

- Seuls les `RedRobot` traitent/envoient activement des messages.
- Les `YellowRobot` (Transformeurs ou Alone) déclenchent les `REQUEST` par leurs dépôts.
- Les `GreenRobot` sont exclus.

### Schémas UML

Ci-dessous le schéma UML du projet, incluant les classes de communication, les agents et les objets de l'environnement:
![img](/img/uml.png)

### Évaluation

1. 1 agent de chaque couleur
Pour la configuartion suivante:
- 4 déchets verts, 4 déchets jaunes, 4 déchets rouges
- 1 GreenRobot, 1 YellowRobot, 3 RedRobot

On obtient en moyenne (sur 10 simulations) les résultats suivants:
- 105 steps en moyenne
- GreenRobot: 187 de distance moyenne
- YellowRobot: 172 de distance moyenne
- RedRobot: 142 de distance moyenne

Ci-dessous l'évolution du nombre de déchets par couleur au cours de la simulation avec cette configuration:
![img1](/img/img1.png)

2. 2 agents de chaque couleur
Pour la configuartion suivante:
- 4 déchets verts, 4 déchets jaunes, 4 déchets rouges
- 2 GreenRobot, 2 YellowRobot, 2 RedRobot

On obtient en moyenne (sur 10 simulations) les résultats suivants:
- 108 steps en moyenne
- GreenRobot: 384 de distance moyenne en cumul
- YellowRobot: 359 de distance moyenne en cumul
- RedRobot: 203 de distance moyenne en cumul

Ci-dessous l'évolution du nombre de déchets par couleur au cours de la simulation avec cette configuration:
![img2](/img/img2.png)

3. 3 agents de chaque couleur
Pour la configuartion suivante:
- 4 déchets verts, 4 déchets jaunes, 4 déchets rouges
- 3 GreenRobot, 3 YellowRobot, 3 RedRobot

On obtient en moyenne (sur 10 simulations) les résultats suivants:
- 79 steps en moyenne
- GreenRobot: 399 de distance moyenne en cumul
- YellowRobot: 381 de distance moyenne en cumul
- RedRobot: 209 de distance moyenne en cumul

Ci-dessous l'évolution du nombre de déchets par couleur au cours de la simulation avec cette configuration:
![img3](/img/img3.png)

### Conclusion

Les résultats montrent que l'approche avec communication et une stratégie de collecte ciblée améliore la simulation de manière générale. En effet, la stratégie et la communication permettent d'abord de mettre plusieurs agents de la même couleur sur le terrain, ce qui permet d'augmenter le nombre de déchets collectés et déposés. Ensuite, la communication entre les agents permet de réduire le nombre de pas nécessaires pour collecter et déposer les déchets. Enfin, la stratégie de collecte ciblée permet d'optimiser le parcours des agents et donc de réduire la distance parcourue par chaque agent unique. 

