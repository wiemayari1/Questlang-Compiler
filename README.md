# QuestLang Forge - Compilateur pour Mondes RPG

QuestLang est un langage dédié (DSL) pour décrire des mondes de jeu RPG. Il permet de déclarer des quêtes, des objets, des personnages non-joueurs (PNJ) et de vérifier automatiquement la cohérence du monde à la compilation grâce à quatre passes d'analyse sémantique rigoureuses.

---

## Aperçu du Pipeline

QuestLang transforme un fichier texte décrivant un monde en une représentation intermédiaire JSON (IR) vérifiée, avec détection des erreurs lexicales, syntaxiques et sémantiques.

```text
Source .ql -> Lexer -> Parser -> AST -> 4 Passes Sémantiques -> IR JSON + Rapport HTML
```

---

## Fonctionnalités

### Langage QuestLang

- **Déclarations** : `world`, `quest`, `item`, `npc`
- **Variables et types** : `var`, `int`, `float`, `bool`, `string`, `list`
- **Expressions** : arithmétiques, logiques, comparaisons
- **Contrôle** : `if`/`else`, `while`, `for`/`in`
- **Fonctions** : `func` avec paramètres et `return`
- **Instructions spéciales** : `give`, `take`, `call`

### Pipeline Sémantique et Analyse Statique

QuestLang effectue une vérification approfondie de la cohérence de la logique de jeu, rendant impossible la création d'un jeu "cassé".

| Passe | Algorithme | Détection |
|-------|------------|-----------|
| 1 - Symboles | Table des symboles | Doublons, références indéfinies |
| 2 - Accessibilité | DFS itératif O(V+E) | Quêtes inaccessibles, condition de victoire inaccessible |
| 3 - Économie | Analyse de flux | Inflation d'or, déficit d'items, surplus |
| 4 - Cycles | Tarjan SCC O(V+E) | Interblocages (Deadlocks), items morts, PNJ inutiles |

---

## Prérequis

- Python **3.10 ou supérieur**
- Un navigateur moderne (Chrome, Firefox, Edge) pour l'interface graphique.

---

## Installation et Lancement sur Windows

### 1. Ouverture du projet
1. Téléchargez ou clonez le projet sur votre machine :
```cmd
git clone https://github.com/wiemayari1/Questlang-Compiler.git
cd Questlang-Compiler
```
2. Ouvrez ce dossier dans votre éditeur de code préféré (ex: **Visual Studio Code**). Si vous avez VS Code installé, tapez simplement :
```cmd
code .
```

### 2. Interface Web (Recommandé)
Créez un environnement virtuel et installez les dépendances :
```cmd
cd web
py -3 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Lancez le serveur Flask :
```cmd
py -3 app.py
```
Ouvrez votre navigateur et allez sur : **http://127.0.0.1:5000**

### 3. Ligne de commande (CLI) et Rapport HTML
Le compilateur en ligne de commande ne nécessite aucune dépendance externe.
```cmd
cd ..
py -3 questlang.py examples\valid_world.ql
```

**Générer un Rapport HTML :**
Le compilateur QuestLang inclut un générateur de rapport HTML (voir le schéma du pipeline). Pour l'obtenir, utilisez simplement l'option `--html` :
```cmd
py -3 questlang.py examples\valid_world.ql --html
```
Cela créera un fichier `.report.html` dans le répertoire courant !

---

## Installation et Lancement sur Ubuntu / Linux

### 1. Ouverture du projet
1. Ouvrez votre terminal et clonez le dépôt :
```bash
git clone https://github.com/wiemayari1/Questlang-Compiler.git
cd Questlang-Compiler
```
2. Ouvrez le dossier dans votre éditeur de code (ex: **VS Code**) :
```bash
code .
```
Assurez-vous que le paquet `python3-venv` est installé :
```bash
sudo apt update
sudo apt install python3-venv python3-pip
```

### 2. Interface Web (Recommandé)
Créez un environnement virtuel et installez les dépendances :
```bash
cd web
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Lancez le serveur Flask :
```bash
python3 app.py
```
Ouvrez votre navigateur et allez sur : **http://127.0.0.1:5000**

### 3. Ligne de commande (CLI) et Rapport HTML
```bash
cd ..
python3 questlang.py examples/valid_world.ql
```

**Générer un Rapport HTML :**
Le compilateur QuestLang inclut un générateur de rapport HTML. Pour l'obtenir, utilisez l'option `--html` :
```bash
python3 questlang.py examples/valid_world.ql --html
```
Cela générera un fichier `.report.html` contenant l'analyse complète de la compilation.

---

## Interface Web - QuestLang Forge

L'interface graphique interactive permet d'éditer, compiler et visualiser les mondes QuestLang dans le navigateur.

### Fonctionnalités de l'interface

**Éditeur de Code Intégré**
- Coloration syntaxique QuestLang personnalisée.
- Marqueurs d'erreurs en temps réel (lignes/colonnes) signalant les échecs lexicaux et syntaxiques.
- Chargement d'exemples pré-faits depuis le serveur.

**Analyse du Pipeline**
- Dashboard interactif illustrant le pipeline de compilation (Lexical -> Syntaxique -> Sémantique -> Génération).
- Les étapes s'affichent en rouge ou en vert selon la réussite.
- Mode pas-à-pas pour inspecter visuellement les résultats des 4 passes sémantiques.

**Carte du Monde (Graphe)**
- Graphe interactif des quêtes, objets et PNJ (propulsé par vis.js).
- Filtres pour afficher ou masquer dynamiquement certains types de nœuds (PNJ, Items, Quêtes).

**Console Intégrée**
- Journal de compilation détaillé avec horodatage.
- Messages d'avertissement et d'erreurs formidables pointant directement la localisation du code.

---

## Structure du projet

```text
questlang/
|-- questlang.py              # CLI principal
|-- src/
|   |-- errors.py             # Gestion des erreurs (Lexical, Syntax, Semantic, Generation)
|   |-- lexer.py              # Analyse lexicale
|   |-- parser.py             # Analyse syntaxique LL(1)
|   |-- ast_nodes.py          # Nœuds de l'AST
|   |-- semantic.py           # 4 passes sémantiques
|   |-- codegen.py            # Génération IR JSON + HTML
|   |-- optimizer.py          # Optimisation de l'AST
|-- tests/
|   |-- test_compiler.py      # Tests unitaires et d'intégration
|-- examples/
|   |-- valid_world.ql        # Exemple de monde valide
|   |-- erreur_lexicale.ql    # Exemple d'erreur lexicale
|   |-- erreur_syntaxique.ql  # Exemple d'erreur de syntaxe
|   |-- monde_inaccessible.ql # Exemple d'erreur sémantique
|-- web/
|   |-- app.py                # Serveur Flask (API REST)
|   |-- requirements.txt      # Dépendances web
|   |-- templates/
|   |   |-- index.html        # Interface graphique
|   |-- static/
|   |   |-- css/style.css     # Thème immersif
|   |   |-- js/main.js        # Logique frontend
|-- docs/
|   |-- RAPPORT_TECHNIQUE.md  # Rapport technique approfondi
|   |-- GRAMMAIRE_EBNF.md     # Grammaire du DSL
|-- README.md
```

---

## Auteurs

Ayari Wiem / Ourari Ranim / Ayadi Soumaya / Sakroufi Aya
