This is for https://github.com/vipulnaik/donations

Specific issue: https://github.com/vipulnaik/donations/issues/20

This script can do two things:

- When running with the `fresh` argument, it can download all the Internet
  Archive snapshots of the top donors/contributors page to reconstruct the
  history of donations. It then outputs this history as a SQL file for use in
  the donations database.
- When running with the `db` argument, it will download just the latest version
  of the top donors/contributors page and checks that against the donations
  database to see what new donations have been made since the last time the
  donations database was updated. It then outputs this latest round of
  donations as a SQL file for use in the donations database.

`out.sql` is a sample output when running with the `fresh` argument, i.e.
`./scrape.py fresh > out.sql`.

## License

CC0.
