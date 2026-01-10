---
description: Test the entire user-flow and all functionalities for errors.
argument-hint: []
---

# Command: Full UI Check

1. run `npm run dev` and use playwright to test the app. 
2. If an error stopping you from testing, end the tes there and generate the report.
3. After test is complete, list all errors found throughout the testing process by creating a md file for each problem encountered. Store groups of errors in `/docs/errors` folder as seperate files.

Notes:
- If you encounter an action you cannot do like logging in, STOP and ask the human to do it. After the human says "I'm done," continue testing.
- Do not create any error logs (not even a summary) if no errors are found.
- Do not close the playwright testing window after completion.
- If playwright MCP is not available or installed, STOP and ask the user to install it. Do not continue without using the Playwright MCP.
- If the underlying cause of an error is not surface level and roots from the system design or database structure of the application, label that error as CRITICAL.
- Do the minimal just enough to test all functionalities.
