#!/usr/bin/env python3
# License: CC0

import requests
from bs4 import BeautifulSoup
import sys
import datetime
import mysql.connector

from util import *


SNAPSHOTS = [
    "https://web.archive.org/web/20120719220051/http://singularity.org:80/topdonors/",
    "https://web.archive.org/web/20120918094656/http://singularity.org:80/topdonors/",
    "https://web.archive.org/web/20121019075109/http://singularity.org:80/topdonors/",
    "https://web.archive.org/web/20121118064729/http://singularity.org:80/topdonors/",
    "https://web.archive.org/web/20130115144542/http://singularity.org/topdonors/",
    "http://archive.today/2013.10.21-235551/http://intelligence.org/topdonors/",
    "http://archive.today/2014.10.10-021359/http://intelligence.org/topdonors/",
    "https://web.archive.org/web/20150117213932/https://intelligence.org/donortools/topdonors.php",
    "https://web.archive.org/web/20150507195856/https://intelligence.org/donortools/topdonors.php",
    "https://web.archive.org/web/20150717072918/https://intelligence.org/donortools/topdonors.php",
    "https://web.archive.org/web/20160115172820/https://intelligence.org/donortools/topdonors.php",
    "https://web.archive.org/web/20160226145912/https://intelligence.org/donortools/topdonors.php",
    "https://web.archive.org/web/20160717181643/https://intelligence.org/donortools/topdonors.php",
    "https://web.archive.org/web/20170204024838/https://intelligence.org/topdonors/",
    "https://web.archive.org/web/20170412043722/https://intelligence.org/topcontributors/",
    "https://web.archive.org/web/20170627074344/https://intelligence.org/topcontributors/",
    "https://web.archive.org/web/20170929195133/https://intelligence.org/topcontributors/",
    "https://web.archive.org/web/20171003083300/https://intelligence.org/topcontributors/",
    "https://web.archive.org/web/20171223071315/https://intelligence.org/topcontributors/",
    "https://web.archive.org/web/20180117010054/https://intelligence.org/topcontributors/",
    "https://web.archive.org/web/20180407192941/https://intelligence.org/topcontributors/",
    "https://web.archive.org/web/20180816004558/https://intelligence.org/topcontributors/",
]


def main():
    try:
        option = sys.argv[1]
    except IndexError:
        print("Please use 'by_donor' or 'sql' as arg 1", file=sys.stderr)
        sys.exit()
    web = web_donations()
    if option == "by_donor":
        db = db_donations()
    else:
        db = []
    all_donors = sorted(set(x["donor"] for x in db)
                        .union(x["donor"] for x in web)
                        .difference(IGNORED_DONORS))
    for donor in all_donors:
        f = lambda x: x["donor"] == donor
        web_d = list(filter(f, web))
        if option == "by_donor":
            db_d = list(filter(f, db))
        if option == "by_donor":
            print(donor, "\n    db:", db_d, "\n    web:", web_d)
        else:
            for donation in web_d:
                print(sql_tuple(donor, donation["amount"],
                                donation["donation_date"], donation["url"]))


def web_donations():
    donations = []
    # The empty dict is so that we add all donors from the first snapshot.
    dicts = [{}] + list(map(lambda x: top_donors(x, use_local_snapshots=True), SNAPSHOTS))
    dates = [snapshot_date(SNAPSHOTS[0])] + list(map(snapshot_date, SNAPSHOTS))
    for i in range(len(dicts) - 1):
        print("On iteration", i, file=sys.stderr)
        donations.extend(diff(dicts[i], dates[i], dicts[i+1], dates[i+1],
                              SNAPSHOTS[i]))
    return donations


def db_donations():
    # Load up existing MIRI donations from our database so we know what we have
    # already covered.
    cnx = mysql.connector.connect(user='issa', database='donations')
    cursor = cnx.cursor()
    cursor.execute("""select donor,amount,donation_date,url
                      from donations
                      where donee='Machine Intelligence Research Institute';""")
    donations = [{"donor": donor, "amount": float(amount),
                  "donation_date": donation_date.strftime("%Y-%m-%d"),
                  "url": url}
                 for donor, amount, donation_date, url in cursor]
    cursor.close()
    cnx.close()
    return donations


def diff(older, older_date, newer, newer_date, donation_url):
    """Take two cumulative contributor lists, older and newer. Find the
    difference in donation amounts since older, and return a list of donations
    that must have taken place."""
    result = []
    all_donors = (set(older.keys()).union(newer.keys())
                                   .difference(IGNORED_DONORS))
    for donor in sorted(all_donors):
        diff_amount = newer.get(donor, 0) - older.get(donor, 0)
        if diff_amount > 0.01:
            # We have a new donation to process
            result.append({"donor": donor, "amount": diff_amount,
                           "donation_date": newer_date,
                           "url": donation_url})
        elif diff_amount < -0.01:
            print("Amount in older exceeds amount in newer: {} {} ({}) > {} ({})"
                  .format(donor, older.get(donor, 0), older_date,
                          newer.get(donor, 0), newer_date),
                  file=sys.stderr)
            result.append({"donor": donor, "amount": diff_amount,
                           "donation_date": newer_date,
                           "url": donation_url})
    return result


if __name__ == "__main__":
    main()
