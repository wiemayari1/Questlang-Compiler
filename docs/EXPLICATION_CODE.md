# Explication Détaillée du Projet et du Code source (QuestLang)

Ce document plonge dans le cœur de **QuestLang**, expliquant comment le projet est structuré, comment le code fonctionne, et la logique derrière chaque étape du compilateur.

---

## 1. Vue d'Ensemble du Projet

**QuestLang** n'est pas un jeu, mais un **Langage Dédié (DSL - Domain Specific Language)**. Son but est de permettre aux concepteurs de jeux (Game Designers) de décrire la logique d'un monde RPG (Quêtes, Objets, PNJ, Conditions de victoire) via un script textuel simple.
Ensuite, le **Compilateur QuestLang** lit ce texte et s'assure qu'il n'y a aucune erreur de logique (ex: une quête impossible à atteindre, un objet manquant pour finir le jeu, une boucle infinie de quêtes qui se bloquent mutuellement). Si le monde est valide, il génère un fichier JSON (Intermediate Representation) utilisable par un vrai moteur de jeu (Unity, Godot, Unreal) pour générer le jeu.

---

## 2. Le Pipeline de Compilation (Comment ça marche sous le capot ?)

Le cœur du compilateur (situé dans le dossier `src/`) fonctionne de manière séquentielle, selon un modèle classique de compilation en 4 grandes étapes :

### Étape 1 : L'Analyse Lexicale (`src/lexer.py`)
Le **Lexer** lit le fichier texte source `.ql` caractère par caractère. Son rôle est de regrouper ces caractères en mots ou symboles compréhensibles, appelés **Tokens**.
- *Exemple* : Il transforme la chaîne `quest depart {` en trois tokens : `[KEYWORD:quest]`, `[IDENTIFIER:depart]`, `[SYMBOL:{]`.
- Le lexer de QuestLang est construit "from scratch" en utilisant des expressions régulières (Regex) en Python. Si un caractère n'appartient pas au langage (ex: un symbole `§`), il lève une **Erreur Lexicale**.

### Étape 2 : L'Analyse Syntaxique (`src/parser.py` et `src/ast_nodes.py`)
Le **Parseur** prend la liste de tokens générée par le lexer et vérifie que les mots sont placés dans un ordre grammaticalement correct. 
- Il s'agit d'un parseur de type **LL(1) à descente récursive**. Cela signifie qu'il lit les tokens de gauche à droite, et construit l'arbre de haut en bas en ne regardant qu'un seul token à l'avance pour savoir quelle règle appliquer.
- En lisant les tokens, il construit un **AST (Abstract Syntax Tree)**. C'est un arbre en mémoire (défini dans `ast_nodes.py`) où chaque élément du jeu (Quête, Objet, Condition `if`) devient un objet Python typé (`QuestNode`, `ItemNode`, `IfNode`).
- Grâce à la méthode `to_dict()` intégrée à l'`ASTNode`, cet arbre est facilement transformable en JSON.

### Étape 3 : L'Analyse Sémantique (`src/semantic.py`)
C'est le "cerveau" principal du projet. Avoir une grammaire correcte ne veut pas dire que la logique du jeu a du sens. Le module sémantique parcourt l'AST en **4 passes successives** :
1. **Passe des Symboles** : Vérifie que tout ce qui est utilisé a été déclaré. *Exemple : La quête A requiert une "potion_magique". Est-ce que "potion_magique" existe dans l'AST des Items ?*
2. **Passe d'Accessibilité (DFS)** : Construit un graphe orienté en mémoire. En partant de l'état "start", il fait un Parcours en Profondeur (Depth-First Search) pour s'assurer qu'il existe un chemin valide pour atteindre la `win_condition` et pour débloquer toutes les autres quêtes.
3. **Passe d'Économie** : Simule les échanges. Elle vérifie si une quête demande 50 pièces d'or (`costs: gold 50`) alors que le joueur ne peut potentiellement en gagner que 20 dans tout le jeu (Déficit).
4. **Passe des Cycles / Deadlocks (Tarjan)** : Utilise l'algorithme des Composantes Fortement Connexes de Tarjan. Il détecte si des quêtes forment une boucle bloquante. *Exemple : La quête A a besoin que la quête B soit finie, mais la quête B requiert la quête A.*

### Étape 4 : La Génération de Code (`src/codegen.py`)
Si toutes les passes sémantiques sont au vert, l'AST et les données sémantiques sont passés au Code Generator.
- Il génère l'**IR (Représentation Intermédiaire)** sous format JSON.
- Il inclut la fonction `to_html()`, capable de recracher un rapport stylisé de compilation expliquant au concepteur ce qui s'est passé.

---

## 3. Architecture du Projet (Structure des dossiers)

Voici le rôle exact de chaque partie du dépôt Git :

### `/src/` - Le cœur du moteur
- `ast_nodes.py` : Définit toutes les classes pour l'arbre syntaxique (Les briques de données).
- `lexer.py` / `parser.py` : Les deux fichiers responsables de lire le texte et de construire l'AST.
- `semantic.py` : Les algorithmes de validation de logique de jeu (Graphes, Tarjan, DFS).
- `codegen.py` : Exportation des résultats.
- `errors.py` : Définit les exceptions (`LexicalError`, `SyntaxError`, `SemanticError`) qui stockent spécifiquement la ligne, la colonne et le message d'erreur.
- `optimizer.py` : Module prévu pour optimiser l'AST (comme la simplification des expressions constantes `2+2` -> `4`) avant la génération.
- `interpreter.py` : Un module permettant de potentiellement "jouer" le monde dans le terminal (simulation).

### `/web/` - L'Interface Graphique (IDE interactif)
- `app.py` : Le serveur backend écrit en **Flask (Python)**. Il expose une API REST (`/api/compile`). Lorsqu'on clique sur "Compiler" sur la page web, le JS envoie le code texte au serveur Flask, qui appelle le compilateur (`src/`) et renvoie le JSON de l'AST, les erreurs, et les données du graphe.
- `static/js/main.js` : Le cœur de l'UI. Il gère l'éditeur de texte, souligne les lignes en rouge selon les erreurs renvoyées par Flask, et utilise la librairie `vis.js` pour dessiner les cercles et les flèches dynamiques dans l'onglet "Carte".
- `templates/index.html` : La structure de la page web.
- `static/css/style.css` : Le design "Dark Mode", très soigné et immersif.

### Autres fichiers
- `questlang.py` : Le point d'entrée principal en ligne de commande (CLI). Permet d'utiliser le compilateur dans un terminal sans interface web.
- `/examples/` : Des scripts `.ql` pré-écrits pour tester différents scénarios (monde valide, erreurs lexicales, monde avec un deadlock, etc.).
- `/docs/` : La documentation technique, incluant ce fichier, le rapport technique global, et la grammaire (EBNF).

---

## 4. Ce qui rend ce code robuste

1. **Aucune dépendance externe dans le noyau** : Le compilateur (tout ce qui est dans `src/`) est écrit en Python pur. Cela le rend ultra-léger, portable, et facile à déboguer.
2. **Localisation des erreurs** : Le fait que `lexer.py` sauvegarde la ligne et la colonne de chaque token, et que `parser.py` transmette ces informations aux nœuds de l'`ASTNode`, est la raison pour laquelle l'interface graphique est capable de pointer l'erreur exacte à l'utilisateur.
3. **Séparation des préoccupations (MVC / Pipeline)** : L'analyse lexicale ignore complètement le sens des mots. L'analyse sémantique n'a pas à se soucier du formatage du texte. L'interface Web Flask ignore comment compiler : elle ne fait qu'appeler le code du noyau. Si on veut remplacer Flask par Django, ou faire une interface en C#, le noyau Python n'a pas besoin d'être modifié.
4. **Algorithmes avancés** : L'utilisation de DFS et Tarjan garantit une validation mathématique stricte de l'accessibilité du monde, quelque chose qui serait très complexe à coder avec de simples boucles if/else.
