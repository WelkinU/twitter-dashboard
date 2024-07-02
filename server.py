
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from typing_extensions import Annotated
from fastapi.templating import Jinja2Templates
import build_database
import flag_users
import graph_analysis

from contextlib import asynccontextmanager

from tweety import Twitter
import config
import time

#-----------------------------------
# Initialize fastapi + twitter login
#-----------------------------------

authenticated_app = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global authenticated_app

    # The code before the "yield" statement gets run on startup
    if config.MAIN_ACCOUNT_USERNAME and config.MAIN_ACCOUNT_PASSWORD:
        try:
            authenticated_app = Twitter("session")
            authenticated_app.sign_in(config.MAIN_ACCOUNT_USERNAME, config.MAIN_ACCOUNT_PASSWORD)
            print('Twitter app authenticated')
        except:
            authenticated_app = None
            print('Twitter authentication failed. Blocking / force unfollow features disabled')

    else:
        print('No main account login credentials entered. Blocking / force unfollow features disabled')

    yield
    # code after the "yield" statement gets run on shutdown after app finishes handling requests


app = FastAPI(lifespan = lifespan)
templates = Jinja2Templates(directory="templates")

#-----------------------------------
# GET request routes
#-----------------------------------

@app.get("/", response_class = HTMLResponse)
async def root(request: Request):
    df = build_database.load_database()
    return templates.TemplateResponse(
        request=request, name="database_render.html", 
        context={"df": df, 'is_auth': authenticated_app is not None}
    )

@app.get("/scrape_data", response_class = HTMLResponse)
async def scrape_data(request: Request):
    return templates.TemplateResponse(
        request=request, name="scrape_data_form.html", 
        context={"MAIN_ACCOUNT_USERNAME": config.MAIN_ACCOUNT_USERNAME}
    )

@app.get("/graph_analysis", response_class = HTMLResponse)
async def scrape_data(request: Request):

    html = graph_analysis.generate_graph_html()

    return templates.TemplateResponse(
        request=request, name="graph_analysis.html", 
        context={"html": html}
    )

@app.get("/about", response_class = HTMLResponse)
async def about(request: Request):
    html_content = """
    <html>
        <head>
            <title>About</title>
        </head>
        <body>
            <p>Some text about this thing</p>
        </body>
    </html>
    """
    return HTMLResponse(content = html_content, status_code = 200)

#-------------------------------------------------
# POST request routes - Data Scraping / Processing
#-------------------------------------------------

@app.post("/scrape_follower_profiles/")
def scrape_follower_profiles(username: Annotated[str, Form()],  pages: Annotated[int, Form()] = False):
    
    build_database.create_database(username, pages = pages)
    return {"msg": 'Done'}

@app.post("/run_flags/")
def run_flags():
    df = build_database.load_database()
    flag_ids, reasons = flag_users.get_all_flagged_users(df)
    flag_users.update_database_with_flags(df, flag_ids, reasons)

    result = f'Flagged {len(flag_ids)} users'
    print(result)
    return {"msg": result}

@app.post("/scrape_follower_followings/")
def scrape_follower_followings(pages: Annotated[int, Form()]):
    build_database.scrape_all_db_followers(pages = pages)

    return {"msg": 'Done'}

#---------------------------------------
# POST request routes - Manage Followers
#---------------------------------------

@app.post("/block/")
def block_user(username: Annotated[str, Form()]):
    print('blocking:', username)
    authenticated_app.block_user(username)
    return {"msg": 'Done'}

@app.post("/force_unfollow/")
def force_unfollow(username: Annotated[str, Form()]):
    print('force_unfollowing:', username)
    authenticated_app.block_user(username)
    time.sleep(0.2)
    authenticated_app.unblock_user(username)
    return {"msg": 'Done'}

@app.post("/set_safe/")
def set_safe(username: Annotated[str, Form()]):
    print('[NOT YET IMPLEMENTED] Setting user as safe:', username)
    return {"msg": 'Not Yet Implemented'}

#--------------------------------------
# Command line arg + uvicorn server run
#--------------------------------------

if __name__ == '__main__':
    import uvicorn
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--host', help='IP Address where the server is hosted', type=str, default='localhost')
    parser.add_argument('--port', help='Port number where the server is hosted', type=int, default='8000')
    parser.add_argument('--reload', action = 'store_true',
    	help='Set this flag so the server doesnt auto-reload when a python file changes')
    args = parser.parse_args()

    app_str = 'server:app'
    uvicorn.run(app_str, host = args.host, port = args.port, reload = args.reload)