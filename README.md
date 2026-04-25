# QuestLang - Compilateur pour Mondes RPG

**Version 2.0** | Projet de Techniques de Compilation | 2024-2025

QuestLang est un DSL (Domain-Specific Language) permettant de decrire des mondes de jeu RPG (quetes, items, PNJ) et de verifier statiquement leur coherence a la compilation grace a 4 passes d'analyse semantique.

## Table des matieres

- [Fonctionnalites](#fonctionnalites)
- [Syntaxe du langage](#syntaxe-du-langage)
- [Installation](#installation)
- [Utilisation](#utilisation)
- [Structure du projet](#structure-du-projet)
- [Tests](#tests)
- [Choix techniques](#choix-techniques)
- [Auteur](#auteur)

## Fonctionnalites

### Pipeline de compilation

```
Source .ql -> Lexer -> Parser -> AST -> 4 Passes Semantiques -> IR JSON + Rapport HTML
```

### 4 passes semantiques

| Passe | Algorithme | Ce qu'elle detecte |
|-------|-----------|-------------------|
| Passe 1 - Symboles | Table des symboles | Doublons, references indefinies |
| Passe 2 - Accessibilite | DFS iteratif O(V+E) | Quetes inaccessibles, fin inaccessible |
| Passe 3 - Economie | Analyse de flux | Inflation/deflation d'or, deficit/surplus d'items |
| Passe 4 - Cycles | Tarjan SCC O(V+E) | Deadlocks narratifs, items morts, PNJ inutiles |

### Fonctionnalites du langage

- **Blocs de declaration**: `world`, `quest`, `item`, `npc`
- **Variables et types**: `var`, `int`, `float`, `bool`, `string`, `list`
- **Expressions**: arithmetiques (+, -, *, /, %, ^), logiques (`and`, `or`, `not`), comparaisons (==, !=, <, >, <=, >=)
- **Structures de controle**: `if`/`else`, `while`, `for`/`in`
- **Fonctions utilisateur**: `func` avec parametres et `return`
- **Instructions speciales**: `give`, `take`, `call`
- **Gestion des erreurs**: lexicales, syntaxiques, semantiques avec localisation precise

## Syntaxe du langage

### Bloc world

```ql
world mon_monde {
    start: premiere_quete;
    start_gold: 50;
    win_condition: quete_finale;
}
```

### Bloc quest

```ql
quest identifiant_quete {
    title:     "Titre affiche";
    desc:      "Description longue";
    requires:  quete_prerequis_1, quete_prerequis_2;
    unlocks:   quete_suivante;
    rewards:   xp 200, gold 50, 1 epee_magique;
    costs:     2 cristaux;
    condition: "Condition narrative";

    script {
        var bonus = 10;
        if (bonus > 5) {
            give xp bonus;
        }
    }
}
```

### Bloc item

```ql
item identifiant_item {
    title:     "Nom affiche";
    value:     50;
    stackable: true;
    type:      weapon;
}
```

### Bloc npc

```ql
npc identifiant_npc {
    title:       "Nom du PNJ";
    location:    village_entree;
    gives_quest: quete1, quete2;
}
```

### Fonctions

```ql
func calcul_bonus(base, multiplicateur) {
    var resultat = base * multiplicateur;
    if (resultat > 100) {
        resultat = 100;
    }
    return resultat;
}
```

### Recompenses

```ql
rewards: xp 500, gold 100, 3 cristal_ombre;
```

### Commentaires

```ql
// Commentaire sur une ligne
/* Commentaire
   multi-ligne */
```

## Installation

```bash
# Cloner le depot
git clone https://github.com/wiemayari1/Questlang-Compiler.git
cd Questlang-Compiler

# Aucune dependance externe requise (Python 3.10+)
python --version  # >= 3.10
```

## Utilisation

### Compiler un fichier

```bash
python questlang.py mon_monde.ql
```

### Options

```bash
--html          Generer un rapport HTML avec graphe de dependances
--ir            Afficher l'IR JSON genere
--tokens        Afficher les tokens lexicaux
--ast           Afficher l'AST simplifie
--out DIR       Repertoire de sortie (defaut: .)
-v, --verbose   Mode verbeux
--no-banner     Desactiver la banniere
```

### Exemples

```bash
# Compilation simple
python questlang.py examples/valid_world.ql

# Compilation avec rapport HTML
python questlang.py examples/valid_world.ql --html --out rapports/

# Voir l'IR JSON
python questlang.py examples/valid_world.ql --ir

# Tester sur le monde brise (avec erreurs intentionnelles)
python questlang.py examples/broken_world.ql
```

## Codes d'erreur

### Passe 1 - Symboles

| Code | Severite | Description |
|------|----------|-------------|
| DUPLICATE_QUEST | ERREUR | Quete definie plusieurs fois |
| DUPLICATE_ITEM | ERREUR | Item defini plusieurs fois |
| DUPLICATE_NPC | ERREUR | PNJ defini plusieurs fois |
| DUPLICATE_FUNC | ERREUR | Fonction definie plusieurs fois |
| UNDEF_QUEST_REF | ERREUR | Reference a une quete inexistante |
| UNDEF_UNLOCK_REF | ERREUR | Reference a une quete inexistante dans unlocks |
| UNDEF_ITEM_REF | ERREUR | Item inexistant dans rewards/costs |
| UNDEF_FUNC_REF | ERREUR | Appel a une fonction inexistante |
| UNDEF_START_QUEST | ERREUR | start pointe vers une quete inexistante |
| UNDEF_WIN_COND | ERREUR | win_condition pointe vers une quete inexistante |

### Passe 2 - Accessibilite

| Code | Severite | Description |
|------|----------|-------------|
| UNREACHABLE_QUEST | ERREUR | Quete inaccessible depuis start_quest |
| WIN_UNREACHABLE | ERREUR | La condition de victoire n'est jamais atteignable |
| WIN_REACHABLE | INFO | Confirmation que la fin est atteignable |
| NO_REWARD | AVERTISSEMENT | Quete accessible sans recompense |
| NO_WORLD | AVERTISSEMENT | Pas de bloc world |

### Passe 3 - Economie

| Code | Severite | Description |
|------|----------|-------------|
| ITEM_DEFICIT | ERREUR | Item consomme plus souvent qu'il n'est produit |
| ITEM_SURPLUS | AVERTISSEMENT | Item produit sans jamais etre consomme |
| GOLD_INFLATION | AVERTISSEMENT | Ratio injecte/consomme > 10x |
| GOLD_DEFLATION | AVERTISSEMENT | Ratio < 0.5x |

### Passe 4 - Cycles

| Code | Severite | Description |
|------|----------|-------------|
| DEADLOCK_CYCLE | ERREUR | Cycle de dependances mutuelles |
| UNLOCK_LOOP | AVERTISSEMENT | Boucle d'unlock |
| DEAD_ITEM | AVERTISSEMENT | Item declare mais jamais utilise |
| IDLE_NPC | AVERTISSEMENT | PNJ qui ne donne aucune quete |

## Structure du projet

```
questlang/
|-- questlang.py              # CLI principal et orchestrateur
|-- src/
|   |-- errors.py             # Gestion centralisee des erreurs
|   |-- lexer.py              # Analyse lexicale (automate a etats)
|   |-- parser.py             # Parser recursif descendant LL(1)
|   |-- ast_nodes.py          # Noeuds de l'AST
|   |-- semantic.py           # 4 passes semantiques
|   |-- codegen.py            # Generation IR JSON + HTML
|-- tests/
|   |-- test_compiler.py      # 27 tests unitaires et d'integration
|-- examples/
|   |-- valid_world.ql        # Monde valide (Le Monde de Valdris)
|   |-- broken_world.ql       # Monde avec erreurs intentionnelles
|-- docs/
|   |-- rapport.md            # Rapport technique detaille
|-- README.md
```

## Tests

```bash
python tests/test_compiler.py
```

La suite couvre:

- **6 tests lexer**: tokens, mots-cles, commentaires, nombres, chaines, localisation
- **7 tests parser**: quetes, world, items, PNJ, recompenses, scripts, fonctions
- **3 tests semantiques Passe 1**: doublons, references indefinies
- **3 tests semantiques Passe 2**: accessibilite, victoire inaccessible, sans recompense
- **2 tests semantiques Passe 3**: deficit d'items, inflation d'or
- **2 tests semantiques Passe 4**: deadlock, items morts
- **4 tests d'integration**: pipeline complet, HTML, JSON, monde brise

## Choix techniques

- **Langage**: Python 3.10+ (lisibilite, rapidite de developpement)
- **Lexer**: Automate a etats avec regex, une seule passe O(n)
- **Parser**: Recursif descendant LL(1) avec recuperation d'erreurs
- **AST**: Structure arborescente typee avec pattern Visitor
- **Passe 2 (Accessibilite)**: DFS iteratif - O(V + E)
- **Passe 3 (Economie)**: Analyse de flux avec accumulation
- **Passe 4 (Cycles)**: Algorithme de Tarjan SCC - O(V + E)
- **Sortie**: IR JSON (machine-readable) + rapport HTML (human-readable)

## Auteur

Projet realise dans le cadre du mini-projet de Techniques de Compilation (Conception et realisation d'un compilateur pour un langage personnalise).

Departement GLSI-ISI, 1ere Ingenieur, 2024-2025.
