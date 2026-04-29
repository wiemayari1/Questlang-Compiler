world test_lexical {
    start: q1;
}

quest q1 {
    title: "Le debut de l'aventure";
    desc: "Ceci est une description valide.";
    
    // Le caractere @ n'est pas reconnu par le langage (hors d'une chaine de caracteres)
    @erreur_ici: 100;
}
