# mfr-resourcepack

Resource pack pubblico di **Minecraft Fantasy Roleplay** (il codice del server è nel repository privato
`giuliogiampieri/minecraft-fantasy-roleplay`). Il server lo propone ai giocatori all'ingresso, senza obbligo.

## Contenuto
- **Monete Fidoro** (1, 5, 10, 20, 50, 100, 200, 500 F), 64×64: `assets/mfr/textures/item/`.
- **Banco Magico del Fidoro**, cubo con 6 facce 64×64: `assets/mfr/textures/block/`.
- Definizioni degli oggetti (`assets/minecraft/items/`): pepite d'oro e magnetite mostrano il disegno solo se
  l'oggetto porta il dato `custom_model_data` impostato dal plugin (`fidoro_<valore>`, `banco_magico`);
  altrimenti restano gli oggetti normali. Chi rifiuta il pack vede pepite d'oro con il nome della moneta.
- **Schermata del banco** (finestra tipo baule da 6 righe): lo sfondo è un carattere del font `mfr:banco`
  (``, con gli spostamenti ``–``), il saldo usa le cifre del font `mfr:saldo`. Le monete dei
  pulsanti usano `assets/mfr/items/fidoro_<valore>.json` (componente `item_model`). Si rigenerano dal disegno in
  `sorgenti/banco-schermata.png` con `python3 genera_schermata.py`.
- **Barra del mana** (riempimento blu della barra dell'esperienza, dove il server mostra il mana 0–100):
  `assets/minecraft/textures/gui/sprites/hud/experience_bar_progress.png`, 182×5 a tutta altezza (sembra più spessa), sfumata da blu a viola, disegno originale generato da
  `python3 genera_barra_mana.py`. Lo sfondo della barra e il numero (verde) restano quelli del gioco.
- `sorgenti/`: immagini originali fornite dal proprietario, da cui sono ricavate le texture.

## Costruire e pubblicare
```bash
python3 costruisci.py      # scrive mfr-resourcepack.zip e ne stampa la SHA-1 (sempre la stessa per lo stesso contenuto)
```
Il plugin scarica lo zip dall'indirizzo `raw.githubusercontent.com` **di un commit preciso** (non cambia mai) e ne
controlla la SHA-1. A ogni modifica del pack si aggiornano indirizzo e SHA-1 nel plugin con una pull request.

Formato: Minecraft 26.3 (`pack_format` 97.1).
