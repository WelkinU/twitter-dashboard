
from tweety import Twitter #pip install tweety-ns     #https://github.com/mahrtayyab/tweety
import config
import emoji
import pandas as pd
import os
from tqdm import tqdm
import time
import datetime

# Database Parameters
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
os.makedirs(DATA_DIR, exist_ok = True)
DB_CSV_PATH = os.path.join(DATA_DIR, 'db.csv')
CSV_DELIMITER = ';'    #choose a rare character for people to put on twitter
DB_TIMESTAMP_FILE = os.path.join(DATA_DIR, "db_generated_timestamp.txt")
DB_FOLLOWINGS_PATH = os.path.join(DATA_DIR, 'followings.csv')

def create_database(username: str, pages = 1, authenticated_app = None):
    ''' Given a username, scrape user profiles of every account that follows that username. Save to database.'''

    if authenticated_app is None:
        authenticated_app = Twitter("session")
        try:
            authenticated_app.connect() #use previous session
            print('Logging in using previous session.')
        except:
            #login with new session
            authenticated_app.sign_in(config.SCRAPING_ACCOUNT_USERNAME, config.SCRAPING_ACCOUNT_PASSWORD)
            print('Logging in using saved username / password.')

    users = authenticated_app.get_user_followers(username, pages = pages)
    df = list_of_users_to_dataframe(users)

    df.to_csv(DB_CSV_PATH, index = False, sep=CSV_DELIMITER)

    with open(DB_TIMESTAMP_FILE, 'w') as file:
        file.write(f'{datetime.datetime.now()}')

def load_database(**kwargs):
    ''' Load from the database created in create_database() function.
    Keyword args passed to this function will be passed to Panda's read_csv function.
    usecols or nrows for example '''
    df = pd.read_csv(DB_CSV_PATH, sep = CSV_DELIMITER, **kwargs)
    return df

def scrape_all_db_followers(authenticated_app = None, pages:int = 10, delay_sec_for_rate_limit: int = 45):
    ''' For user in the database from create_database() scrape which accounts they follow. Save results to second database.

    authenticated_app {tweety session} -- Pass in an authenticated Tweety session object here. 
                                        Default value creates new session object.
    pages {int}  -- Number of pages of followers to get for each user. 1 page is approximately 50-60 user acounts
    delay_for_rate_limit {int} -- Number of seconds between each call to get_user_followings(). 
                                Per docs, every method has rate limit as low as 50 requests per 15 minutes.
                                https://github.com/mahrtayyab/tweety/wiki/FAQs#twitter-new-limits
    '''
    
    if authenticated_app is None:
        authenticated_app = Twitter("session")
        try:
            authenticated_app.connect() #use previous session
            print('Logging in using previous session.')
        except:
            #login with new session
            authenticated_app.sign_in(config.SCRAPING_ACCOUNT_USERNAME, config.SCRAPING_ACCOUNT_PASSWORD)
            print('Logging in using saved username / password.')

    df = load_database()

    if 'followings' not in df.columns:
        df['followings'] = '[]'

    df_list = []

    error_count, error_limit = 0, 5

    with tqdm(total=len(df)) as pbar:

        for row in df.itertuples():

            #update progressbar
            pbar.update(row.Index)
            pbar.set_description(f"Scraping follower data for user {row.Index}/{len(df)}: @{row.username}")

            if row.protected == True: #can't scrape followers for protected users
                continue

            try:
                users = authenticated_app.get_user_followings(row.username, pages = pages, wait_time = 2)
            except Exception as e:
                #if we can't fetch data, try next user. If we failed too many times, stop fetching and save data.
                error_count += 1
                if error_count >= error_limit:
                    print(f'Error limit exceeded, saving data and exiting. Error fetching user data for @{row.username} Error: {e}')
                    break
                else:
                    print(f'Error fetching user data for @{row.username} -- continuing to next user. Error: {e}')
                    continue

            follower_attributes = [
                'username', 'id', 'description', 'location','statuses_count', 
                'followers_count', 'friends_count', 'protected','verified']

            df_user = list_of_users_to_dataframe(users, user_attributes = follower_attributes)
            df_user['followed_by_username'] = row.username

            df.loc[row.Index,['followings']] = str(list(df_user['username']))

            df_list.append(df_user)

            time.sleep(delay_sec_for_rate_limit)


    #save follower connections into db
    df.to_csv(DB_CSV_PATH, index = False, sep=CSV_DELIMITER)

    #save all followings to CSV "database" - this is just for reference right now
    followings_df = pd.concat(df_list, ignore_index = True)
    followings_df.to_csv(DB_FOLLOWINGS_PATH, index = False, sep=CSV_DELIMITER)

#------------------------------------
# Helper functions
#------------------------------------

def list_of_users_to_dataframe(users, user_attributes = None, replace_emojis = False):

    if user_attributes is None:
        user_attributes = [
            'username', 'name', 'id', 'created_at', 'description', 'location',
            'followed_by','following', 
            'statuses_count', 'followers_count', 'friends_count','subscriptions_count',
            'profile_banner_url','profile_image_url_https',
            'favourites_count', 'protected','verified'
            ]

    db_buffer = {attribute:[] for attribute in user_attributes}

    for user in users:
        try:
            for attribute in user_attributes:
                val = user.__getattribute__(attribute)
                
                #remove commas from any strings for CSV - we don't need this if we're using a real database
                if isinstance(val, str):
                    val = val.replace(CSV_DELIMITER,' ')

                    if replace_emojis: # emoji ---> emoji short-text
                        val = emoji.demojize(val)
                        #val = val.encode('unicode-escape') # emoji ---> \U181237347 (unicode escape)
                
                if val is not None and attribute == 'description':
                    if not isinstance(val, str):
                        val = str(val)
                    val = val.replace('\n', ' ').replace('\r', ' ')

                db_buffer[attribute].append(val)

        except Exception as e:
            print(str(e))

    df = pd.DataFrame(db_buffer)
    df['flags'] = '' #add empty column "flags"

    return df

if __name__ == "__main__":
    scrape_all_db_followers()

    quit()

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--user', type=str, default=config.MAIN_ACCOUNT_USERNAME,
        help='The @username of the account you want to scrape all follower data for. Default config.MAIN_ACCOUNT_USERNAME')
    parser.add_argument('-p','--pages', type=int, default=10,
        help='Number of pages of followers to load. About 50-60 users per page')
    args = parser.parse_args()

    create_database(args.user, pages = args.pages) #ex. create_database('elonmusk', pages = 5)

    #df = load_database(usecols = ['username', 'name', 'id', 'location'])
    #pd.options.display.width = 0 #So Pandas autodetects the size of your terminal window
    #print(df.head())