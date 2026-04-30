# Rapport Technique - QuestLang Compiler

## 1. Introduction

QuestLang est un langage spécifique au domaine (DSL) conçu spécifiquement pour la description formelle de mondes de jeux de rôle (RPG).

Ce projet implémente un compilateur complet, incluant l'analyse lexicale, syntaxique, sémantique, et la génération de code. Le compilateur traduit un fichier source `.ql` en une représentation intermédiaire JSON (IR) rigoureusement vérifiée, accompagnée d'un graphe visuel et d'une interface web.

L'objectif majeur de QuestLang est de garantir la cohérence logique d'un monde RPG avant son exécution (ex. quêtes inaccessibles, inflation de ressources, interblocages).

---

## 2. Architecture du Compilateur

Le compilateur suit une architecture modulaire classique, structurée autour d'un pipeline séquentiel :

- **Lexer (Analyseur Lexical)** : Transforme le code source brut en une séquence de tokens (mots-clés, identifiants, valeurs).
- **Parser (Analyseur Syntaxique)** : Vérifie l'ordre des tokens selon une grammaire `LL(1)` et génère un Arbre Syntaxique Abstrait (AST).
- **Analyseur Sémantique** : Parcourt l'AST à travers quatre passes distinctes pour valider la logique du jeu.
- **Optimiseur** : Simplifie l'AST (ex: Constant Folding) pour optimiser les performances futures.
- **Générateur de Code** : Transforme l'AST validé en une représentation JSON lisible par les moteurs de jeux (IR).

---

## 3. Choix Technologiques

| Technologie | Usage |
|-------------|-------|
| **Python (3.10+)** | Langage principal du compilateur. Flexibilité du typage dynamique, manipulation d'arbres (AST), bibliothèque standard riche. |
| **Flask** | Framework backend léger pour l'interface web (API REST et rendu des templates HTML). |
| **HTML5 / CSS3 / JavaScript Vanilla** | Interface web performante et légère, directement intégrable via Flask. |
| **vis.js** | Visualisation interactive du monde sous forme de graphe (relations Quêtes, PNJ, Objets). |

---

## 4. Grammaire et AST

### 4.1 Grammaire EBNF

Conçue pour être intuitive pour la déclaration d'éléments de RPG. Elle permet de déclarer des blocs de type `world`, `quest`, `item`, `npc` et `func`.

Supporte :
- Un système complet d'expressions et d'instructions de contrôle (`if`, `while`, `for`)
- Des instructions spécifiques au domaine comme `give` et `take`

> *Voir `docs/GRAMMAIRE_EBNF.md` pour la définition complète.*

### 4.2 Arbre Syntaxique Abstrait (AST)

- Construit de manière orientée objet
- Chaque type de nœud hérite d'une classe de base `ASTNode`
- La racine est le `ProgramNode`
- Les nœuds stockent leur position (ligne et colonne) dans le code source d'origine pour garantir des remontées d'erreurs précises

---

## 5. Analyse Sémantique (Les 4 Passes)

Pour s'assurer qu'un monde défini par l'utilisateur ne comporte pas de quêtes inaccessibles, d'objets impossibles à obtenir ou de boucles bloquantes (deadlocks) rendant le jeu injouable, un pipeline sémantique strict en 4 passes a été mis en place :

### 5.1 Résolution des Symboles

Vérification des doublons et des références indéfinies via une table des symboles.

### 5.2 Accessibilité (Graphes)

Utilisation d'un algorithme de parcours en profondeur (DFS) itératif (complexité **O(V+E)**) pour vérifier que toutes les quêtes et la condition de victoire sont accessibles depuis l'état de départ.

### 5.3 Économie (Analyse de Flux)

Vérification de la création de ressources :
- Inflation de ressources
- Déficit d'objets essentiels à la progression

### 5.4 Détection de Cycles (Deadlocks)

Implémentation de l'**algorithme de Tarjan** (Recherche des composantes fortement connexes - SCC) pour détecter les interblocages stricts où plusieurs quêtes s'attendent mutuellement.

---

## 6. Défis Rencontrés et Solutions

### 6.1 Temps d'Exécution de la Compilation (Timeout)

**Problème :** L'analyse de mondes complexes avec des dépendances cycliques importantes entraînait parfois des lenteurs excessives ou des délais d'attente (timeouts) dans l'interface web (limite initiale de 8 secondes).

**Solution :**
- Remplacement d'algorithmes récursifs naïfs par des parcours itératifs ou par l'algorithme de Tarjan beaucoup plus optimisé pour les cycles.
- Ajustement de la configuration de l'interface et optimisation des structures de données (utilisation de dictionnaires et d'ensembles de hash Python `set()`) pour réduire la complexité de l'analyse sémantique.

### 6.2 Génération du Rapport HTML et Expérience Utilisateur (UI)

**Problème :** L'interface web et l'exportation des données de compilation devaient être fluides, et le rapport de compilation devait être facilement partageable.

**Solution :**
- Intégration d'une fonctionnalité `--html` dans la CLI et d'un bouton d'export dans l'interface web pour appeler la méthode `CodeGenerator.to_html()`.
- Implémentation d'un **"Mode pas-à-pas"** dans l'UI permettant de visualiser le succès ou l'échec des 4 passes sémantiques en temps réel, offrant un retour visuel crucial lors de l'apprentissage du langage.
- Amélioration de la console web avec la propagation exacte des lignes/colonnes d'erreurs (grâce à l'AST) pour placer des marqueurs visuels dans l'éditeur.

---

## 7. Conclusion

Le développement du compilateur **QuestLang** a permis de créer un outil robuste, spécifiquement adapté à la conception de logiques de RPG.

En faisant le choix de tout implémenter "from scratch" en Python, le projet a pu intégrer des vérifications sémantiques avancées (accessibilité, économie, détection de deadlocks) garantissant la viabilité d'un monde de jeu avant même son exécution.

L'interface web interactive vient sublimer ce moteur d'analyse statique, rendant la création de mondes accessible tout en conservant une grande rigueur technique sous le capot.
