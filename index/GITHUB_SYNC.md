# GitHub Synchronization

The local checkout is initialized as a Git repository on branch `main`.

## Add Remote

Create a private GitHub repository named `experience-vault`, then add it:

```bash
git -C /home/l30002999/experience-vault remote add origin git@github.com:<owner>/experience-vault.git
```

## Pull Before Work

```bash
python /home/l30002999/experience-vault/scripts/experience_vault.py git-pull
```

If no remote exists, the command reports that remote setup is pending.

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
