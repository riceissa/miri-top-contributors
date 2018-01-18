This is for https://github.com/vipulnaik/donations

Specific issue: https://github.com/vipulnaik/donations/issues/20

There are two scripts here:

- `scrape.py`: This is the incremental scraper.
  It will download just the latest version
  of the top donors/contributors page and will check that against the donations
  database to see what new donations have been made since the last time the
  donations database was updated. It then outputs this latest round of
  donations as a SQL file for use in the donations database.
- `scrape2.py`: This is the historical scraper.
  It will download each Internet Archive snapshot of the top donors page and
  will infer all donations that have been made historically (since early 2015,
  when the top donors page first appeared).
  It has two output formats depending on the argument you give to it.
  When run with the `by_donor` argument (like `./scrape2.py by_donor > out`),
  it will list each donor along with
  donations from the DLW database and the donations from the top donors page,
  so that you can compare which donations are tracked where. It looks like
  [this](https://gist.github.com/riceissa/2f213d7a58aa5edd6488ab69c4fd871d).
  When run with the `sql` argument, it will SQL tuples of the donations
  inferred from the top donors page snapshots. It looks like
  [this](https://gist.github.com/riceissa/0d04ce0584bd5fbe70fbe768faa23d18).

## License

CC0.
