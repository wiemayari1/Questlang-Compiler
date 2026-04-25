// ============================================================
// Monde Brise - Exemple avec erreurs intentionnelles
// QuestLang v2.0
// ============================================================
// Ce fichier contient des erreurs pour tester les 4 passes
// semantiques du compilateur.
// ============================================================

world monde_brise {
    start: quete_depart;
    start_gold: 100;
    win_condition: quete_finale_inexistante;  // ERREUR: quete inexistante
}

// ============================================================
// Quetes avec erreurs
// ============================================================

quest quete_depart {
    title: "Le debut";
    desc: "C'est ici que tout commence.";
    rewards: xp 50, gold 10;
    unlocks: quete_milieu, quete_inaccessible;
}

quest quete_milieu {
    title: "Le milieu";
    desc: "La quete du milieu.";
    requires: quete_depart;
    costs: 5 potion_inexistante;  // ERREUR: item inexistant
    rewards: xp 100, gold 20;
    unlocks: quete_boucle;
}

// Quete dupliquee (deuxieme definition)
quest quete_depart {  // ERREUR: quete dupliquee
    title: "Le debut (bis)";
}

// Quete inaccessible (pas de chemin depuis start)
quest quete_inaccessible {
    title: "Inaccessible";
    desc: "Personne ne peut arriver ici.";
    rewards: xp 999;
}

// Boucle de deadlock narratif
quest quete_boucle {
    title: "La boucle";
    desc: "Cette quete cree un deadlock.";
    requires: quete_deadlock;
    unlocks: quete_deadlock;
    rewards: xp 10;
}

quest quete_deadlock {
    title: "Le deadlock";
    desc: "Impossible de completer.";
    requires: quete_boucle;
    unlocks: quete_boucle;
    rewards: xp 10;
}

// Quete sans recompense (avertissement)
quest quete_sans_recompense {
    title: "Sans recompense";
    desc: "Cette quete n'offre rien.";
    requires: quete_depart;
}

// Quete avec inflation d'or extreme
quest quete_inflation {
    title: "L'inflation";
    desc: "Trop d'or injecte.";
    rewards: gold 10000;
    costs: gold 10;
}

// ============================================================
// Items
// ============================================================

item epee_rouillee {
    title: "Epee Rouillee";
    value: 10;
    type: weapon;
    stackable: false;
}

// Item jamais utilise (avertissement)
item bouclier_oublie {
    title: "Bouclier Oublie";
    value: 50;
    type: armor;
    stackable: false;
}

// ============================================================
// PNJ
// ============================================================

npc guide {
    title: "Le Guide";
    location: place_centrale;
    gives_quest: quete_depart;
}

// PNJ inutile (ne donne aucune quete)
npc villageois_inutile {
    title: "Villageois";
    location: village;
}
