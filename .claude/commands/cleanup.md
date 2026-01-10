---
description: Remove AI-generated code slop and inconsistencies
---

# Cleanup

Check the diff against main, and remove all AI generated slop introduced in this branch.

This includes:
- Extra comments that a human wouldn't add or is inconsistent with the rest of the file
- Extra defensive checks or try/catch blocks that are abnormal for that area of the codebase (especially if called by trusted / validated codepaths)
- Casts to any to get around type issues
- Any other style that is inconsistent with the file

Also please double check your work and what you generated. 
- Is it really complete? 
- Did you approach it from different angles? 

Define first at what angles you can approach it. 
Reiterate on the goal and what it means and what is required to achieve it.
Define what "complete" means in this context.

Proceed with the double check only after you are sure you have done all of the above.

Ultrathink!

$ARGUMENTS