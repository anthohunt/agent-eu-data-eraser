# Security and privacy

*English · [Français](SECURITY.fr.md)*

## What is stored, and where
Everything personal stays on the user's machine, in `donnees/` (git-ignored, permissions 700/600): the identifiers to erase, mailbox access, optional ID copy, log, copies of sent and received emails, complaint files. The repository only holds the code, the templates and the public broker list.

## Risks considered
- **A fake broker in the list** would receive every user's name, emails, phone and postal addresses. Mitigation: an address enters the shared list only with a page on the broker's own domain that publishes it, accepted by a human maintainer; each user also approves every new address before their agent writes to it, and the agent only writes to an address on one of the broker's domains.
- **A fake "broker" email asking for your ID**: the agent replies only to a request signed (DKIM, as recorded by your own provider's topmost Authentication-Results header) by one of the broker's exact domains and aligned with the sender, only to the approved address in the list (never to the requester), once per broker, with a copy watermarked "Demande RGPD à <broker>, <date>, usage unique". Without an ID file, the request comes back to the user.
- **A booby-trapped link**: the agent opens a confirmation link only from an authenticated email, and only if the link's host belongs to the broker's domains.
- **A web page that gives orders to the research agent**: it runs in a temporary folder that holds only the public list (never `donnees/`), with web search and fetch, read access to that folder and write access to its single proposals file, and no shell. Its output is validated before being copied back.
- **Spam sorting (optional) sends your new mail to an AI model**: sender, subject, authentication header and the first 1,200 characters of each email go to the model you run (Claude Haiku through your own Claude Code account by default). The model has no tools and runs in an empty folder: an email that tries to give it orders can at worst get itself kept or moved, never trigger an action. A moved email stays recoverable for 30 days, and the model is told to keep anything in doubt.
- **Mailbox access**: an app password dedicated to the agent; deleting it at the provider cuts the agent off without touching anything else.

## Reporting a problem
Open an issue without any personal data in it or, for a vulnerability, contact the maintainer through the GitHub profile of the project.
