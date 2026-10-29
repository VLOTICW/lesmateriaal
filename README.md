# ICW — lesmateriaal

Bronbestanden van de lessite. Elke push naar `main` bouwt en publiceert de site automatisch.

## Eenmalig instellen

1. Maak in je GitHub-organisatie een repository aan, bv. `lesmateriaal` (publiek op GitHub Free, privé kan met GitHub Team).
2. Upload de inhoud van deze map naar die repository (of push met git).
3. Repository → **Settings → Pages** → bij *Source* kiezen voor **GitHub Actions**.
4. Tabblad **Actions**: de workflow *Publiceer site* loopt; na ±1 minuut staat de site op
   `https://<organisatie>.github.io/lesmateriaal/`.

## Materiaal toevoegen

Zet een bestand in de juiste map en push:

```
inhoud/
  computationeel-denken/5icw/
  computationeel-denken/6icw/
  fysica-elektronica/5icw/
  fysica-elektronica/6icw/
  softwareontwikkeling/5icw/
  softwareontwikkeling/6icw/
```

- **Volgorde**: zet een volgnummer vooraan (`01-`, `02-`, …). Het nummer verschijnt niet op de site.
- **Naam op de site**: bij HTML-bestanden de `<title>`, anders de bestandsnaam
  (`03-wet-van-ohm.pdf` → *Wet van ohm*).
- **Tussenkoppen**: een submap wordt een tussenkop, bv. `fysica-elektronica/6icw/01-transistoren/`.
- **Pagina met eigen bestanden** (HTML met afbeeldingen, scripts…): zet alles in één submap met
  een `index.html`. Die submap verschijnt als één item.
- Nieuwe items krijgen 14 dagen het label *nieuw*.

Vakken of klassen hernoemen of toevoegen: pas `site.toml` aan en maak de bijhorende mappen.

## Links voor Teams

Per klasgroep een tabblad met de link naar het eigen luik; de andere klas blijft één klik verder:

- `…/computationeel-denken/#5icw`
- `…/fysica-elektronica/#6icw`
- enz.

## Lokaal testen

```
python build.py
```

en open daarna `_site/index.html`.

## Let op

De **site is openbaar** voor wie de link heeft, ook als de repository privé staat.
Geen leerlinggegevens, punten of nog niet vrijgegeven oplossingen in `inhoud/`.
