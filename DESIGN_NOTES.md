# LearnOrbit study interface

The interface uses a calm academic palette with white reading surfaces, pale blue backgrounds, navy text, cobalt actions and teal category accents. The theme is applied across course discovery, lessons, assessments, mock tests, checkout and account pages.

## Typography

- Headings: Trebuchet MS, with Segoe UI and sans-serif fallbacks. Bold, upright headings replace the previous editorial serif and italic styles.
- Body: Segoe UI / system-ui, 16px with a 1.7 line height. Course descriptions use up to 70 characters per line where the layout permits.
- Hero headings: fluid 36-60px; page headings: 30-46px; card headings: 22px; labels: 12-15px.
- Fonts use local system stacks and have no external download dependency.

## Colour roles

| Role | Hex |
| --- | --- |
| Primary actions and focus | #2356b2 |
| Headings and main text | #18334f |
| Secondary text | #52667b |
| Page background | #f3f7fc |
| Reading surface | #ffffff |
| Borders | #d8e3ee |
| Selected states | #e8f0ff |
| Category accents | #14685f |
| Supporting teal surface | #e8f5f1 |

Measured contrast: main text/background 12.01:1; secondary text/white 5.92:1; white/primary button 6.90:1; teal/category background 5.79:1. The selected text pairs exceed 4.5:1. Timer urgency retains a separate red state and textual countdown.

The course and mock cards share cool blue/teal cover artwork, clear headings, restrained borders and rounded action buttons. Motion uses subtle entrances and hover feedback and respects reduced-motion preferences.

Desktop and mobile previews are in docs/screenshots. Fictional accounts and isolated demo databases are used. Browser checks cover all major pages, overflow at 320px and 390px, account-menu behaviour, quiz countdown and automatic submission. Django system checks pass.
