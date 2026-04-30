# Rapport Technique - QuestLang Compiler

Ce document détaille l'architecture interne, les choix technologiques, la structure du compilateur et les solutions apportées aux défis rencontrés lors du développement de **QuestLang**.

---

## 1. Choix technologiques (outils, langages)

- **Python (3.10+)** : Choisi comme langage principal pour le développement du compilateur. Python offre une flexibilité exceptionnelle pour le typage dynamique, la manipulation d'arbres (AST) et une riche bibliothèque standard, idéale pour l'analyse lexicale, syntaxique et sémantique.
- **Flask (Python)** : Utilisé comme framework backend léger pour l'interface web (API REST et rendu des templates HTML).
- **HTML5 / CSS3 / JavaScript Vanilla** : Choix délibéré d'éviter les frameworks front-end lourds (comme React ou Angular) au profit d'une interface web performante, simple et directement intégrable via Flask.
- **vis.js** : Librairie JavaScript utilisée pour la visualisation interactive du monde sous forme de graphe, permettant aux utilisateurs d'inspecter les relations complexes entre Quêtes, PNJ et Objets.

---

## 2. Architecture du Compilateur

Le compilateur QuestLang ne repose sur aucun générateur de parseur externe (comme ANTLR, PLY ou YACC). Il s'agit d'un compilateur implémenté "from scratch", permettant un contrôle total sur le pipeline de compilation.

- **Lexer** personnalisé (basé sur les expressions régulières) pour la tokénisation.
- **Parseur LL(1)** de type "Recursive Descent" (descente récursive), permettant des messages d'erreur de syntaxe très précis et personnalisés.

---

## 3. La structure de la grammaire et de l'AST

- **Grammaire EBNF** : Conçue pour être intuitive pour la déclaration d'éléments de jeu de rôle (RPG). Elle permet de déclarer des blocs de type `world`, `quest`, `item`, `npc` et `func`. Elle supporte un système complet d'expressions et d'instructions de contrôle (`if`, `while`, `for`), ainsi que des instructions spécifiques au domaine comme `give` et `take`. (*Voir `docs/GRAMMAIRE_EBNF.md` pour la définition complète*).
- **Arbre Syntaxique Abstrait (AST)** : Construit de manière orientée objet, chaque type de nœud héritant d'une classe de base `ASTNode`. La racine est le `ProgramNode`. Les nœuds stockent leur position (ligne et colonne) dans le code source d'origine pour garantir des remontées d'erreurs précises.

---

## 4. Analyse Sémantique (Les 4 Passes)

Pour s'assurer qu'un monde défini par l'utilisateur ne comporte pas de quêtes inaccessibles, d'objets impossibles à obtenir ou de boucles bloquantes (deadlocks) rendant le jeu injouable, un pipeline sémantique strict en 4 passes a été mis en place :

1. **Résolution des Symboles** : Vérification des doublons et des références indéfinies via une table des symboles.
2. **Accessibilité (Graphes)** : Utilisation d'un algorithme de parcours en profondeur (DFS) itératif (complexité $O(V+E)$) pour vérifier que toutes les quêtes et la condition de victoire sont accessibles depuis l'état de départ.
3. **Économie (Analyse de Flux)** : Vérification de la création de ressources (inflation, déficit d'objets essentiels à la progression).
4. **Détection de Cycles (Deadlocks)** : Implémentation de l'**algorithme de Tarjan** (Recherche des composantes fortement connexes - SCC) pour détecter les interblocages stricts où plusieurs quêtes s'attendent mutuellement.

---

## 5. Les défis rencontrés et solutions apportées

### 5.1 Temps d'exécution de la Compilation (Timeout)
**Problème :** L'analyse de mondes complexes avec des dépendances cycliques importantes entraînait parfois des lenteurs excessives ou des délais d'attente (timeouts) dans l'interface web (limite initiale de 8 secondes).
**Solution :**
- Remplacement d'algorithmes récursifs naïfs par des parcours itératifs ou par l'algorithme de Tarjan beaucoup plus optimisé pour les cycles.
- Ajustement de la configuration de l'interface et optimisation des structures de données (utilisation de dictionnaires et d'ensembles de hash Python `set()`) pour réduire la complexité de l'analyse sémantique.

### 5.2 Génération du Rapport HTML et Expérience Utilisateur (UI)
**Problème :** L'interface web et l'exportation des données de compilation devaient être fluides, et le rapport de compilation devait être facilement partageable.
**Solution :**
- Intégration d'une fonctionnalité `--html` dans la CLI et d'un bouton d'export dans l'interface web pour appeler la méthode `CodeGenerator.to_html()`.
- Implémentation d'un "Mode pas-à-pas" dans l'UI permettant de visualiser le succès ou l'échec des 4 passes sémantiques en temps réel, offrant un retour visuel crucial lors de l'apprentissage du langage.
- Amélioration de la console web avec la propagation exacte des lignes/colonnes d'erreurs (grâce à l'AST) pour placer des marqueurs visuels dans l'éditeur.

---

## 6. Conclusion

Le développement du compilateur **QuestLang** a permis de créer un outil robuste, spécifiquement adapté à la conception de logiques de RPG. En faisant le choix de tout implémenter "from scratch" en Python, le projet a pu intégrer des vérifications sémantiques avancées (accessibilité, économie, détection de deadlocks) garantissant la viabilité d'un monde de jeu avant même son exécution. L'interface web interactive vient sublimer ce moteur d'analyse statique, rendant la création de mondes accessible tout en conservant une grande rigueur technique sous le capot.