world test_syntaxe {
    start: q1;
}

quest q1 {
    // Erreur syntaxique : on a oublie les deux-points ":" apres title
    title "Une quete mal formatee";
    desc: "Cette ligne ne sera probablement pas analysee.";
}
