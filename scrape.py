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


def main():
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

    # Now get the up-to-date top contributors info.
    response = requests.get("https://intelligence.org/topcontributors/",
                            headers={'User-Agent': 'Mozilla/5.0 '
                                     '(X11; Linux x86_64) AppleWebKit/537.36 '
                                     '(KHTML, like Gecko) '
                                     'Chrome/63.0.3239.132 Safari/537.36'})
    soup = BeautifulSoup(response.content, "lxml")
    top_contributors = {}
    for tbody in soup.find_all("tbody"):
        for tr in tbody.find_all("tr"):
            cols = list(map(lambda x: x.text.strip(), tr.find_all("td")))
            donor = cols[0]
            amount = cols[1].replace("$", "").replace(",", "")
            assert donor not in top_contributors
            top_contributors[donor] = float(amount)

    all_donors = (set(existing_donors.keys()).union(top_contributors.keys())
                                             .difference(IGNORED_DONORS))
    first = True
    print("""insert into donations (donor, donee, amount, donation_date,
    donation_date_precision, donation_date_basis, cause_area, url,
    donor_cause_area_url, notes, affected_countries,
    affected_regions) values""")

    for donor in all_donors:
        diff = top_contributors.get(donor, 0) - existing_donors.get(donor, 0)
        if diff > 0.01:
            # We have a new donation to process
            print(("    " if first else "    ,") + sql_tuple(donor, diff))
            first = False
        elif diff < -0.01 and donor in top_contributors:
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


if __name__ == "__main__":
    main()
