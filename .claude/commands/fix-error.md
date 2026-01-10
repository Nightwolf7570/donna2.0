Review the error documentation in mentioned in the error report. Each error file contains structured information including the error description, root cause analysis, code snippets, reproduction steps, and suggested fixes.

Your task is to:

1. **Analyze the error** - Read and understand the error documentation thoroughly
2. **Locate the affected code** - Find the files and code mentioned in the root cause section
3. **Implement the fix** - Apply the suggested fix or develop an appropriate solution based on the root cause analysis
4. **Verify the fix** - Follow the reproduction steps to confirm the error is resolved
5. **Update documentation** - Mark the error as RESOLVED in the docs/errors file and add notes about the fix applied

If handling multiple errors, prioritize by status (CRITICAL > HIGH > MEDIUM > LOW).

After completion, log significant changes to the `/docs/CHANGELOG.md` file and commit your changes.

After fixing, provide a summary of:
- What was fixed
- Files modified
- How to verify the fix works
