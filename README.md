# Projekt 3 - Scraping volebních výsledků

Tento projekt slouží k získání volebních výsledků z webu volby.cz pro volby do Poslanecké sněmovny 2017. Program stáhne data o všech obcích z vybraného územního celku a uloží je do CSV souboru.

## Popis funkcionality

Program provádí následující kroky:
1. Stáhne hlavní stránku územního celku
2. Extrahuje seznam všech obcí s jejich kódy a názvy
3. Pro každou obec stáhne detailní výsledky voleb
4. Získá data o počtu voličů, obálkách a platných hlasech
5. Extrahuje výsledky hlasování pro všechny politické strany
6. Exportuje všechna data do CSV souboru

## Instalace knihoven

### Vytvoření virtuálního prostředí (doporučeno)
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# nebo
venv\Scripts\activate     # Windows
```

### Instalace závislostí
```bash
pip install -r requirements.txt
```

### Ruční instalace knihoven
```bash
pip install beautifulsoup4 lxml pandas requests tqdm
```

## Použití programu

### Základní syntaxe
```bash
python main.py "URL_ADRESA" "NAZEV_SOUBORU.csv"
```

### Ukázka běhu programu

Pro zpracování dat okesu Prostějov zadejte následující údaje:

První argument: `https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=12&xnumnuts=7103`
Druhý argument: `vysledky.csv`
#### Spuštění programu z příkazové řádky:
```bash
python main.py "https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=12&xnumnuts=7103" "vysledky.csv"
```

### Výstup programu
```
Stahuji hlavní stránku...
Získávám seznam obcí...
Nalezeno 97 obcí ke zpracování.
--- Zahajuji stahování detailů pro všechny obce ---
Zpracovávám obce: 100%|████████████| 97/97 [00:45<00:00,  1.92obec/s]

Stahování detailů dokončeno.
Exportuji data do souboru: vysledky.csv
Data byla úspěšně uložena do vysledky.csv.
Program úspěšně dokončen.
```

## Struktura výstupního CSV souboru

Výstupní soubor obsahuje tyto sloupce:

| Sloupec | Popis |
|---------|-------|
| `code` | Kód obce |
| `location` | Název obce |
| `registered` | Počet registrovaných voličů |
| `envelopes` | Počet vydaných obálek |
| `valid` | Počet platných hlasů |
| `[Název strany]` | Počet hlasů pro jednotlivé politické strany |

### Ukázka výstupního souboru
```csv
code,location,registered,envelopes,valid,Občanská demokratická strana,...
506761,Alojzov,205,145,144,29,0,0,9,0,5,17,4,1,1,0,0,18,0,5,32,0,0,6,...
589268,Bedihošť,834,527,524,51,0,0,28,1,13,123,2,2,14,1,0,34,0,6,140,0,0,26,...
```

## Požadavky

- Python 3.8+
- Internetové připojení
- Platná URL adresa územního celku z webu volby.cz

## Poznámky

- Program automaticky zobrazuje progress bar během stahování dat
- Výstupní CSV soubor je kódován v UTF-8
- URL adresa musí být v uvozovkách kvůli speciálním znakům

## Struktura projektu

```
projekt_3/
├── main.py             # Hlavní soubor programu
├── requirements.txt    # Seznam závislostí
├── README.md           # Dokumentace
└── vysledky.csv        # Ukázkový výstupní soubor
```