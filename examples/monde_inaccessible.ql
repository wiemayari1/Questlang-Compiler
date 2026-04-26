world inaccessible_test {
    start: q1;
    start_gold: 50;
    win_condition: q2;
}

quest q1 {
    title: "Accessible";
    desc: "Celle-ci est OK.";
    unlocks: q2;
    rewards: xp 100, gold 25;
}

quest q2 {
    title: "Victoire";
    desc: "Condition de victoire.";
    requires: q1;
    rewards: xp 500;
}

quest q3 {
    title: "Oubliee";
    desc: "Personne ne debloque cette quete.";
    rewards: xp 1000, gold 999;
}