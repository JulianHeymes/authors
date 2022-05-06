import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates

def fetch_from_psi():
    #dict containing the names the we need to replace with
    #shorter or slightly different variants
    to_fix = {'Lars Erik Fröjd':'Erik Fröjdh',
    'Maria del Mar Carulla Areste': 'Maria Carulla',
    'Julian Brice Dominique Heymes':'Julian Heymes' }

    url = 'https://www.psi.ch/en/lxn/team'
    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")

    id_tags = ['collapsible-item', 'collapsible-item--2']
    names = []
    for id_tag in id_tags:
        results = soup.find(id = id_tag)
        groups  = results.find_all("div", class_='psi-summary-media-wrapper')
        for item in groups:
            res = item.find("strong", class_="content-item__title heading")
            name = res.getText().strip('\n')
            name = name.replace('Dr. ', '')
            if name in to_fix:
                name = to_fix[name]
            names.append(name)

    names.sort(key=lambda s : s.split(maxsplit=1)[1].casefold())
    return names

def tex_jinst(names):
    #assume that the first author is corresponding author
    names = [tex_replace_umlaut(name) for name in names]
    names_iter = iter(names)

    first = f'\\author[a,1]{{{next(names_iter)}\\note{{Corresponding author.}}}} '
    rest = ' '.join(f'\\author[a]{{{name}}}' for name in names_iter)
    return first+rest

def tex_replace_umlaut(name):
    name = name.replace('å', '\\aa ')
    name = name.replace('ö', '\\"o')
    name = name.replace('ä', '\\"a')
    name = name.replace('ü', '\\"u')
    return name

def get_names(lastname = None):
    result = {}
    names = fetch_from_psi()
    if lastname:
        lastname = lastname.casefold()
        print(lastname)
        for i, name in enumerate(names):
            
            if lastname in name.partition(' ')[2].casefold():
                names.insert(0, names.pop(i))
                break

    result['full'] = ', '.join(names)
    result['n_members'] = len(names)
    

    short = []
    for name in names:
        first, _ = name.split(maxsplit=1)
        short.append(name.replace(first, f'{name[0]}.'))
    result['short'] = ', '.join(short)

    result['jinst_full'] = tex_jinst(names)
    result['jinst_short'] = tex_jinst(short)

    return result




templates = Jinja2Templates(directory="templates/")
app = FastAPI()
@app.get("/")
async def read_root(request: Request):
    result = get_names()
    return  templates.TemplateResponse("main.html", context={"request": request, "result": result})

@app.get("/author/{lastname}")
async def read_author(request: Request, lastname):
    result = get_names(lastname)
    return  templates.TemplateResponse("main.html", context={"request": request, "result": result})

