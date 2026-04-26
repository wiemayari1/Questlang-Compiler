world monde_casse {
    start: quete_inexistante;
    start_gold: 50;
    win_condition: quete_finale;
}

quest quete_depart {
    title: "Depart";
    desc: "Quete de depart.";
    unlocks: quete_milieu;
    rewards: xp 100, gold 25;
}

quest quete_milieu {
    title: "Milieu";
    desc: "Quete du milieu.";
    requires: quete_inexistante;
    unlocks: quete_finale;
    rewards: xp 200, gold 50, 1 epee;
    costs: 5 potion;
}

quest quete_finale {
    title: "Fin";
    desc: "Quete finale.";
    requires: quete_milieu;
    rewards: xp 500;
}

quest quete_orpheline {
    title: "Orpheline";
    desc: "Jamais debloquee.";
    rewards: xp 999;
}

item epee { title: "Epee"; value: 50; stackable: false; type: weapon; }