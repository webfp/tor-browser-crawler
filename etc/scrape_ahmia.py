from urllib2 import urlopen


def get_popular_hidden_services(limit=10, by="public_backlinks"):
    hs_urls = []
    ahmia_url = "https://ahmia.fi/stats/popularity"
    query_url = "%s?limit=%s&order_by=%s" % (ahmia_url, limit, by)
    print("Querying %s" % query_url)
    query_res = urlopen(query_url).read()
    for line in query_res.split('\n'):
        if "about" in line:
            hs_urls.append("%s.onion" % line.split('"')[-2])
    return hs_urls


def save_popular_hidden_services(limit, by):
    hidden_services = get_popular_hidden_services(limit=limit, by=by)
    csv_file = "ahmia_fi_by_%s.csv" % by
    with open(csv_file, "w") as f:
        f.write("\n".join(hidden_services))
    print("%s top HSes by %s written into %s" % (limit, by, csv_file))


def main():
    save_popular_hidden_services(limit=100, by="public_backlinks")
    save_popular_hidden_services(limit=100, by="tor2web")
    save_popular_hidden_services(limit=100, by="clicks")

if __name__ == '__main__':
    main()
