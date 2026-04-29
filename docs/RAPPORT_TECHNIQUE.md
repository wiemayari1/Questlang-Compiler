# Rapport Technique : QuestLang Compiler

## 1. Introduction

QuestLang est un langage spécifique au domaine (DSL) conçu spécifiquement pour la description formelle de mondes de jeux de rôle (RPG).
Ce projet implémente un compilateur complet, incluant l'analyse lexicale, syntaxique, sémantique, et la génération de code. Le compilateur traduit un fichier source `.ql` en une représentation intermédiaire JSON (IR) rigoureusement vérifiée, accompagnée d'un graphe visuel et d'une interface web.

L'objectif majeur de QuestLang est de garantir la **cohérence logique d'un monde RPG avant son exécution** (ex. quêtes inaccessibles, inflation de ressources, interblocages).

---

## 2. Architecture du Compilateur

Le compilateur suit une architecture modulaire classique, structurée autour d'un pipeline séquentiel :

1. **Lexer (Analyseur Lexical)** : Transforme le code source brut en une séquence de tokens (mots-clés, identifiants, valeurs).
2. **Parser (Analyseur Syntaxique)** : Vérifie l'ordre des tokens selon une grammaire `LL(1)` et génère un Arbre Syntaxique Abstrait (AST).
3. **Analyseur Sémantique** : Parcourt l'AST à travers quatre passes distinctes pour valider la logique du jeu.
4. **Optimiseur** : Simplifie l'AST (ex: Constant Folding) pour optimiser les performances futures.
5. **Générateur de Code** : Transforme l'AST validé en une représentation JSON lisible par les moteurs de jeux (IR).

---

## 3. Analyse Sémantique (Les 4 Passes)

La force de QuestLang réside dans sa validation statique approfondie. Le module sémantique (`src/semantic.py`) effectue 4 passes indépendantes :

### Passe 1 : Analyse des Symboles
Cette passe s'assure que chaque entité est déclarée correctement et uniquement.
- **Vérifications :** Détection de doublons (deux quêtes portant le même nom) et vérification que chaque référence pointant vers une entité (ex: `unlocks: quete_inconnue;`) pointe bien vers une entité déclarée.

### Passe 2 : Analyse d'Accessibilité (Graphes)
Utilise un algorithme de Parcours en Profondeur (DFS - *Depth-First Search*) de complexité `O(V + E)`.
- **Vérifications :** Assure qu'à partir de la quête de départ, toutes les autres quêtes sont atteignables. Détecte également si la condition de victoire (`win_condition`) peut réellement être accomplie.

### Passe 3 : Analyse Économique (Flux de Ressources)
Vérifie la gestion des objets et de l'or.
- **Vérifications :** Détecte l'inflation excessive (trop d'or distribué sans coût), le déficit structurel (les coûts des quêtes dépassent les récompenses distribuées), et les objets créés mais jamais consommés.

### Passe 4 : Analyse des Cycles et Interblocages (Deadlocks)
Utilise l'algorithme de **Tarjan** pour trouver les composantes fortement connexes (SCC) de complexité `O(V + E)`.
- **Vérifications :** Détecte les boucles infinies de prérequis (Quête A dépend de B, qui dépend de A), rendant le monde irrésoluble.

---

## 4. Gestion Robuste des Erreurs

Une architecture d'exceptions propre a été conçue (`src/errors.py`) pour stopper proprement la compilation à l'étape défectueuse :
- `LexicalError` : Caractère invalide (ex: `@`).
- `SyntaxError` : Mauvaise formation grammaticale (ex: `title "Le titre"` sans deux-points `:`).
- `SemanticError` : Incohérence logique (ex: quête inaccessible).
- `GenerationError` : Échec lors de la transformation JSON/Graphe.

Lorsqu'une de ces erreurs survient, l'interface Web (API Flask) retourne un statut HTTP 200 accompagné du message précis (ligne et colonne de l'erreur) pour afficher le diagnostic à l'utilisateur, évitant ainsi le crash du serveur (Erreur HTTP 500).

---

## 5. Optimisations et Débogages Récents

Lors du développement, plusieurs défis techniques critiques ont été relevés :

1. **Boucle infinie dans l'Optimiseur (`RecursionError`) :**
   L'optimiseur implémentait un visiteur (`_generic_visit`) qui traversait récursivement les attributs internes Python des `Enum` au lieu de se limiter strictement aux nœuds `ASTNode`. Une refactorisation stricte du filtrage des objets a supprimé ces blocages inattendus (qui causaient un "Timeout" dans le navigateur).
2. **Propagations des erreurs dans l'API Flask :**
   Les erreurs de compilation métier étaient interceptées mais masquées par le serveur web (qui retournait un code `500 Internal Server Error`). Le backend a été corrigé pour renvoyer des rapports de diagnostic propres sous format JSON, ce qui permet à l'interface d'indiquer exactement quelle étape (Lexique, Syntaxe, etc.) a échoué.

---

## 6. Interface Utilisateur (QuestLang Forge)

Une interface web a été développée en **JavaScript Vanilla, HTML et CSS** et reliée via un backend **Flask (Python)**.
Elle permet :
- L'édition de code source en temps réel.
- L'affichage immédiat des diagnostics dans une console intégrée.
- La visualisation dynamique du graphe du monde sous forme de réseau (bibliothèque `vis.js`).
- L'affichage de l'état du pipeline pour comprendre à quelle étape de la compilation le code a échoué.

*(Note : Afin de focaliser l'interface sur son rôle principal d'outil de conception et de validation de langages, le module de Simulation a été volontairement retiré du périmètre.)*

---

## 7. Conclusion

Le compilateur QuestLang démontre avec succès la création d'un langage dédié, intégrant des concepts fondamentaux de la théorie de la compilation (Lexing, Parsing `LL(1)`, Visiteurs AST) couplés à des algorithmes de théorie des graphes (DFS, Algorithme de Tarjan) pour prouver des propriétés logiques complexes. L'outil est à la fois robuste, fonctionnel et pédagogique.