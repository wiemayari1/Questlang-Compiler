world inflation_test {
    start: q1;
    start_gold: 10;
    win_condition: q3;
}

quest q1 {
    title: "Quete d'Or";
    desc: "Trop d'or injecte.";
    unlocks: q2;
    rewards: gold 10000, xp 50;
}

quest q2 {
    title: "Milieu";
    desc: "Transition.";
    requires: q1;
    unlocks: q3;
    rewards: gold 5000, xp 50;
}

quest q3 {
    title: "Fin";
    desc: "Victoire.";
    requires: q2;
    rewards: xp 100;
}