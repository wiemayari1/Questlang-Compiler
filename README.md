# QuestLang Forge - Compilateur pour Mondes RPG

QuestLang est un langage dedie (DSL) pour decrire des mondes de jeu RPG. Il permet de declarer des quetes, des objets, des personnages non-joueurs et de verifier automatiquement la coherence du monde a la compilation grace a quatre passes d'analyse semantique.

---

## Apercu

QuestLang transforme un fichier texte decrivant un monde en une representation intermediaire JSON verifiee, avec detection des erreurs lexicales, syntaxiques et semantiques.

```
Source .ql -> Lexer -> Parser -> AST -> 4 Passes Semantiques -> IR JSON + Rapport
```

---

## Fonctionnalites

### Langage QuestLang

- **Declarations** : `world`, `quest`, `item`, `npc`
- **Variables et types** : `var`, `int`, `float`, `bool`, `string`, `list`
- **Expressions** : arithmetiques, logiques, comparaisons
- **Controle** : `if`/`else`, `while`, `for`/`in`
- **Fonctions** : `func` avec parametres et `return`
- **Instructions speciales** : `give`, `take`, `call`

### Pipeline semantique

| Passe | Algorithme | Detection |
|-------|------------|-----------|
| 1 - Symboles | Table des symboles | Doublons, references indefinies |
| 2 - Accessibilite | DFS iteratif O(V+E) | Quetes inaccessibles, fin inaccessible |
| 3 - Economie | Analyse de flux | Inflation, deficit, surplus |
| 4 - Cycles | Tarjan SCC O(V+E) | Deadlocks, items morts, PNJ inutiles |

### Simulation du monde

Apres compilation reussie, l'interface web permet de simuler le deroulement du monde :

- Ordre de completion des quetes (topologique)
- Evolution de l'inventaire du joueur (or, XP, items)
- Visualisation pas-a-pas ou lecture automatique
- Detection de la condition de victoire

---

## Installation rapide

### Prerequis

- Python **3.10 ou superieur**
- `pip` a jour
- Un navigateur moderne (Chrome, Firefox, Edge)

### 1. Cloner le projet

```bash
git clone https://github.com/wiemayari1/Questlang-Compiler.git
cd Questlang-Compiler
```

### 2. Lancer le compilateur en ligne de commande (CLI)

Aucune dependance externe n'est requise pour le CLI.

```bash
# Tester la compilation d'un exemple
python questlang.py examples/valid_world.ql

# Generer le rapport HTML + IR JSON
python questlang.py examples/valid_world.ql --html --ir --out ./rapports/
```

### 3. Lancer l'interface web (QuestLang Forge)

```bash
cd web

# (Recommande) Creer un environnement virtuel
python -m venv venv

# Activer l'environnement virtuel
# Sur Windows :
venv\Scripts\activate
# Sur macOS/Linux :
source venv/bin/activate

# Installer les dependances
pip install -r requirements.txt

# Demarrer le serveur Flask
python app.py
```

### 4. Ouvrir dans le navigateur

Rendez-vous sur : **http://localhost:5000**

### 5. Utiliser l'interface

1. **Charger un exemple** : selectionnez un monde dans le menu deroulant en haut.
2. **Charger votre fichier** : cliquez sur le bouton 📂 puis choisissez un fichier `.ql` depuis votre ordinateur.
3. **Compiler** : cliquez sur le bouton **Compiler** pour voir l'analyse lexicale, syntaxique, les 4 passes semantiques, le graphe du monde et la simulation.
4. **Explorer** : utilisez les onglets *Carte*, *Analyse*, *Simulation* et la console en bas.

### 6. Executer les tests

```bash
python tests/test_compiler.py
```

---

## Utilisation CLI

```bash
# Compilation simple
python questlang.py examples/valid_world.ql

# Avec rapport HTML
python questlang.py examples/valid_world.ql --html --out rapports/

# Afficher l'IR JSON
python questlang.py examples/valid_world.ql --ir

# Tester le monde avec erreurs
python questlang.py examples/broken_world.ql
```

Options disponibles :

```
--html          Generer un rapport HTML avec graphe de dependances
--ir            Afficher l'IR JSON genere
--tokens        Afficher les tokens lexicaux
--ast           Afficher l'AST simplifie
--out DIR       Repertoire de sortie (defaut: .)
-v, --verbose   Mode verbeux
--no-banner     Desactiver la banniere
```

---

## Interface Web - QuestLang Forge

Une interface graphique interactive et immersive pour editer, compiler, visualiser et simuler les mondes QuestLang dans le navigateur.

### Fonctionnalites de l'interface

**Editeur**
- Syntax highlighting QuestLang avec coloration personnalisee
- Snippets : taper `quest` + Ctrl+Space genere le squelette d'une quete
- Pliage de code pour les blocs imbriques
- Marqueurs d'erreur cliquables dans la gouttiere
- Sauvegarde auto dans le navigateur (localStorage)

**Carte du Monde**
- Graphe interactif des quetes, objets et PNJ avec vis.js
- Filtres : afficher/masquer par type (quetes, items, PNJ, recompenses)
- Layout hierarchique gauche-droite avec zoom et deplacement
- Physique activable/desactivable
- Export PNG du graphe

**Analyse Semantique**
- Dashboard des 4 passes avec statuts colores et metriques detaillees
- Mode pas-a-pas : execution sequentielle animee des passes
- Metriques : compteurs en temps reel

**Simulation**
- Inventaire du joueur : or, XP, nombre d'items
- Timeline des quetes avec etats (completee, active, future)
- Controles : precedent, suivant, lecture automatique, reinitialisation
- Barre de progression visuelle
- Details par etape : recompenses et couts appliques

**Export**
- Telechargement du fichier `.ql`
- Telechargement de l'IR JSON
- Telechargement du graphe en PNG

**Console**
- Journal de compilation avec horodatage
- Localisation precise (ligne:colonne)
- Couleurs par severite (erreur, alerte, info, succes)

---

## Structure du projet

```
questlang/
|-- questlang.py              # CLI principal
|-- src/
|   |-- errors.py             # Gestion des erreurs
|   |-- lexer.py              # Analyse lexicale
|   |-- parser.py             # Analyse syntaxique LL(1)
|   |-- ast_nodes.py          # Noeuds de l'AST
|   |-- semantic.py           # 4 passes semantiques
|   |-- codegen.py            # Generation IR JSON + HTML
|-- tests/
|   |-- test_compiler.py      # Tests unitaires et d'integration
|-- examples/
|   |-- valid_world.ql        # Monde valide (Le Monde de Valdris)
|   |-- broken_world.ql       # Monde avec erreurs intentionnelles
|-- web/
|   |-- app.py                # Serveur Flask (API REST)
|   |-- requirements.txt      # Dependances web
|   |-- templates/
|   |   |-- index.html        # Interface unique
|   |-- static/
|   |   |-- css/style.css     # Theme RPG immersif
|   |   |-- js/main.js        # Logique frontend complete
|-- docs/
|   |-- rapport.md            # Rapport technique
|-- README.md
```

---

## Tests

```bash
python tests/test_compiler.py
```

Couverture :

- 6 tests lexer (tokens, mots-cles, commentaires, nombres, chaines, localisation)
- 7 tests parser (quetes, world, items, PNJ, recompenses, scripts, fonctions)
- 3 tests semantiques Passe 1 (doublons, references indefinies)
- 3 tests semantiques Passe 2 (accessibilite, victoire inaccessible, sans recompense)
- 2 tests semantiques Passe 3 (deficit d'items, inflation d'or)
- 2 tests semantiques Passe 4 (deadlock, items morts)
- 4 tests d'integration (pipeline complet, HTML, JSON, monde brise)

---

## Choix techniques

- **Langage** : Python 3.10+ (lisibilite, rapidite de prototypage)
- **Lexer** : Automate a etats avec expressions regulieres, une passe O(n)
- **Parser** : Recursif descendant LL(1) avec recuperation d'erreurs
- **AST** : Structure arborescente typee avec pattern Visitor
- **Passe 2** : DFS iteratif - O(V + E)
- **Passe 3** : Analyse de flux avec accumulation
- **Passe 4** : Algorithme de Tarjan SCC - O(V + E)
- **Sortie** : IR JSON (machine-readable) + rapport HTML (human-readable)
- **Interface web** : Flask + vis.js, zero dependance lourde
- **Simulation** : Calcul d'ordre topologique des quetes avec evolution de l'inventaire

---

## Depannage courant

| Probleme | Solution |
|----------|----------|
| `ModuleNotFoundError: No module named 'flask'` | `cd web && pip install -r requirements.txt` |
| Le port 5000 est deja utilise | `python app.py` utilise le port 5000 par defaut. Fermez l'autre application ou modifiez `port=5000` dans `app.py`. |
| L'interface web affiche "Mode demo" | Le backend ne trouve pas les modules `src/`. Verifiez que vous lancez `app.py` depuis le dossier `web/` et que le dossier `src/` existe bien a la racine. |
| Le fichier `.ql` ne se charge pas | Verifiez que vous avez bien la derniere version de `main.js` avec le listener sur `#file-input`. |

---

## Auteur

Ayari Wiem / Ourari Ranim / Ayadi Soumaya / Sakroufi Aya
