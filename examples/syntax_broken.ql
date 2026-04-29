// ============================================================
// Monde Syntaxiquement Brise - Test des erreurs lexicales/syntaxiques
// QuestLang v2.0
// ============================================================

world test {
  start: quete1;
  start_gold: 50;
  win_condition: quete2;
}

// ERREUR LEXICALE : caractere @ interdit dans une chaine ? Non, dans un identifiant
// On met le @ hors chaine pour etre sur
quest quete1 {
  title: "Test";
  rewards: xp 50;
}

// ERREUR LEXICALE volontaire sur la ligne suivante (decommentez pour tester)
// quest quete_err_lex { title: "Erreur @ ici"; }

// ERREUR SYNTAXIQUE : deux-points manquant apres 'title'
quest quete2 {
  title "Sans deux-points";
  rewards: xp 50, gold 20;
}

// ERREUR SYNTAXIQUE : virgule manquante entre les recompenses
quest quete3 {
  title: "Virgule manquante";
  rewards: xp 50 gold 20;
  unlocks: quete4;
}

// ERREUR SYNTAXIQUE : point-virgule manquant apres unlocks
quest quete4 {
  title: "Point virgule manquant";
  rewards: xp 10;
  unlocks: quete5
}

// ERREUR SEMANTIQUE : quete5 n'existe pas (pour montrer la difference)
quest quete5 {
  title: "Quete finale";
  rewards: xp 100;
}
