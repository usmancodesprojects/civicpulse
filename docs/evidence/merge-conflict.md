# Deliberate merge-conflict evidence

The frontend branch and deployment branch deliberately edited `.gitignore` independently. Merging commit `6087ba0` into the frontend work produced the following real conflict before merge commit `672570f` resolved it.

## Conflict markers

```text
<<<<<<< frontend
.env.*
!.env.example
__pycache__/
*.py[cod]
=======
.venv/
__pycache__/
*.py[cod]
*.egg-info/
>>>>>>> deployment
```

The same merge produced a second conflict around `node_modules/`, `dist/`, generated Vite files, editor metadata, and `docs/evidence/*` rules. The conflict can be reproduced without changing the working tree with:

```powershell
$base = git merge-base 2a85702 6087ba0
git merge-tree $base 2a85702 6087ba0
```

## Resolution and proof

The resolved `.gitignore` keeps both branches' valid exclusions, preserves `.env.example`, and keeps the evidence README tracked while ignoring intermediate generated evidence. This combined version won because choosing either side alone would either lose frontend-generated-file exclusions or remove deployment and evidence safeguards. Merge commit `672570f` records the resolution; `git show --cc 672570f -- .gitignore` shows the combined diff.
