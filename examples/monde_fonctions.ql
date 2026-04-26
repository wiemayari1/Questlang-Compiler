world test_fonctions {
    start: q1;
    start_gold: 50;
    win_condition: q2;
}

func calculer_bonus(niveau) {
    var bonus = niveau * 10;
    if (bonus > 50) {
        return bonus;
    }
    return 50;
}

func verifier_or(montant) {
    if (montant >= 100) {
        return true;
    }
    return false;
}

quest q1 {
    title: "Test de Fonctions";
    desc: "Test des fonctions utilisateur.";
    unlocks: q2;
    rewards: xp 100, gold 25;

    script {
        var niveau = 5;
        var bonus = call calculer_bonus(niveau);
        give xp bonus;

        var riche = call verifier_or(bonus);
        if (riche) {
            give gold 10;
        }
    }
}

quest q2 {
    title: "Fin";
    desc: "Victoire.";
    requires: q1;
    rewards: xp 200;
}