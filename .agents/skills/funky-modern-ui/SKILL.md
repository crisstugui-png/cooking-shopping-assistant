---
name: funky-modern-ui
description: >
  This skill should be used when designing, creating, or styling user interfaces (UI) in this project.
  It ensures the design is modern, funky, and visually engaging. It enforces using tasteful fun colors,
  avoiding boring colors and pure blacks, utilizing rounded buttons, and selecting fun typography.
metadata:
  author: Antigravity
  version: 1.0.0
---

# Funky & Modern UI Design Guidelines

This skill ensures that all user interfaces created in this project have a modern, funky, and high-energy feel. We avoid standard browser defaults, boring enterprise gray-and-blue palettes, and harsh pure blacks, opting instead for a tasteful, playful, and delightful aesthetic.

---

## 1. Funky & Tasteful Color System

### Avoid Boring/Default Colors & Pure Blacks
- **No Harsh Blacks:** Avoid `#000000`. Use rich deep violets, deep space blues, or warm dark chocolates (e.g., `#0e0d1a`, `#151226`, `#1c0d02`).
- **No Dry Grays:** Replace standard gray backgrounds and borders with soft pastel tones, cream shades, or translucent tinted backdrops.
- **No Generic Primaries:** Avoid plain `#ff0000` (red), `#0000ff` (blue), or `#00ff00` (green).

### Recommended Palette Themes
* Use harmonious, curated CSS variables to maintain a consistent theme:
```css
:root {
  /* Funky & Modern Neon-Pastel Theme */
  --bg-gradient: linear-gradient(135deg, #f7f3ff 0%, #fff5f8 100%);
  --text-dark: #1f1b2e; /* Deep rich indigo-black */
  --text-light: #fefeff;
  
  --color-primary: #fe5f55;   /* Coral Pink */
  --color-secondary: #7a66f4; /* Electric Lavender */
  --color-accent: #37db9c;    /* Bright Mint */
  --color-warning: #ffd166;   /* Sunny Yellow */
  
  /* Glassmorphism & Borders */
  --glass-bg: rgba(255, 255, 255, 0.45);
  --glass-border: rgba(255, 255, 255, 0.6);
  --shadow-playful: 0 8px 30px rgba(122, 102, 244, 0.15);
}
```

---

## 2. Rounded & Playful Components

To maintain a friendly, soft, and modern aesthetic, components must have generous border-radius properties and tactile interactions.

- **Generous Rounding (`border-radius`):**
  - Buttons: `12px` to `50px` (pill-shaped).
  - Cards / Containers: `16px` to `24px`.
- **Soft Shadows:** Avoid hard outlines; use soft, colored drop shadows matching the element's primary color context.
- **Micro-interactions & Hover States:** Elements should feel "alive" when interacted with:
  - Add scale transitions on buttons and cards (`transform: scale(1.03)` on hover).
  - Use smooth transition timing (`transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1)`).

---

## 3. Fun & Modern Typography

Default system sans-serif or times-new-roman feels too corporate or dated. Import and use playful, modern typefaces.

- **Google Fonts Recommendations:**
  - **Outfit** / **Quicksand** (Clean, round, geometric, friendly)
  - **Fredoka** / **Comfortaa** (Extra round, soft, highly funky)
  - **Plus Jakarta Sans** (Stylish, contemporary, high energy)
- **CSS Import Example:**
```css
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght=400;600;800&family=Comfortaa:wght=500;700&display=swap');

body {
  font-family: 'Outfit', sans-serif;
  color: var(--text-dark);
}

h1, h2, h3, .brand-logo {
  font-family: 'Comfortaa', cursive;
  font-weight: 700;
}
```

---

## 4. Design Examples & Templates

### Funky Button (Vanilla CSS)
```css
.funky-button {
  font-family: 'Outfit', sans-serif;
  font-weight: 600;
  font-size: 1rem;
  padding: 12px 28px;
  border: none;
  border-radius: 50px; /* Pill shape */
  background: linear-gradient(135deg, var(--color-primary) 0%, #ff857a 100%);
  color: var(--text-light);
  cursor: pointer;
  box-shadow: 0 6px 20px rgba(254, 95, 85, 0.3);
  transition: all 0.25s ease;
}

.funky-button:hover {
  transform: translateY(-2px) scale(1.04);
  box-shadow: 0 8px 25px rgba(254, 95, 85, 0.45);
}

.funky-button:active {
  transform: translateY(1px) scale(0.98);
}
```

### Funky Card Container (Vanilla CSS)
```css
.funky-card {
  background: var(--glass-bg);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid var(--glass-border);
  border-radius: 20px;
  padding: 24px;
  box-shadow: var(--shadow-playful);
  transition: transform 0.3s ease;
}

.funky-card:hover {
  transform: translateY(-4px);
}
```
