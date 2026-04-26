world deadlock_test {
    start: q1;
    start_gold: 100;
    win_condition: q3;
}

quest q1 {
    title: "Quete A";
    desc: "A a besoin de B.";
    requires: q2;
    unlocks: q3;
    rewards: xp 100;
}

quest q2 {
    title: "Quete B";
    desc: "B a besoin de A.";
    requires: q1;
    rewards: xp 100;
}

quest q3 {
    title: "Quete C";
    desc: "Jamais atteinte.";
    requires: q1;
    rewards: xp 200;
}