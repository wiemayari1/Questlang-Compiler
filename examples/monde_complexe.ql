world royaume_eldoria {
    start: quete_village;
    start_gold: 100;
    win_condition: quete_royale;
}

quest quete_village {
    title: "Le Village en Detresse";
    desc: "Des gobelins attaquent le village.";
    unlocks: quete_foret, quete_mine;
    rewards: xp 50, gold 20, 3 torche;
}

quest quete_foret {
    title: "La Foret Maudite";
    desc: "Trouvez l'herbe medicinale.";
    requires: quete_village;
    unlocks: quete_chateau;
    rewards: xp 100, gold 30, 1 herbe_rare;
    costs: 1 torche;
}

quest quete_mine {
    title: "Les Profondeurs";
    desc: "Recuperez le minerai magique.";
    requires: quete_village;
    unlocks: quete_forge;
    rewards: xp 120, gold 40, 1 minerai_magique;
    costs: 2 torche;
}

quest quete_forge {
    title: "La Forge Celeste";
    desc: "Forgez l'epee legendaire.";
    requires: quete_mine;
    unlocks: quete_royale;
    rewards: xp 200, gold 50, 1 epee_legendaire;
    costs: 1 minerai_magique;
}

quest quete_chateau {
    title: "Le Chateau Oublie";
    desc: "Trouvez le parchemin ancien.";
    requires: quete_foret;
    unlocks: quete_royale;
    rewards: xp 150, gold 40, 1 parchemin_ancien;
}

quest quete_royale {
    title: "Le Couronnement";
    desc: "Devenez le roi d'Eldoria.";
    requires: quete_forge, quete_chateau;
    rewards: xp 1000, gold 500, 1 couronne_royale;
}

item herbe_rare { title: "Herbe Rare"; value: 30; stackable: true; type: material; }
item torche { title: "Torche"; value: 5; stackable: true; type: consumable; }
item minerai_magique { title: "Minerai Magique"; value: 100; stackable: false; type: material; }
item epee_legendaire { title: "Epee Legendaire"; value: 500; stackable: false; type: weapon; }
item parchemin_ancien { title: "Parchemin Ancien"; value: 200; stackable: false; type: artifact; }
item couronne_royale { title: "Couronne Royale"; value: 5000; stackable: false; type: artifact; }

npc chef_village { title: "Chef du Village"; location: village; gives_quest: quete_village; }
npc druide { title: "Le Druide"; location: foret; gives_quest: quete_foret; }
npc mineur_nain { title: "Thorin le Mineur"; location: mine; gives_quest: quete_mine; }
npc forgeron_maitre { title: "Maître Forgeron"; location: forge; gives_quest: quete_forge; }
npc roi { title: "Roi Eldor"; location: chateau; gives_quest: quete_royale; }