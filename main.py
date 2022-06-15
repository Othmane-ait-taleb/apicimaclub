from source import *
from flask import *
from waitress import serve

http_proxy = os.getenv('HTTP_PROXY') if os.getenv('HTTP_PROXY') is not None else "http://10.23.201.11:3128"
https_proxy = os.getenv('HTTPS_PROXY') if os.getenv('HTTPS_PROXY') is not None else "http://10.23.201.11:3128"
ftp_proxy = os.getenv('FTP_PROXY') if os.getenv('FTP_PROXY') is not None else "ftp://10.23.201.11:3128"

proxies = {
    "http": http_proxy,
    "https": https_proxy,
    "ftp": ftp_proxy
}

port = "2096"
cimaclub = f"https://www.cima-club.io/"

def searchall(title: str, movie_or_series: Type, with_proxy=False):
    if with_proxy:
        search_result = BeautifulSoup(requests.get(cimaclub + "search", params={"s": title}, proxies=proxies).text,
                                      'html.parser')
    else:
        search_result = BeautifulSoup(requests.get(cimaclub + "search", params={"s": title}).text, 'html.parser')
    links = []
    titles = []
    for i in search_result.select('div[class*="media-block"] > div'):
        a = i.find_all('a')[-1]
        if movie_or_series == Type.movie and "series" not in a["href"] and 'season' not in a["href"]:
            links.append(a["href"])
            titles.append(a.text)
        elif movie_or_series == Type.series and 'season' in a["href"]:
            links.append(a["href"])
            titles.append(a.text)
    assert len(links) == len(titles)

    #####
    links_dict = dict()
    for i in range(len(titles)):
        links_dict[titles[i]] = links[i]
    sort_links = dict(sorted(links_dict.items(), key=lambda x: extract_season_number(x[0], with_proxy), reverse=False))
    links = list(sort_links.values())
    titles = list(sort_links.keys())
    for i in range(len(titles)):
        print(f"{titles[i]} : ({i + 1})")




def beautify_download_links(links: list):
    quality_link = {}
    for i in links:
        if "-240" in i:
            quality_link["240"] = i
        elif "-360" in i:
            quality_link["360"] = i
        elif "-480" in i:
            quality_link["480"] = i
        elif "-720" in i:
            quality_link["720"] = i
        elif "-1080" in i:  # aac-1080
            quality_link["1080"] = i
    if list(quality_link.keys()) == []:
        raise RuntimeError("no links found")
    return quality_link


def best_quality_link(links: dict):
    L = []
    for i in links.keys():
        if str(i).isnumeric():
            L.append(int(i))
    return str(max(L))



def save_in_txt(quality, links_list, title):
    mylinks = {}
    mylinks["download links"]=[]
    if quality == 'best':
        for links in links_list:
            mylinks["download links"].append(links[best_quality_link(links)])
        print(mylinks)
        return mylinks
    else:
        for links in links_list:
            mylinks["download links"].append(links[quality])
            print(mylinks)
            return mylinks


def choose_multiple_quality(qualities: set, links_list: list, title: str,qualtytoShose: str):
    quality = qualtytoShose
    if quality == 'best' or quality in qualities:
           return save_in_txt(quality, links_list, title)


def searchonemovie(chosen: int,title: str, movie_or_series: Type, with_proxy=False ):
    if with_proxy:
        search_result = BeautifulSoup(requests.get(cimaclub + "search", params={"s": title}, proxies=proxies).text,
                                      'html.parser')
    else:
        search_result = BeautifulSoup(requests.get(cimaclub + "search", params={"s": title}).text, 'html.parser')
    links = []
    titles = []
    for i in search_result.select('div[class*="media-block"] > div'):
        a = i.find_all('a')[-1]
        if movie_or_series == Type.movie and "series" not in a["href"] and 'season' not in a["href"]:
            links.append(a["href"])
            titles.append(a.text)
        elif movie_or_series == Type.series and 'season' in a["href"]:
            links.append(a["href"])
            titles.append(a.text)
    assert len(links) == len(titles)

    #####
    links_dict = dict()
    for i in range(len(titles)):
        links_dict[titles[i]] = links[i]
    sort_links = dict(sorted(links_dict.items(), key=lambda x: extract_season_number(x[0], with_proxy), reverse=False))
    links = list(sort_links.values())
    titles = list(sort_links.keys())

    a = links[chosen]
    if movie_or_series == Type.movie:
        a = a.replace("film", "watch")
    elif 'season' in a:
        episodes = get_episodes_links(a, with_proxy)
        chosen_episode = input(f"please choose an episode : (1-{len(episodes)}) or 'all': ")
        # case of all episodes in one season || multiple episodes
        logging.debug(f"chosen ep : {chosen_episode}--{bool(re.compile('[1-9]+-[1-9]+').match(chosen_episode))} ")
        if chosen_episode == "all" or bool(re.compile('[1-9]+-[1-9]+').match(chosen_episode)):
            return generate_list_of_links_to_download(chosen_episode, episodes)
        chosen_episode = int(chosen_episode)
        while not (0 < chosen_episode <= len(episodes)):
            print("err :::::: " + f"the chosen must be between 1 and {len(episodes)}")
            chosen_episode = int(input(f"please choose an episode : (1-{len(episodes)}) : "))
        a = episodes[chosen_episode - 1]
        if a is not None:
            a = a.replace("episode", "watch")
    return a


app = Flask(__name__)
@app.route('/searchmovie/',methods=['GET'])
def give_me_show():
    link = searchall(request.args.get('name'), Type.movie, False)
    print(link)

@app.route('/searchonemovie/',methods=['GET'])
def givethatshow():
    with_proxy=False
    title=request.args.get('name')
    link = searchonemovie(int(request.args.get('number')),title, Type.movie, with_proxy)
    if not isinstance(link, list):
        download_links = []
        qualities = []
        links = beautify_download_links(get_download_links(link, with_proxy))
        download_links.append(links)
        qualities.append(list(links.keys()))
        return choose_multiple_quality(set.intersection(*map(set, qualities)), download_links, title,"best")





if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))