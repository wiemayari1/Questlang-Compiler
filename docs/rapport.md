# Rapport Technique - QuestLang Compiler 

**Projet**: Techniques de Compilation - Mini-Projet  
**Auteur**: Ayari Wiem / Sakroufi Aya / Ourari Ranim / Ayadi Soumaya
**Date**: 2025-2026 


---

## Table des matieres

1. [Introduction](#1-introduction)
2. [Choix technologiques](#2-choix-technologiques)
3. [Grammaire formelle](#3-grammaire-formelle)
4. [Architecture du compilateur](#4-architecture-du-compilateur)
5. [Analyse lexicale](#5-analyse-lexicale)
6. [Analyse syntaxique](#6-analyse-syntaxique)
7. [AST](#7-ast)
8. [Analyse semantique](#8-analyse-semantique)
9. [Generation de code](#9-generation-de-code)
10. [Tests et validation](#10-tests-et-validation)
11. [Defis rencontres et solutions](#11-defis-rencontres-et-solutions)
12. [Conclusion](#12-conclusion)

---

## 1. Introduction

QuestLang est un DSL (Domain-Specific Language) concu pour decrire des mondes de jeu RPG. L'objectif est de permettre aux concepteurs de jeux de definir des quetes, des items, des personnages non-joueurs (PNJ) et des scripts de gameplay de maniere declarative, tout en verifiant statiquement la coherence du monde avant toute execution.

Le compilateur QuestLang implemente un pipeline complet de compilation comprenant une analyse lexicale, une analyse syntaxique, la construction d'un AST, quatre passes d'analyse semantique, et la generation d'une representation intermediaire JSON accompagnee d'un rapport HTML.

### Objectifs du projet

- Concevoir un langage de programmation personnalise adapte a la description de mondes RPG
- Implementer un compilateur complet avec gestion des erreurs a chaque etape
- Verifier statiquement la jouabilite du monde (accessibilite, economie, cycles)
- Produire une documentation claire et des exemples illustratifs

---

## 2. Choix technologiques

### Langage d'implementation: Python 3.10+

**Justification**:
- Rapidite de developpement et lisibilite du code
- Support natif des types (type hints) pour la documentation
- Bibliotheque standard riche (json, re, collections)
- Pas de dependances externes requises

### Outils d'analyse

| Composant | Approche | Complexite |
|-----------|----------|------------|
| Lexer | Automate a etats avec regex | O(n) |
| Parser | Recursif descendant LL(1) | O(n) |
| Passe 2 (Accessibilite) | DFS iteratif | O(V + E) |
| Passe 4 (Cycles) | Tarjan SCC | O(V + E) |

### Format de sortie

- **IR JSON**: Representation intermediaire machine-readable pour integration avec d'autres outils
- **HTML**: Rapport visuel avec graphe de dependances, statistiques et diagnostics

---

## 3. Grammaire formelle

### Grammaire BNF complete

```bnf
program         ::= declaration* EOF

declaration     ::= worldDecl | questDecl | itemDecl | npcDecl | funcDecl | varDecl

worldDecl       ::= "world" IDENTIFIER "{" worldStmt* "}"
worldStmt       ::= ("start" | "start_gold" | "win_condition") ":" expression ";"
                | varDecl

questDecl       ::= "quest" IDENTIFIER "{" questStmt* "}"
questStmt       ::= ("title" | "desc" | "requires" | "unlocks" 
                | "rewards" | "costs" | "condition") ":" value ";"
                | "script" "{" stmtList "}"

itemDecl        ::= "item" IDENTIFIER "{" itemStmt* "}"
itemStmt        ::= ("title" | "value" | "stackable" | "type") ":" value ";"

npcDecl         ::= "npc" IDENTIFIER "{" npcStmt* "}"
npcStmt         ::= ("title" | "location" | "gives_quest") ":" value ";"

funcDecl        ::= "func" IDENTIFIER "(" paramList ")" "{" stmtList "}"
paramList       ::= IDENTIFIER ("," IDENTIFIER)* | epsilon

varDecl         ::= "var" IDENTIFIER "=" expression ";"

stmtList        ::= statement*
statement       ::= varDecl | assignStmt | ifStmt | whileStmt | forStmt
                | returnStmt | giveStmt | takeStmt | callStmt | exprStmt

assignStmt      ::= target ("=" | "+=" | "-=") expression ";"
target          ::= IDENTIFIER | IDENTIFIER "[" expression "]"

ifStmt          ::= "if" "(" expression ")" "{" stmtList "}" [ "else" "{" stmtList "}" ]
whileStmt       ::= "while" "(" expression ")" "{" stmtList "}"
forStmt         ::= "for" IDENTIFIER "in" expression "{" stmtList "}"
returnStmt      ::= "return" expression ";"
giveStmt        ::= "give" rewardList ";"
takeStmt        ::= "take" rewardList ";"
callStmt        ::= "call" IDENTIFIER "(" argList ")" ";"
exprStmt        ::= expression ";"

expression      ::= orExpr
orExpr          ::= andExpr ("or" andExpr)*
andExpr         ::= eqExpr ("and" eqExpr)*
eqExpr          ::= compExpr (("==" | "!=") compExpr)*
compExpr        ::= addExpr (("<" | ">" | "<=" | ">=") addExpr)*
addExpr         ::= mulExpr (("+" | "-") mulExpr)*
mulExpr         ::= powExpr (("*" | "/" | "%") powExpr)*
powExpr         ::= unaryExpr ("^" unaryExpr)*
unaryExpr       ::= ("-" | "not") unaryExpr | primary

primary         ::= NUMBER | STRING | "true" | "false"
                | IDENTIFIER | IDENTIFIER "(" argList ")"
                | IDENTIFIER "[" expression "]"
                | IDENTIFIER "." IDENTIFIER
                | "[" elementList "]"
                | "(" expression ")"

argList         ::= expression ("," expression)* | epsilon
elementList     ::= expression ("," expression)* | epsilon

rewardList      ::= reward ("," reward)*
reward          ::= "xp" expression | "gold" expression | expression IDENTIFIER

idList          ::= IDENTIFIER ("," IDENTIFIER)*

value           ::= expression | idList | rewardList
```

---

## 4. Architecture du compilateur

```
+------------------+     +------------------+     +------------------+
|   Fichier .ql    | --> |     Lexer        | --> |     Tokens       |
+------------------+     |  (O(n), regex)   |     +------------------+
                         +------------------+              |
                                                            v
+------------------+     +------------------+     +------------------+
|   Rapport HTML   | <-- |   CodeGenerator  | <-- |      AST         |
|   + IR JSON      |     |  (JSON + HTML)   |     |  (arborescence)  |
+------------------+     +------------------+     +------------------+
                              ^                          |
                              |                          v
                         +------------------+     +------------------+
                         |  Diagnostics     | <-- |  SemanticAnalyzer|
                         |  (erreurs/warn)  |     |  (4 passes)      |
                         +------------------+     +------------------+
```

### Modules

| Module | Role | Fichier |
|--------|------|---------|
| errors.py | Hierarchie d'exceptions et reporting | src/errors.py |
| lexer.py | Tokenisation du source | src/lexer.py |
| parser.py | Construction de l'AST | src/parser.py |
| ast_nodes.py | Definitions des noeuds AST | src/ast_nodes.py |
| semantic.py | 4 passes d'analyse semantique | src/semantic.py |
| codegen.py | Generation IR JSON + HTML | src/codegen.py |
| questlang.py | CLI principal | questlang.py |

---

## 5. Analyse lexicale

### Approche

Le lexer utilise un automate a etats fini implemente avec des expressions regulieres. Il parcourt le source caractere par caractere en une seule passe O(n).

### Tokens supportes

- **Mots-cles**: world, quest, item, npc, func, var, if, else, while, for, in, return, give, take, call, and, or, not, true, false
- **Types d'items**: weapon, armor, key, reagent, consumable, misc
- **Litteraux**: entiers, flottants, chaines avec echappement
- **Operateurs**: +, -, *, /, %, ^, ==, !=, <, >, <=, >=, =, +=, -=
- **Delimiteurs**: {}, (), [], :, ;, ,, ., ->
- **Commentaires**: // ligne et /* bloc */

### Gestion des erreurs lexicales

Les caracteres inattendus generent une `LexicalError` avec ligne et colonne precise.

---

## 6. Analyse syntaxique

### Approche

Parser recursif descendant LL(1) avec recuperation d'erreurs par synchronisation. Chaque non-terminal de la grammaire correspond a une methode du parser.

### Recuperation d'erreurs

En cas d'erreur, le parser affiche le diagnostic et avance jusqu'au prochain point de synchronisation (debut de declaration: world, quest, item, npc, func, var).

### Exemple de parsing

Pour l'expression `a + b * c`:
```
BinaryOp('+')
  +-- Identifier('a')
  +-- BinaryOp('*')
        +-- Identifier('b')
        +-- Identifier('c')
```

---

## 7. AST

### Structure

L'AST est implemente avec le pattern Visitor. Chaque noeud herite de `ASTNode` et implemente `accept(visitor)`.

### Types de noeuds

- **Declarations**: ProgramNode, WorldNode, QuestNode, ItemNode, NPCNode, FunctionNode
- **Instructions**: VarDeclNode, AssignNode, IfNode, WhileNode, ForNode, ReturnNode, BlockNode
- **Expressions**: BinaryOpNode, UnaryOpNode, LiteralNode, IdentifierNode, CallExprNode, ListLiteralNode, IndexNode, PropertyAccessNode
- **Ressources**: ResourceNode, RewardListNode, IdListNode

---

## 8. Analyse semantique

### Passe 1: Table des symboles

**Objectif**: Construire la table des symboles et detecter les doublons.

**Algorithme**:
1. Parcourir toutes les declarations
2. Enregistrer chaque entite (quete, item, PNJ, fonction)
3. Verifier l'unicite des noms
4. Verifier les references (requires, unlocks, gives_quest, items dans rewards/costs)

**Complexite**: O(n) ou n est le nombre de declarations.

### Passe 2: Accessibilite (DFS)

**Objectif**: Verifier que toutes les quetes sont accessibles depuis la quete de depart.

**Algorithme**:
1. Identifier la quete de depart (propriete `start` du world)
2. DFS iteratif depuis cette quete en suivant les liens `unlocks`
3. Marquer les quetes visitees
4. Signaler les quetes non visitees comme inaccessibles
5. Verifier que `win_condition` est accessible

**Complexite**: O(V + E) ou V = nombre de quetes, E = nombre de liens unlocks.

### Passe 3: Economie (Analyse de flux)

**Objectif**: Detecter les desequilibres economiques (inflation/deflation).

**Algorithme**:
1. Pour chaque quete, accumuler les recompenses (production) et couts (consommation)
2. Calculer les totaux par item et pour l'or
3. Detecter les deficits (consommation > production)
4. Detecter les surplus (production sans consommation)
5. Calculer le ratio or injecte / or consomme

**Complexite**: O(n) ou n est le nombre de ressources.

### Passe 4: Cycles (Tarjan SCC)

**Objectif**: Detecter les deadlocks narratifs et les elements inutilises.

**Algorithme de Tarjan**:
1. Construire le graphe de dependances (requires + unlocks)
2. Appliquer l'algorithme de Tarjan pour trouver les CFC
3. Une CFC de taille > 1 indique un cycle
4. Distinguer les deadlocks (cycle de requires mutuels) des unlock loops

**Complexite**: O(V + E).

---

## 9. Generation de code

### IR JSON

Structure hierarchique contenant:
- Metadonnees (version, statut)
- World (nom, proprietes, variables)
- Quetes (liste avec proprietes)
- Items (liste avec proprietes)
- PNJ (liste avec proprietes)
- Fonctions (liste avec parametres)
- Diagnostics (erreurs, avertissements, infos)

### Rapport HTML

Interface visuelle comprenant:
- En-tete avec statut de compilation
- Cartes de statistiques (nombre de quetes, items, PNJ, erreurs)
- Section diagnostics coloree
- Graphe de dependances SVG (quetes en cercle, fleches unlocks)
- Details des quetes, items et PNJ
- IR JSON formate

---

## 10. Tests et validation

### Suite de tests

27 tests repartis en 7 classes:

| Classe | Tests | Description |
|--------|-------|-------------|
| TestLexer | 6 | Tokens, nombres, operateurs, commentaires, chaines, localisation |
| TestParser | 7 | Quetes, world, items, PNJ, recompenses, scripts, fonctions |
| TestSemanticPass1 | 3 | Doublons, references indefinies |
| TestSemanticPass2 | 3 | Accessibilite, victoire inaccessible, sans recompense |
| TestSemanticPass3 | 2 | Deficit d'items, inflation d'or |
| TestSemanticPass4 | 2 | Deadlock, items morts |
| TestIntegration | 4 | Pipeline complet, HTML, JSON, monde brise |

### Execution

```bash
python tests/test_compiler.py
```

### Couverture

Les tests couvrent:
- Tous les tokens du lexer
- Toutes les constructions syntaxiques
- Tous les codes d'erreur des 4 passes
- Les cas limites (monde vide, references circulaires, inflation extreme)

---

## 11. Defis rencontres et solutions

### Defi 1: Recuperation d'erreurs du parser

**Probleme**: Le parser s'arretait a la premiere erreur.  
**Solution**: Implementation d'un mecanisme de synchronisation qui avance jusqu'au prochain token de declaration (world, quest, item, npc, func, var).

### Defi 2: Grammaire des recompenses ambigue

**Probleme**: `rewards: xp 100, gold 50, 3 potion` necessite de distinguer les mots-cles `xp`/`gold` des identifiants d'items.  
**Solution**: Le lexer traite `xp` et `gold` comme des IDENTIFIER, et le parser les reconnait par valeur dans le contexte des recompenses.

### Defi 3: Graphe SVG de dependances

**Probleme**: Generer un graphe visuel sans dependances externes.  
**Solution**: Generation directe de SVG avec positionnement circulaire des noeuds et fleches SVG.

### Defi 4: Evaluation des expressions constantes

**Probleme**: La passe 3 doit evaluer des expressions comme `gold 10 * 2` pour l'analyse economique.  
**Solution**: Methode `_eval_expr` recursive qui evalue les expressions constantes a la compilation.

---

## 12. Conclusion

QuestLang demontre l'application des concepts fondamentaux de la compilation (analyse lexicale, syntaxique, semantique, generation de code) a un domaine concret: la verification de la jouabilite des mondes RPG.

Les 4 passes semantiques permettent de detecter des problemes critiques avant l'execution:
- Des quetes inaccessibles qui bloqueraient le joueur
- Des deadlocks narratifs qui rendraient le jeu impossible a terminer
- Des desequilibres economiques qui casseraient l'experience
- Des elements inutilises qui gaspilleraient les ressources de developpement

### Ameliorations futures possibles

- Machine virtuelle pour executer les scripts QuestLang
- Optimisations: elimination de code mort, constant folding
- Interface graphique (GUI) pour editer les mondes visuellement
- Export vers des moteurs de jeu (Unity, Godot)

---

**Annexes**

- Annexe A: Diagramme de classes AST
- Annexe B: Table des symboles complete
- Annexe C: Exemples de sorties HTML
