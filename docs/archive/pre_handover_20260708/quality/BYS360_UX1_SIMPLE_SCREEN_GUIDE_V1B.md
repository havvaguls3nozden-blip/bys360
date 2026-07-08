# BYS360 UX-1B Simple Screen Guide Verify Hotfix

This hotfix keeps the UX-1 simple screen guide behavior and replaces Turkish literal checks in the PowerShell verifier with ASCII-safe contract checks.

Reason: Windows PowerShell may read UTF-8 scripts without BOM using a non-UTF code page, so checks for strings like Turkish screen labels may fail even when the JavaScript is correct.

Success criteria:
- base.html loads UX-1 CSS and JS.
- JavaScript exports `window.BYS360UX1SimpleScreenGuide`.
- JavaScript contains context contract keys and long-text simplifier function.
- CSS contains quick logic card and collapsible text classes.
