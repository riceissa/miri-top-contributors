#!/usr/bin/env python3
# License: CC0

import requests
from bs4 import BeautifulSoup
import sys
import datetime
import mysql.connector

from util import *


def main():
    diff_and_print(db_donors(),
                   top_donors("https://intelligence.org/topcontributors/"),
                   datetime.date.today().strftime("%Y-%m-%d"))


def db_donors():
    # Load up existing MIRI donations from our database so we know what has
    # happened since whenever we last updated MIRI donor info.
    cnx = mysql.connector.connect(user='issa', database='donations')
    cursor = cnx.cursor()
    cursor.execute("""select donor,sum(amount)
                      from donations where
                      donee='Machine Intelligence Research Institute'
                      group by donor;""")
    existing_donors = {donor: float(amount) for donor, amount in cursor}
    cursor.close()
    cnx.close()
    return existing_donors


def diff_and_print(older, newer, newer_date):
    """Take two contributor lists, older and newer. Find the difference in
    donation amounts since older, and just print SQL insert lines for that
    difference."""
    all_donors = (set(older.keys()).union(newer.keys())
                                   .difference(IGNORED_DONORS))
    first = True
    print("""insert into donations (donor, donee, amount, donation_date,
    donation_date_precision, donation_date_basis, cause_area, url,
    donor_cause_area_url, notes, affected_countries,
    affected_regions) values""")

    for donor in sorted(all_donors):
        diff = newer.get(donor, 0) - older.get(donor, 0)
        if diff > 0.01:
            # We have a new donation to process
            print(("    " if first else "    ,") +
                  sql_tuple(donor, diff, newer_date,
                            "https://intelligence.org/topcontributors/"))
            first = False
        elif diff < -0.01 and donor in newer:
            print("Amount in older exceeds amount in newer:",
                  donor, older[donor], ">", newer[donor], file=sys.stderr)
    print(";")


if __name__ == "__main__":
    main()
