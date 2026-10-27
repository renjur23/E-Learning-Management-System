# CourseCloud minimal education interface

The interface uses a single forest green accent (#24634e), warm white backgrounds, light sage sections, and system fonts. It prioritises finding a course, reading its curriculum, and accessing lessons.

- Catalogue: compact learning introduction, labelled search, consistent course cards.
- Course overview: light header, clearly separated curriculum and enrolment summary.
- Cart and checkout: neutral totals, one primary action, preserved Razorpay flow.
- Account: consistent menu, profile form, and purchase history navigation.
- Mobile: stacked content, wrapped navigation, at least 44px primary controls, no horizontal page overflow at 390px.
- Accessibility: visible keyboard focus, native details menus, Escape dismissal, labelled search and forms, reduced motion support.

Desktop and mobile screenshots are in docs/screenshots. They use fictional accounts and isolated demo data. Browser checks cover rendering, mobile overflow, and opening and closing the account menu. The Django test suite covers the existing learning and payment behaviour.
