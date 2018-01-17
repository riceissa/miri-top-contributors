#!/usr/bin/env python3
# License: CC0

import requests
from bs4 import BeautifulSoup
import csv
import sys
import datetime
import re
import mysql.connector


# These are donors we track separately, so ignore them in this script.
IGNORED_DONORS = {
    "Open Philanthropy Project",
}


SNAPSHOTS = [
    "https://web.archive.org/web/20140403110808/https://intelligence.org/topdonors/",
    "https://web.archive.org/web/20140625101856/https://intelligence.org/topdonors/",
    "https://web.archive.org/web/20141116233057/https://intelligence.org/topdonors/",
    "https://web.archive.org/web/20150107070310/https://intelligence.org/topdonors/",
    "https://web.archive.org/web/20150405093831/https://intelligence.org/topdonors/",
    "https://web.archive.org/web/20150529195536/https://intelligence.org/topdonors/",
    "https://web.archive.org/web/20150717030404/https://intelligence.org/topdonors/",
    "https://web.archive.org/web/20150925051425/https://intelligence.org/topdonors/",
    "https://web.archive.org/web/20160115113719/https://intelligence.org/topdonors/",
    "https://web.archive.org/web/20160304081836/https://intelligence.org/topdonors/",
    "https://web.archive.org/web/20160519132619/https://intelligence.org/topdonors/",
    "https://web.archive.org/web/20160717181525/https://intelligence.org/topdonors/",
    "https://web.archive.org/web/20161015133929/https://intelligence.org/topdonors/",
    "https://web.archive.org/web/20170204024838/https://intelligence.org/topdonors/",
    "https://web.archive.org/web/20170412043722/https://intelligence.org/topcontributors/",
    "https://web.archive.org/web/20170627074344/https://intelligence.org/topcontributors/",
    "https://web.archive.org/web/20170929195133/https://intelligence.org/topcontributors/",
    "https://web.archive.org/web/20180117010054/https://intelligence.org/topcontributors/",
]


def main():
    # The empty dict is so that we add all donors from the first snapshot.
    dicts = [{}] + list(map(top_contributors, SNAPSHOTS))
    for i in range(len(dicts) - 1):
        print("On iteration", i, file=sys.stderr)
        diff_and_print(dicts[i], dicts[i+1])


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


def top_contributors(url):
    print("Downloading", url, file=sys.stderr)
    response = requests.get(url,
                            headers={'User-Agent': 'Mozilla/5.0 '
                                     '(X11; Linux x86_64) AppleWebKit/537.36 '
                                     '(KHTML, like Gecko) '
                                     'Chrome/63.0.3239.132 Safari/537.36'})
    soup = BeautifulSoup(response.content, "lxml")
    contributors = {}
    for tbody in soup.find_all("tbody"):
        for tr in tbody.find_all("tr"):
            cols = list(map(lambda x: x.text.strip(), tr.find_all("td")))
            donor = cols[0]
            amount = cols[1].replace("$", "").replace(",", "")

            # Make sure each donor appears only once in the list
            assert donor not in contributors

            contributors[donor] = float(amount)

    print("Has", len(contributors), "donors", file=sys.stderr)
    return contributors


def diff_and_print(older, newer):
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

    for donor in all_donors:
        diff = newer.get(donor, 0) - older.get(donor, 0)
        if diff > 0.01:
            # We have a new donation to process
            print(("    " if first else "    ,") + sql_tuple(donor, diff))
            first = False
        elif diff < -0.01 and donor in newer:
            raise ValueError(("Amount in DLW database exceeds MIRI top "
                             "contributors amount", donor))
    print(";")


def mysql_quote(x):
    '''
    Quote the string x using MySQL quoting rules. If x is the empty string,
    return "NULL". Probably not safe against maliciously formed strings, but
    whatever; our input is fixed and from a basically trustable source..
    '''
    if not x:
        return "NULL"
    x = x.replace("\\", "\\\\")
    x = x.replace("'", "''")
    x = x.replace("\n", "\\n")
    return "'{}'".format(x)


def sql_tuple(donor, amount):
    return ("(" + ",".join([
        mysql_quote(donor),  # donor
        mysql_quote("Machine Intelligence Research Institute"),  # donee
        str(amount),  # amount
        mysql_quote("FIXME"),  # donation_date
        mysql_quote("FIXME"),  # donation_date_precision
        mysql_quote("donee contributor list"),  # donation_date_basis
        mysql_quote("AI risk"),  # cause_area
        mysql_quote("https://intelligence.org/topcontributors/"),  # url
        mysql_quote(""),  # donor_cause_area_url
        mysql_quote(""),  # notes
        mysql_quote(""),  # affected_countries
        mysql_quote(""),  # affected_regions
    ]) + ")")


def snapshot_date(url):
    lst = url.split('/')
    date_part = lst[lst.index("web") + 1]
    return date_part[0:4] + "-" + date_part[4:6] + "-" + date_part[6:8]


if __name__ == "__main__":
    main()
