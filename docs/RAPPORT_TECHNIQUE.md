# Rapport Technique - QuestLang Compiler

## 1. Introduction

QuestLang est un DSL (Domain-Specific Language) dédié à la description de mondes de jeu RPG. Ce rapport détaille les choix technologiques, la structure de la grammaire et de l'AST, ainsi que les défis rencontrés lors du développement.

## 2. Choix Technologiques

### 2.1 Langage d'implémentation : Python 3.10+

**Pourquoi Python ?**
- Rapidité de prototypage et lisibilité du code
- Gestion native des structures de données complexes (dictionnaires, listes)
- Pas de compilation intermédiaire, cycle de développement rapide
- Bibliothèque standard riche (json, pathlib, unittest)

**Pourquoi pas Flex/Bison ou ANTLR ?**
- Le parser récursif descendant manuel offre un contrôle total sur la récupération d'erreurs
- Moins de boilerplate pour un projet de cette taille
- Meilleure compréhension pédagogique du processus de compilation

### 2.2 Architecture du compilateur

```
Source .ql -> Lexer (automate à états) -> Parser LL(1) -> AST -> 4 Passes Sémantiques -> IR JSON + Rapport HTML
```

### 2.3 Interface Web

- **Flask** : micro-framework léger, zéro configuration
- **CodeMirror** : éditeur de code dans le navigateur avec syntax highlighting personnalisé
- **vis.js** : visualisation de graphes interactifs pour la carte du monde
- **Chart.js** : graphiques de métriques (répartition, économie)

## 3. Structure de la Grammaire

Voir le fichier `GRAMMAIRE_EBNF.md` pour la grammaire complète en notation EBNF.

### 3.1 Points clés de la grammaire

- **LL(1)** : Grammaire sans récursivité à gauche, adaptée au parser récursif descendant
- **Précédence des opérateurs** : 8 niveaux de précédence (not > ^ > */% > +- > comparaisons > égalité > and > or)
- **Blocs déclaratifs** : `world`, `quest`, `item`, `npc` avec corps typés
- **Scripts impératifs** : variables, contrôle de flux, fonctions utilisateur

### 3.2 Récupération d'erreurs syntaxiques

Le parser utilise une stratégie de **synchronisation par panic mode** :
- En cas d'erreur, consommation des tokens jusqu'au prochain point de synchronisation (`;` ou `}`)
- Reprise de l'analyse sans abandonner la compilation
- Rapport de toutes les erreurs détectées, pas seulement la première

## 4. Structure de l'AST

### 4.1 Hiérarchie des nœuds

```
Program
├── WorldNode (name, start, start_gold, win_condition)
├── QuestNode (id, title, desc, requires[], unlocks[], rewards, costs, script)
├── ItemNode (id, title, value, stackable, type)
├── NPCNode (id, title, location, gives_quest[])
└── FuncNode (name, params[], body)

Script (body)
├── VarDecl (name, type, init)
├── Assignment (target, value)
├── IfStmt (condition, then_branch, else_branch)
├── WhileStmt (condition, body)
├── ForStmt (var, iterable, body)
├── GiveStmt (resource, amount)
├── TakeStmt (resource, amount)
├── CallStmt (func_name, args[])
├── ReturnStmt (value)
└── ExprStmt

Expressions
├── BinaryOp (op, left, right)
├── UnaryOp (op, operand)
├── Literal (value, type)
├── VariableRef (name)
└── FuncCall (name, args[])
```

### 4.2 Pattern Visitor

L'AST implémente le pattern **Visitor** pour les traversées :
- `SemanticVisitor` : 4 passes d'analyse sémantique
- `CodeGenVisitor` : génération de l'IR JSON
- `HTMLReportVisitor` : génération du rapport HTML

## 5. Les 4 Passes Sémantiques

### 5.1 Passe 1 - Table des symboles

**Algorithme** : Parcours de l'AST avec insertion dans une table de hachage

**Détections** :
- Doublons de quêtes, items, PNJ, fonctions
- Références indéfinies (start, win_condition, requires, unlocks, rewards, costs)
- Appels de fonctions inexistantes

**Complexité** : O(n) où n = nombre de déclarations

### 5.2 Passe 2 - Accessibilité

**Algorithme** : DFS itératif sur le graphe de quêtes

**Détections** :
- Quêtes inaccessibles depuis le point de départ
- Condition de victoire jamais atteignable
- Quêtes accessibles sans récompense (avertissement)

**Complexité** : O(V + E) où V = quêtes, E = liens requires/unlocks

### 5.3 Passe 3 - Économie

**Algorithme** : Analyse de flux avec accumulation

**Détections** :
- Déficit d'item (consommé plus que produit)
- Surplus d'item (produit sans jamais être consommé)
- Inflation d'or (ratio injecté/consommé > 10)
- Déflation d'or (ratio < 0.5)

**Complexité** : O(n) où n = nombre de quêtes

### 5.4 Passe 4 - Cycles

**Algorithme** : Tarjan Strongly Connected Components (SCC)

**Détections** :
- Cycles de dépendances mutuelles (deadlock narratif)
- Boucles d'unlock (avertissement)
- Items déclarés mais jamais utilisés
- PNJ qui ne donnent aucune quête

**Complexité** : O(V + E)

## 6. Génération de Code

### 6.1 IR JSON

L'IR (Intermediate Representation) est un document JSON structuré contenant :
- Le monde avec ses propriétés
- Les quêtes avec leurs dépendances et récompenses
- Les items avec leurs caractéristiques
- Les PNJ avec leurs liens

Cette représentation est **machine-readable** et peut servir de base à :
- Un moteur de jeu
- Une base de données de contenu
- Un générateur de rapports

### 6.2 Rapport HTML

Le rapport HTML contient :
- Le graphe de dépendances des quêtes (vis.js)
- La liste des erreurs et avertissements
- Les métriques du monde

## 7. Défis Rencontrés et Solutions

### 7.1 Récupération d'erreurs syntaxiques

**Problème** : Le parser s'arrêtait à la première erreur.
**Solution** : Implémentation du panic mode avec points de synchronisation (`;`, `}`). Le parser consomme les tokens jusqu'au prochain point sûr et continue l'analyse.

### 7.2 Détection des quêtes inaccessibles

**Problème** : Comment détecter efficacement les quêtes qui ne sont jamais atteignables.
**Solution** : Modélisation du monde sous forme de graphe dirigé (quêtes = nœuds, requires/unlocks = arêtes) puis DFS depuis le point de départ. Les nœuds non visités sont inaccessibles.

### 7.3 Analyse de l'économie

**Problème** : Comment détecter les déséquilibres économiques (inflation, déficit).
**Solution** : Accumulation des flux d'or et d'items sur l'ensemble des quêtes. Calcul du ratio injecté/consommé pour l'or et des bilans par item.

### 7.4 Détection des cycles

**Problème** : Détecter les dépendances circulaires entre quêtes (A nécessite B, B nécessite A).
**Solution** : Algorithme de Tarjan pour les composantes fortement connexes. Toute SCC de taille > 1 contient un cycle.

### 7.5 Interface web interactive

**Problème** : Comment visualiser le graphe de quêtes de manière intuitive.
**Solution** : Utilisation de vis.js avec layout hiérarchique dirigé. Filtres interactifs par type de nœud. Simulation du déroulement du monde avec évolution de l'inventaire.

## 8. Tests et Validation

### 8.1 Couverture des tests

- **6 tests lexer** : tokens, mots-clés, commentaires, nombres, chaînes, localisation
- **7 tests parser** : quêtes, world, items, PNJ, récompenses, scripts, fonctions
- **3 tests sémantiques Passe 1** : doublons, références indéfinies
- **3 tests sémantiques Passe 2** : accessibilité, victoire inaccessible, sans récompense
- **2 tests sémantiques Passe 3** : déficit d'items, inflation d'or
- **2 tests sémantiques Passe 4** : deadlock, items morts
- **4 tests d'intégration** : pipeline complet, HTML, JSON, monde brisé

### 8.2 Cas de test

- `valid_world.ql` : Monde cohérent avec 3 quêtes, 3 items, 1 PNJ
- `broken_world.ql` : Monde avec erreurs intentionnelles pour tester la robustesse

## 9. Conclusion

QuestLang démontre la conception complète d'un compilateur pour un DSL spécialisé, de l'analyse lexicale à la génération de code intermédiaire, en passant par quatre passes d'analyse sémantique avancée. L'interface web interactive et la simulation du monde ajoutent une dimension innovante au projet.
