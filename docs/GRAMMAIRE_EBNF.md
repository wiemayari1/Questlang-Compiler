# Grammaire Formelle QuestLang - EBNF

## 1. Structure generale

```ebnf
program        = { declaration } ;
declaration    = world_decl | quest_decl | item_decl | npc_decl | func_decl ;
```

## 2. Bloc world

```ebnf
world_decl     = "world" identifier "{" world_body "}" ;
world_body     = [ start_field ] [ start_gold_field ] [ win_condition_field ] ;
start_field    = "start" ":" identifier ";" ;
start_gold_field = "start_gold" ":" number ";" ;
win_condition_field = "win_condition" ":" identifier ";" ;
```

## 3. Bloc quest

```ebnf
quest_decl     = "quest" identifier "{" quest_body "}" ;
quest_body     = { quest_field } [ script_block ] ;
quest_field    = title_field | desc_field | requires_field | unlocks_field
               | rewards_field | costs_field | condition_field ;
title_field    = "title" ":" string ";" ;
desc_field     = "desc" ":" string ";" ;
requires_field = "requires" ":" identifier_list ";" ;
unlocks_field  = "unlocks" ":" identifier_list ";" ;
rewards_field  = "rewards" ":" reward_list ";" ;
costs_field    = "costs" ":" reward_list ";" ;
condition_field = "condition" ":" string ";" ;

reward_list    = reward_item { "," reward_item } ;
reward_item    = "xp" number | "gold" number | number identifier ;
identifier_list = identifier { "," identifier } ;
```

## 4. Bloc item

```ebnf
item_decl      = "item" identifier "{" item_body "}" ;
item_body      = { item_field } ;
item_field     = title_field | value_field | stackable_field | type_field ;
value_field    = "value" ":" number ";" ;
stackable_field = "stackable" ":" boolean ";" ;
type_field     = "type" ":" item_type ";" ;
item_type      = "weapon" | "armor" | "consumable" | "material" | "artifact" ;
```

## 5. Bloc npc

```ebnf
npc_decl       = "npc" identifier "{" npc_body "}" ;
npc_body       = { npc_field } ;
npc_field      = title_field | location_field | gives_quest_field ;
location_field = "location" ":" identifier ";" ;
gives_quest_field = "gives_quest" ":" identifier_list ";" ;
```

## 6. Bloc script (instructions QuestLang)

```ebnf
script_block   = "script" "{" { statement } "}" ;
statement      = var_decl | assignment | if_stmt | while_stmt | for_stmt
               | give_stmt | take_stmt | call_stmt | return_stmt ;

var_decl       = "var" identifier [ "=" expression ] ";" ;
assignment     = identifier "=" expression ";" ;
if_stmt        = "if" "(" expression ")" "{" { statement } "}" [ else_clause ] ;
else_clause    = "else" "{" { statement } "}" ;
while_stmt     = "while" "(" expression ")" "{" { statement } "}" ;
for_stmt       = "for" "(" identifier "in" identifier ")" "{" { statement } "}" ;
give_stmt      = "give" identifier expression ";" ;
take_stmt      = "take" identifier expression ";" ;
call_stmt      = "call" identifier "(" [ arg_list ] ")" ";" ;
return_stmt    = "return" [ expression ] ";" ;
```

## 7. Fonctions utilisateur

```ebnf
func_decl      = "func" identifier "(" [ param_list ] ")" "{" { statement } "}" ;
param_list     = identifier { "," identifier } ;
arg_list       = expression { "," expression } ;
```

## 8. Expressions

```ebnf
expression     = or_expr ;
or_expr        = and_expr { "or" and_expr } ;
and_expr       = eq_expr { "and" eq_expr } ;
eq_expr        = rel_expr { ( "==" | "!=" ) rel_expr } ;
rel_expr       = add_expr { ( "<" | ">" | "<=" | ">=" ) add_expr } ;
add_expr       = mul_expr { ( "+" | "-" ) mul_expr } ;
mul_expr       = pow_expr { ( "*" | "/" | "%" ) pow_expr } ;
pow_expr       = unary_expr [ "^" pow_expr ] ;
unary_expr     = [ "-" | "not" ] primary ;
primary        = number | string | boolean | identifier
               | identifier "(" [ arg_list ] ")"
               | "(" expression ")" ;
```

## 9. Types et litteraux

```ebnf
number         = digit { digit } [ "." digit { digit } ] ;
string         = """ { any_char_except_quote } """ ;
boolean        = "true" | "false" ;
identifier     = letter { letter | digit | "_" } ;
letter         = "a" .. "z" | "A" .. "Z" ;
digit          = "0" .. "9" ;
```

## 10. Commentaires

```ebnf
comment        = line_comment | block_comment ;
line_comment   = "//" { any_char } newline ;
block_comment  = "/*" { any_char } "*/" ;
```

---

## Remarques sur la grammaire

- **LL(1)** : La grammaire est conçue pour être analysée par un parser récursif descendant LL(1). Aucune récursivité à gauche n'est présente.
- **Associativité** : Les opérateurs `+`, `-`, `*`, `/`, `%` sont associatifs à gauche. L'opérateur `^` (puissance) est associatif à droite.
- **Précédence** : `not` > `^` > `* / %` > `+ -` > `< > <= >=` > `== !=` > `and` > `or`.
- **Ambiguïté** : Aucune ambiguïté dans la grammaire. Les blocs `quest`, `item`, `npc` sont distingués par leur mot-clé initial.
