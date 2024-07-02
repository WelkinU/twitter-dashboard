# twitter-dashboard

This project tries to make it easy to review, analyze and remove large groups of followers on Twitter/X. Inspired by @calvinfroedge goal of purging bots from his followers.

The functionalities implemented are:
- Scrape the profile data of all followers of a designated account (such as your own account)
- Flag users with a wide variety of filters
- Provide a UI dashboard that shows all relevant follower info in a table. Flagged users highlighted in red. 1 click to block a user or force them to unfollow you.
- Provide a mechanism for creating and organizing users in a network graph plot

**Note:** Since Elon took over, many API endpoints have been removed and a lot of data scraping projects are broken and unmaintained. This project is currently using [Tweety](https://github.com/mahrtayyab/tweety) to scrape data - it's a key dependancy and it's always a risk that the API changes again and breaks Tweety's scraping code.

## Python Environment Setup

This project requires Python >= 3.8. Install needed libraries with `pip install -r requirements.txt`

## Usage

1. It's strongly recommended to make a seperate account for scraping user data! Twitter/X has a lot of rate limits now and abuse can lead to action being taken against the account that's scraping data. See Tweety FAQ for more info: [https://github.com/mahrtayyab/tweety/wiki/FAQs#twitter-new-limits](https://github.com/mahrtayyab/tweety/wiki/FAQs#twitter-new-limits) 

1. Configure login info and settings in `config.py`
    - Set `SCRAPING_ACCOUNT_USERNAME` and `SCRAPING_ACCOUNT_PASSWORD` to the username and password of account you're using for scraping data. 
    - [OPTIONAL] For blocking or forcing users to unfollow you, set `MAIN_ACCOUNT_USERNAME` and `MAIN_ACCOUNT_PASSWORD` to the appropriate values. This will only be used later in the UI for blocking and forcing users to unfollow you. The main account will not for scraping data.
    - Set `TEXT_TO_FLAG` to any text you would like to flag in a user's name or bio.
    - Set `EMOJI_TO_FLAG` to any emojis you would like to flag in a user's name or bio. See [https://carpedm20.github.io/emoji](https://carpedm20.github.io/emoji) for the short-text of each emoji. Capitalization matters here.

1. Open web UI
    - In the command line: run `python server.py`
    - In your web browser, navigate to `localhost:8000/scrape_data`

1. Scrape user data
    - In the "Get Follower Profiles" section, enter an @username that you want to scrape follower profiles.
    - Enter the number of pages of followers you want to get. It's about 50-60 users per page
    - Click submit. It should take a few seconds per page (don't want to run afoul of new rate limits).
    - When this finishes running, you should see a `db.csv` file created in the repository root folder. This contains the scraped data.

1. Flag users
    - In the `localhost:8000/scrape_data` endpoint, see the "Flag Users" section. Click submit, and it will use the flags configured in `config.py` and identify users matching those criteria.

1. Review / Remove Followers
    - In your web browser, navigate to `localhost:8000`. You should see a large table showing the scraped data in a more human viewable form. It might take a few seconds for images to all load. Flagged users will appear in red, with a column explaining the reasons the user is flagged.
    - If `MAIN_ACCOUNT_USERNAME` and `MAIN_ACCOUNT_PASSWORD` are set in `config.py` you will have the "Block" and "Force Unfollow" buttons available.
    - "Whitelist User" button is not yet implemented

## View Network Graph

1. Scrape follower relationships for the users scraped above
    - In the web browser page `localhost:8000/scrape_data`, see the section "Scrape User Followings for Making Network Graphs".
    - For each scraped user, we will scrape the list of who they follow. Enter the number of pages of their followings list to scrape (50-60 users per page).
    - Click submit to start scraping
    - The runtime of this operation is VERY LONG. Depending on how many users you're grabbing data for, this can take hours (rate limits...). Monitor progress in the command prompt.

1. When data scraping is complete, open the `localhost:8000/graph_analysis` endpoint. After a few seconds, the network graph should appear. Use the mouse to pan / zoom the plot. If you have a lot of users plotted, it might be a little laggy.

## Algorithm

### 1. Scrape follower data using [Tweety](https://github.com/mahrtayyab/tweety)

1. Scrape data with Tweety
1. Save data to csv "database"

### 2. Flag users

Flag users on a variety of metrics

Implemented:
- User isn't following enough other users: Implies user created account just to follow you!
- Flag certain text / emojis that you define
- Flag users that got followers too fast, indicating they're part of a botnet. There are a lot of users created last week that already have hundreds of followers - not legit!
- Flag users that were created very recently. Statistically unlikely a real person follows your immediately after creating their account.
- Flag randomly generated usernames. This will have a higher false positve rate than other schemes
    - Naive algorithm to check if the username seems to be random alphanumeric
    - N-Gram frequency analysis to determine if the username seems "human readable". This can fail on non-english users

TODO:
- Graph clustering based flagging
- Vision based method for flagging certain types of content such as the fake women bot accounts. A few neural network options for this - the new multimodal LLM models, CLIP. Don't want a pretrained dedicated neural network because it won't be as flexible when you want to detect something different.

### 3. Provide UI to review/remove followers

Implemented:
- Basic FastAPI webapp to handle the follower review/removal
- Add a UI frontend for the command line stuff for scraping/flagging, to make more user friendly
- Weighted graph generation + interactive visualization

TODO:
- Pagination for very large dashboard tables
- Community detection via modularity based graph clustering algorithm such as Leiden method


## Other Ideas

- Dashboard UI adds
    - AI text summary of a user's recent posts
    - AI text summary of the descriptions of all of a user's followers
    - Use the text summary + text embedding vector to get another way of clustering users

- Graph analysis
    - Use geolocation of followers to determine best location for a meetup - suggested way back by @Balajis
    - Graph analysis "score" of a user - maybe eccentricity is good enough?
    - AI text summary of a community of users, for a more automated community classification?

- Imposter detection - everyone knows about the social media imposters, but now we can flag those too. Look for:
    - Duplicate name and description with simple text equality
    - Similar @username - Usually the edit distance between imposter and real account is 1 or 2.
    - Validate similar profile picture. Can easily check if same image. Image similarity metric such as SSIM or Wavelet SSIM will flag craftier imposters who slightly alter the image.

- Text based image search of a group of user's profile/banner images. Implement using OpenAI CLIP + vector database. Lets you type in a query and do a vision based search for specific types of image content.

