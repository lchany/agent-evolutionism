# GitHub Synchronization

The local checkout is initialized as a Git repository on branch `main`.

## Add Remote

Create a private GitHub repository named `experience-vault`, then add it:

```bash
git -C /home/l30002999/experience-vault remote add origin git@github.com:<owner>/experience-vault.git
```

## Pull Before Work

```bash
python /home/l30002999/experience-vault/scripts/experience_vault.py ensure-latest
```

If no remote exists, the command reports that remote setup is pending.

When multiple projects share this vault, always ensure the local checkout is current before reading or writing. `search`, `recall`, `distill`, `new`, and `archive` do this automatically unless `--no-pull` is supplied.

For write commands, the helper refuses to pull over local uncommitted changes. Review and sync local changes first, or intentionally retry with `--no-pull` after checking the diff.

## Review Before Commit

```bash
python /home/l30002999/experience-vault/scripts/experience_vault.py validate
python /home/l30002999/experience-vault/scripts/experience_vault.py git-review
```

## Commit

Use a specific message:

```bash
git -C /home/l30002999/experience-vault add .
git -C /home/l30002999/experience-vault commit -m "Initialize experience vault"
```

## Push

Push only after review:

```bash
git -C /home/l30002999/experience-vault push -u origin main
```

Do not push if validation reports potential secrets.
