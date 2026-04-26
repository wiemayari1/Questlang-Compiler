world valdris {
    start: quete_depart;
    start_gold: 50;
    win_condition: quete_finale;
}

quest quete_depart {
    title: "Le Reveil";
    desc: "Vous vous reveillez dans un village detruit.";
    unlocks: quete_forgeron;
    rewards: xp 100, gold 25;

    script {
        var bonus = 10;
        if (bonus > 5) {
            give xp bonus;
        }
    }
}

quest quete_forgeron {
    title: "L'Appel du Fer";
    desc: "Le forgeron a besoin de minerai.";
    requires: quete_depart;
    unlocks: quete_finale;
    rewards: xp 200, gold 50, 1 epee_rouillee;
    costs: 2 minerai;
}

quest quete_finale {
    title: "Le Dernier Combat";
    desc: "Affrontez le dragon.";
    requires: quete_forgeron;
    rewards: xp 500, gold 100, 1 ame_dragon;
}

item epee_rouillee {
    title: "Epee Rouillee";
    value: 25;
    stackable: false;
    type: weapon;
}

item minerai {
    title: "Minerai de Fer";
    value: 5;
    stackable: true;
    type: material;
}

item ame_dragon {
    title: "Ame du Dragon";
    value: 1000;
    stackable: false;
    type: artifact;
}

npc forgeron_gorak {
    title: "Gorak le Forgeron";
    location: forge_centrale;
    gives_quest: quete_forgeron;
}