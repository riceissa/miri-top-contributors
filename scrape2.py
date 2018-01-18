#!/usr/bin/env python3
# License: CC0

import requests
from bs4 import BeautifulSoup
import sys
import datetime
import mysql.connector


# These are donors we track separately, so ignore them in this script.
IGNORED_DONORS = {
    "Open Philanthropy Project",
    "Gordon Irlam",
    "Loren Merritt",
}


SNAPSHOTS = [
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
]


def main():
    web = web_donations()
    db = db_donations()
    all_donors = sorted(set(x["donor"] for x in db)
                        .union(x["donor"] for x in web)
                        .difference(IGNORED_DONORS))
    for donor in all_donors:
        f = lambda x: x["donor"] == donor
        web_d = list(filter(f, web))
        db_d = list(filter(f, db))
        # print(donor, "\n    db:", db_d, "\n    web:", web_d)
        for donation in web_d:
            print(sql_tuple(donor, donation["amount"],
                            donation["donation_date"], donation["url"]))


def web_donations():
    donations = []
    # The empty dict is so that we add all donors from the first snapshot.
    dicts = [{}] + list(map(top_donors, SNAPSHOTS))
    dates = ["2015-01-17"] + list(map(snapshot_date, SNAPSHOTS))
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


def top_donors(url):
    print("Downloading", url, file=sys.stderr)
    response = requests.get(url,
                            headers={'User-Agent': 'Mozilla/5.0 '
                                     '(X11; Linux x86_64) AppleWebKit/537.36 '
                                     '(KHTML, like Gecko) '
                                     'Chrome/63.0.3239.132 Safari/537.36'})
    soup = BeautifulSoup(response.content, "lxml")
    donors = {}
    for table in soup.find_all("table"):
        for tr in table.find_all("tr"):
            cols = list(map(lambda x: x.text.strip(), tr.find_all("td")))
            donor = donor_normalized(cols[0])
            amount = cols[1].replace("$", "").replace(",", "")

            # Make sure each donor appears only once in the list
            assert donor not in donors

            donors[donor] = float(amount)

    print("Has", len(donors), "donors", file=sys.stderr)
    return donors


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


def sql_tuple(donor, amount, donation_date, donation_url):
    return ("(" + ",".join([
        mysql_quote(donor),  # donor
        mysql_quote("Machine Intelligence Research Institute"),  # donee
        str(amount),  # amount
        mysql_quote(donation_date),  # donation_date
        mysql_quote("year"),  # donation_date_precision
        mysql_quote("donee contributor list"),  # donation_date_basis
        mysql_quote("AI risk"),  # cause_area
        mysql_quote(donation_url),  # url
        mysql_quote(""),  # donor_cause_area_url
        mysql_quote(""),  # notes
        mysql_quote(""),  # affected_countries
        mysql_quote(""),  # affected_regions
    ]) + ")")


def snapshot_date(url):
    lst = url.split('/')
    date_part = lst[lst.index("web") + 1]
    return date_part[0:4] + "-" + date_part[4:6] + "-" + date_part[6:8]


def donor_normalized(x):
    if x == "Johan Edstr\u0e23\u0e16m":
        return "Johan Edström"
    if x == "Marius van Voorden (via Bitcoin)":
        return "Marius van Voorden"
    return x


if __name__ == "__main__":
    main()
