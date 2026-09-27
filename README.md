# 🏋️ Home Workout – Trening w domu

Kompletna aplikacja do treningu w domu z **dynamicznym dostosowywaniem planów** do posiadanego sprzętu.

Zbudowana w **Streamlit** – gotowa do wrzucenia na GitHub i wdrożenia na [Streamlit Community Cloud](https://streamlit.io/cloud).

---

## Funkcje

| Moduł | Opis |
|-------|------|
| **🛠️ Sprzęt** | Checklista: masa ciała, hantle, drążek, gumy, ławka, TRX, skakanka |
| **📚 Baza ćwiczeń** | 30+ ćwiczeń z partiami mięśniowymi, poziomem i wymaganym sprzętem |
| **⚡ Generator** | Cel (spalanie / siła / FBW / wytrzymałość) + czas (15/30/45 min) + poziom |
| **▶️ Gracz treningu** | Krok po kroku, stoper, przerwy, postęp |
| **📜 Historia** | Zapis sesji w `st.session_state` (w sesji przeglądarki) |

---

## Szybki start (lokalnie)

```bash
git clone https://github.com/TWOJ_USER/home-workout-streamlit.git
cd home-workout-streamlit
pip install -r requirements.txt
streamlit run app.py
```

Otwórz http://localhost:8501

---

## Wdrożenie na Streamlit Cloud (z GitHub)

1. Wrzuć repozytorium na GitHub (publiczne lub prywatne).
2. Wejdź na [share.streamlit.io](https://share.streamlit.io).
3. Kliknij **New app**.
4. Wybierz swoje repozytorium.
5. **Main file path**: `app.py`
6. Kliknij **Deploy**.

Gotowe – aplikacja będzie dostępna pod adresem typu:
`https://twoj-user-home-workout-streamlit-app-xxxx.streamlit.app`

---

## Struktura projektu

```
home-workout-streamlit/
├── app.py                  # Główna aplikacja Streamlit
├── data/
│   └── exercises.py        # Baza 30+ ćwiczeń + etykiety PL
├── utils/
│   └── workout.py          # Generator treningu + filtrowanie
├── .streamlit/
│   └── config.toml         # Dark theme (zielony + pomarańczowy)
├── requirements.txt
└── README.md
```

---

## Design

- **Mobile-First** (max ~480 px)
- Dark mode: tło `#0a0a0f`, akcent `#22c55e` (neon zielony)
- Duże przyciski, czytelne karty
- Nawigacja dolna: Trening | Sprzęt | Historia

---

## Uwagi techniczne

- **Stan** – `st.session_state` (działa w ramach sesji przeglądarki).
- **Timery** – odliczanie z `time.sleep` (działa dobrze na krótkich przerwach 30–60 s).
- **Brak logowania** – wszystko lokalne w sesji.
- Aby zachować historię między sesjami, można dodać np. SQLite lub Google Sheets (opcjonalnie).

---

## Licencja

MIT – używaj swobodnie.
