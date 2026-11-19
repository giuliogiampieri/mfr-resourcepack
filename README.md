# mfr-resourcepack

Resource pack pubblico di **Minecraft Fantasy Roleplay** (il codice del server è nel repository privato
`giuliogiampieri/minecraft-fantasy-roleplay`). Il server lo propone ai giocatori all'ingresso, senza obbligo.

## Contenuto
- **Monete Fidoro** (1, 5, 10, 20, 50, 100, 200, 500 F), 64×64: `assets/mfr/textures/item/`.
- **Banco Magico del Fidoro**, cubo con 6 facce 64×64: `assets/mfr/textures/block/`.
- Definizioni degli oggetti (`assets/minecraft/items/`): pepite d'oro e magnetite mostrano il disegno solo se
  l'oggetto porta il dato `custom_model_data` impostato dal plugin (`fidoro_<valore>`, `banco_magico`);
  altrimenti restano gli oggetti normali. Chi rifiuta il pack vede pepite d'oro con il nome della moneta.
- `sorgenti/`: immagini originali fornite dal proprietario, da cui sono ricavate le texture.

## Costruire e pubblicare
```bash
python3 costruisci.py      # scrive mfr-resourcepack.zip e ne stampa la SHA-1 (sempre la stessa per lo stesso contenuto)
```
Il plugin scarica lo zip dall'indirizzo `raw.githubusercontent.com` **di un commit preciso** (non cambia mai) e ne
controlla la SHA-1. A ogni modifica del pack si aggiornano indirizzo e SHA-1 nel plugin con una pull request.

Formato: Minecraft 26.3 (`pack_format` 97.1).
