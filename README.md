This is for https://github.com/vipulnaik/donations

Specific issue: https://github.com/vipulnaik/donations/issues/20

This script can do two things:

- When running with the `fresh` argument, it can download all the Internet
  Archive snapshots of the top donors/contributors page to reconstruct the
  history of donations. It then outputs this history as a SQL file for use in
  the donations database.
- When running with the `db` argument, it will download just the latest version
  of the top donors/contributors page and check that against the donations
  database to see what new donations have been made since the last time the
  donations database was updated.

## License

CC0.
