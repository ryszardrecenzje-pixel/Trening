# 🏋️ Home Workout – Trening w domu

Aplikacja Streamlit do treningu w domu z planami dopasowanymi do sprzętu.

## Funkcje

- **Sprzęt** – checklista (masa ciała, hantle, drążek, gumy, ławka, TRX, skakanka)
- **Generator** – cel, czas (15/30/45), poziom + opcjonalna **rozgrzewka**
- **GIF-y** – animacja techniki każdego ćwiczenia
- **Stoper** – Start / Stop, **3 s zwłoki**, dźwięki 3–2–1 i koniec
- **Historia** – zapis JSON + **streak**, statystyki tygodnia
- **RPE + notatka** po treningu
- **Ulubione plany** – szybki start
- **Zamienniki** i **wskazówki bezpieczeństwa**
- **PL / EN**, eksport/import backupu
- **Onboarding** przy pierwszym uruchomieniu

> Supabase / logowanie – później. Na Streamlit Cloud pliki mogą znikać po restarcie → **Eksport** w zakładce Więcej.

## Uruchomienie

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy (Streamlit Cloud)

1. Push na GitHub
2. https://share.streamlit.io → New app
3. Main file: `app.py`

## Struktura

```
app.py
data/exercises.py
utils/workout.py storage.py audio.py i18n.py
user_data/          # runtime JSON
.streamlit/config.toml
```
