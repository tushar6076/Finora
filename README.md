# 🪙 Finora – Smart Account Management

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Download APK](https://img.shields.io/badge/Download-Latest%20APK-0078D4?style=for-the-badge&logo=android)](https://github.com/tushar6076/Finora/releases/latest)

**Finora** is a high-performance, privacy-centric **account management engine** built for developers and professionals who demand speed and data sovereignty. Finora eliminates cloud risks by keeping your sensitive financial records exactly where they belong: **on your device.**

---

## 📥 Download & Install
Experience Finora on your Android device:
1. Navigate to the [Releases](https://github.com/tushar6076/Finora/releases/latest) page.
2. Download the `finora-arm64-v8a-debug.apk`.
3. Install and manage your accounts with 100% offline security.

> **Note:** Optimized for modern 64-bit processors (arm64-v8a).

---

## 🌟 Key Pillars
- **🔐 Zero-Cloud Privacy** – Fully offline architecture. No external servers, no telemetry, 100% local storage.
- **📄 Professional Exports** – Generate high-fidelity **XLSX reports** and **PDF receipts** using native Android sharing intents.
- **🚀 64-Bit Architecture** – Compiled strictly for **arm64-v8a** for maximum performance on modern hardware (e.g., Oppo Reno 8).
- **📂 Secure Storage** – Implements **Android SAF (Storage Access Framework)** and **FileProvider** for scoped, permission-compliant file handling.
- **🧹 Cache Management** – Automated "Silent Cleanup" logic that purges temporary export caches on exit.

---

## 🛠️ The Architect's Stack
- **Backend:** Python 3.11+
- **Frontend:** Kivy & KivyMD (Material Design 3 Logic)
- **Database:** SQLite / SQLAlchemy ORM
- **PDF Engine:** `fpdf2` (Modern PDF generation)
- **Excel Engine:** `XlsxWriter`
- **Bridge:** Pyjnius (JNI hooks for native Android APIs)

---

## 🚀 Development Roadmap
- [x] **v1.0:** Core Offline Management & XLSX Engine
- [x] **v1.1:** Android 14 FileProvider & Sharing Patches
- [ ] **v1.2:** **SQLCipher Integration** (AES-256 Database Encryption)
- [ ] **v1.3:** Biometric Lock (Fingerprint/Face Unlock)
- [ ] **v1.4:** Encrypted JSON Cloud-Vault (Optional Google Drive Sync)

---

## 🎥 Demo Preview
[![Finora Demo](https://img.youtube.com/vi/YOUR_VIDEO_ID/maxresdefault.jpg)](https://github.com/tushar6076/Finora/blob/main/demo.mp4)
> *Click the image above to view the full demo video.*

---

## 🤝 Contributing
Contributions are welcome! 
1. **Fork** the project.
2. Create your **Feature Branch** (`git checkout -b feature/AmazingFeature`).
3. **Commit** changes (`git commit -m 'Add AmazingFeature'`).
4. **Push** to the branch (`git push origin feature/AmazingFeature`).
5. Open a **Pull Request**.

---

## 📄 License
Distributed under the **MIT License**. See `LICENSE` for more information.

---
💡 *Finora: Account handling made **private, professional, and reliable**.*