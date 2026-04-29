program        = { declaration } ;

declaration    = world_decl
| quest_decl
| item_decl
| npc_decl
| var_decl
| func_decl ;

world_decl     = "world" IDENTIFIER "{" { world_member } "}" ;
world_member   = "start" ":" expression ";"
| "start_gold" ":" expression ";"
| "win_condition" ":" expression ";"
| var_decl ;

quest_decl     = "quest" IDENTIFIER "{" { quest_member } "}" ;
quest_member   = "title" ":" expression ";"
| "desc" ":" expression ";"
| "requires" ":" id_list ";"
| "unlocks" ":" id_list ";"
| "rewards" ":" reward_list ";"
| "costs" ":" reward_list ";"
| "condition" ":" expression ";"
| script_block ;

item_decl      = "item" IDENTIFIER "{" { item_member } "}" ;
item_member    = "title" ":" expression ";"
| "value" ":" expression ";"
| "stackable" ":" expression ";"
| "type" ":" IDENTIFIER ";"
| "type" ":" type_name ";" ;

npc_decl       = "npc" IDENTIFIER "{" { npc_member } "}" ;
npc_member     = "title" ":" expression ";"
| "location" ":" IDENTIFIER ";"
| "gives_quest" ":" id_list ";" ;

func_decl      = "func" IDENTIFIER "(" [ param_list ] ")" block ;
param_list     = IDENTIFIER { "," IDENTIFIER } ;

var_decl       = "var" IDENTIFIER "=" expression ";" ;
script_block   = "script" block ;

block          = "{" { statement } "}" ;
statement      = var_decl
| if_stmt
| while_stmt
| for_stmt
| return_stmt
| give_stmt
| take_stmt
| call_stmt
| assignment
| expr_stmt ;

if_stmt        = "if" "(" expression ")" block [ "else" block ] ;
while_stmt     = "while" "(" expression ")" block ;
for_stmt       = "for" IDENTIFIER "in" expression block ;
return_stmt    = "return" expression ";" ;
give_stmt      = "give" reward_list ";" ;
take_stmt      = "take" reward_list ";" ;
call_stmt      = "call" IDENTIFIER "(" [ arg_list ] ")" ";" ;
assignment     = IDENTIFIER ( "=" | "+=" | "-=" ) expression ";" ;
expr_stmt      = expression ";" ;

arg_list       = expression { "," expression } ;
id_list        = IDENTIFIER { "," IDENTIFIER } ;
reward_list    = reward { "," reward } ;
reward         = "xp" expression
| "gold" expression
| expression IDENTIFIER ;

expression     = or_expr ;
or_expr        = and_expr { "or" and_expr } ;
and_expr       = equality_expr { "and" equality_expr } ;
equality_expr  = comparison_expr { ( "==" | "!=" ) comparison_expr } ;
comparison_expr= additive_expr { ( "<" | "<=" | ">" | ">=" ) additive_expr } ;
additive_expr  = multiplicative_expr { ( "+" | "-" ) multiplicative_expr } ;
multiplicative_expr = power_expr { ( "*" | "/" | "%" ) power_expr } ;
power_expr     = unary_expr { "^" unary_expr } ;
unary_expr     = [ "-" | "not" ] primary ;

primary        = NUMBER
| STRING
| "true"
| "false"
| IDENTIFIER
| IDENTIFIER "(" [ arg_list ] ")"
| IDENTIFIER "[" expression "]"
| IDENTIFIER "." IDENTIFIER
| "(" expression ")"
| list_literal ;

list_literal   = "[" [ expression { "," expression } ] "]" ;
type_name      = "int" | "float" | "bool" | "string" | "list" ;

IDENTIFIER     = letter { letter | digit | "_" } ;
NUMBER         = digit { digit } [ "." digit { digit } ] ;
STRING         = '"' { character } '"' ;
letter         = "A" | ... | "Z" | "a" | ... | "z" | "_" ;
digit          = "0" | ... | "9" ;
character      = ? any printable character except " ? ;