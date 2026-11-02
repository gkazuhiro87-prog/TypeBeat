# 🎵 TypeBeat

**Turn your favorite songs into a typing challenge!**

TypeBeat is a rhythm-based typing game built with Python. Listen to your favorite songs, follow synchronized lyrics, and test your typing skills while the music plays.

Choose a song from your computer, find its lyrics automatically, and challenge yourself to keep up with the rhythm!

## ✨ Features

- 🎵 **Local Music Support** — Play songs directly from your computer.
- 📝 **Synchronized Lyrics** — Lyrics are synchronized with the music using LRC files.
- 🔎 **Automatic Lyrics Search** — Find synchronized lyrics through LRCLIB.
- ⌨️ **Typing Gameplay** — Type the lyrics as they appear on screen.
- 🎯 **Scoring System** — Earn points for every correct character.
- 🔥 **Combo System** — Build combos to increase your score multiplier.
- 📊 **Performance Tracking** — Track your score, accuracy, and mistakes.
- 🎨 **Visual Feedback** — Correct characters turn green, while mistakes turn red.

## 🎮 How to Play

1. Open TypeBeat.
2. Select a song from your computer.
3. Wait for the lyrics to be found or load an LRC file manually.
4. Get ready during the countdown.
5. Type the lyrics as they appear on screen.
6. Build combos, increase your multiplier, and get the highest score possible!

### Scoring System

Every correct character earns points based on your current combo.

| Combo | Multiplier |
|---|---:|
| 0–9 | x1 |
| 10–24 | x2 |
| 25–49 | x3 |
| 50–99 | x4 |
| 100+ | x5 |

- Correct character: 100 × multiplier points.
- Incorrect character: breaks your combo.
- Accuracy is calculated based on correct and incorrect characters.

## ⬇️ Download

**Windows**

Download the released version:

👉 [Download TypeBeat for Windows](https://github.com/gkazuhiro87-prog/TypeBeat/releases/latest)

1. Download the Windows ZIP file.
2. Extract the downloaded folder.
3. Open `TypeBeat.exe`.
4. Select a song and start playing!

No separate Python installation is required when using the packaged Windows version.

## 🛠️ Built With

- [Python](https://www.python.org/)
- [PySide6](https://doc.qt.io/qtforpython-6/)
- [Qt Multimedia](https://doc.qt.io/qtforpython-6/PySide6/QtMultimedia/index.html)
- [Mutagen](https://mutagen.readthedocs.io/)
- [LRCLIB](https://lrclib.net/)

## 💻 Running From Source

If you want to run the project from source:

**1. Clone the repository**

```bash
git clone https://github.com/gkazuhiro87-prog/TypeBeat.git
cd TypeBeat
```

**2. Install the dependencies**

```bash
py -m pip install PySide6 mutagen requests
```

**3. Run the game**

```bash
py main.py
```

## 📁 Project Structure

```text
TypeBeat/
├── main.py
├── game/
│   ├── __init__.py
│   ├── letras.py
│   └── busca_letra.py
├── assets/
├── songs/
├── icone.ico
└── README.md
```

## 📌 Notes

- TypeBeat uses local audio files selected by the player.
- Automatic lyrics search requires an internet connection.
- You can also load synchronized `.lrc` lyrics manually.
- Songs are not included in the repository.

## 👨‍💻 Author

Developed by [@gkazuhiro87-prog](https://github.com/gkazuhiro87-prog).

## 📄 License

This project is currently provided without an explicit open-source license. All rights are reserved by the author unless a license is added.

---

**Enjoy the music. Feel the rhythm. TypeBeat!** 🎵
