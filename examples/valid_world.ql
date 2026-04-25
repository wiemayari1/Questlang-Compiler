// ============================================================
// Le Monde de Valdris - Exemple de monde RPG valide
// QuestLang v2.0
// ============================================================

world valdris {
    start: prologue;
    start_gold: 50;
    win_condition: epilogue;
}

// ============================================================
// Quetes principales
// ============================================================

quest prologue {
    title: "L'appel aux armes";
    desc: "Le roi Aldric convoque tous les aventuriers pour defendre le royaume.";
    rewards: xp 100, gold 20;
    unlocks: premiere_mission, renforcement_arme;
}

quest premiere_mission {
    title: "Premiere mission";
    desc: "Partez vers la foret des ombres et eliminez les gobelins.";
    requires: prologue;
    costs: 1 potion_soin;
    rewards: xp 200, gold 50, 1 epee_magique;
    unlocks: boss_gobelin;
}

quest renforcement_arme {
    title: "Renforcement de l'arme";
    desc: "Le forgeron peut ameliorer votre equipement.";
    requires: prologue;
    costs: gold 30;
    rewards: xp 50;
    unlocks: boss_gobelin;
}

quest boss_gobelin {
    title: "Le chef des gobelins";
    desc: "Affrontez Grakthar, le chef redoute des gobelins.";
    requires: premiere_mission, renforcement_arme;
    costs: 2 potion_soin;
    rewards: xp 500, gold 150, 1 armure_fer;
    unlocks: retour_chateau;
}

quest retour_chateau {
    title: "Retour au chateau";
    desc: "Rapportez la victoire au roi Aldric.";
    requires: boss_gobelin;
    rewards: xp 100, gold 50;
    unlocks: epilogue;
}

quest epilogue {
    title: "Le royaume sauve";
    desc: "Vous etes celebre dans tout le royaume.";
    requires: retour_chateau;
    rewards: xp 1000, gold 500, 1 medaille_honneur;
}

// ============================================================
// Items
// ============================================================

item epee_magique {
    title: "Epee de Flammes";
    value: 150;
    type: weapon;
    stackable: false;
}

item armure_fer {
    title: "Armure de Fer";
    value: 200;
    type: armor;
    stackable: false;
}

item potion_soin {
    title: "Potion de Soin";
    value: 25;
    type: consumable;
    stackable: true;
}

item medaille_honneur {
    title: "Medaille d'Honneur";
    value: 1000;
    type: misc;
    stackable: false;
}

// ============================================================
// Personnages non-joueurs
// ============================================================

npc roi_aldric {
    title: "Roi Aldric";
    location: chateau;
    gives_quest: prologue, retour_chateau;
}

npc forgeron_grom {
    title: "Grom le Forgeron";
    location: forge;
    gives_quest: renforcement_arme;
}

npc capitaine_garde {
    title: "Capitaine des Gardes";
    location: caserne;
    gives_quest: premiere_mission, boss_gobelin;
}
