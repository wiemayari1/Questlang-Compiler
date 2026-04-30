# Argumentaire de Soutenance - QuestLang Compiler

Ce document fournit les arguments clés pour défendre le projet QuestLang face au jury, en se basant sur les 4 critères d'évaluation demandés.

---

## 1. Créativité (Originalité du langage et de ses fonctionnalités)

**Argumentaire :**
- **Un langage ciblé (DSL) :** Contrairement à un énième langage généraliste (comme un mini-C ou mini-Python), QuestLang résout un problème concret de l'industrie du jeu vidéo (le Game Design). Il permet de vérifier qu'un jeu de rôle n'est pas "cassé" avant même d'écrire une ligne de code du jeu réel.
- **Mots-clés natifs au métier :** Le langage intègre nativement des concepts de RPG (`quest`, `item`, `npc`, `requires`, `unlocks`, `gives_quest`, `rewards`, `costs`).
- **Gestion des ressources intégrée :** Le compilateur comprend la différence entre de la monnaie (`gold`), de l'expérience (`xp`) et des objets empilables (`potion`). Les instructions `give` et `take` gèrent ces économies de façon native.
- **L'Interface Web (QuestLang Forge) :** Plutôt que de se limiter à un compilateur console triste, le projet propose un véritable petit IDE dans le navigateur, avec coloration syntaxique, génération de graphes de quêtes interactifs en temps réel (via `vis.js`) et visualisation "pas-à-pas" du pipeline.

## 2. Robustesse (Qualité de la gestion des erreurs et des tests)

**Argumentaire :**
- **Précision chirurgicale des erreurs :** Lorsqu'une erreur survient, le compilateur ne "crashe" pas bêtement. L'analyseur (Lexer/Parser) sauvegarde l'état, et génère des erreurs typées (`LexicalError`, `SyntaxError`, `SemanticError`) qui incluent **la ligne et la colonne exactes**.
- **Remontée visuelle (UI) :** Ces coordonnées sont envoyées au backend Flask, ce qui permet à l'interface web de souligner en rouge l'endroit exact de l'erreur dans l'éditeur de texte.
- **Un monde garanti sans bugs :** La robustesse de QuestLang réside dans sa promesse : si le code compile, le jeu est finissable à 100%. Il n'y aura aucun "objet introuvable" ou "quête fantôme". L'architecture refuse de générer l'IR (Intermediate Representation) si la moindre faille logique est détectée.
- **Sécurité du serveur :** La compilation via l'interface web est exécutée dans un thread séparé avec un **Timeout (délai d'attente maximum de 8 secondes)** pour éviter qu'une boucle infinie ou un graphe trop lourd ne fasse planter le serveur Flask.

## 3. Complexité (Niveau technique des fonctionnalités implémentées)

**Argumentaire :**
- **Compilateur "From Scratch" :** Aucun outil de génération automatique de parseur (comme ANTLR, PLY, ou Yacc) n'a été utilisé. Le Lexer (expressions régulières) et le Parseur (LL(1) Descente Récursive) ont été codés entièrement à la main en Python, prouvant une maîtrise parfaite de la théorie des langages.
- **Algorithmique Avancée sur les Graphes :**
  - **DFS (Parcours en Profondeur) :** Utilisé pour la passe d'accessibilité. Le compilateur simule tous les chemins possibles depuis le nœud "start" pour s'assurer que la `win_condition` est toujours atteignable.
  - **Algorithme de Tarjan (SCC) :** Utilisé de manière très ingénieuse pour détecter les "Deadlocks" (interblocages). Si la quête A débloque la quête B, et que la quête B est requise pour la quête A, Tarjan détecte ce cycle complexe et bloque la compilation.
- **Génération d'Arbre (AST) Complexe :** L'arbre syntaxique est entièrement orienté objet, récursif, et capable de s'auto-sérialiser (`to_dict`) pour communiquer avec des APIs externes en JSON.

## 4. Documentation (Clarté et exhaustivité)

**Argumentaire :**
- **Formalisation Mathématique :** La grammaire du langage n'est pas improvisée, elle est strictement formalisée au standard EBNF (Extended Backus-Naur Form) dans le fichier `GRAMMAIRE_EBNF.md`.
- **Rapports Techniques et Architecturaux :** Le projet contient des documentations internes détaillées (`RAPPORT_TECHNIQUE.md`, `EXPLICATION_CODE.md`) qui décortiquent chaque fichier, chaque étape du pipeline de compilation et les choix d'algorithmes (pourquoi Tarjan ? Pourquoi LL(1) ?).
- **Rapport de Compilation Exportable :** Le compilateur dispose d'une fonctionnalité (`--html`) capable de générer un rapport web autonome de l'analyse sémantique, facilitant le travail asynchrone des Game Designers.
- **Facilité d'installation :** Le `README.md` principal offre des étapes claires pour déployer l'interface web ou le CLI sous Windows et Ubuntu grâce à l'utilisation d'environnements virtuels (`venv`) standards.
