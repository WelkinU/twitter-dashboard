#--------------------------------------------------------------------------------
# ENTER LOGIN CREDENTIALS HERE
#--------------------------------------------------------------------------------

# Scraping account will only be used to scrape data.
# Strongly recommended to use a different account than main account in case Twitter bans you!
SCRAPING_ACCOUNT_USERNAME = 'YOUR_SCRAPING ACCOUNT_USERNAME'
SCRAPING_ACCOUNT_PASSWORD = 'YOUR_SCRAPING_ACCOUNT_PASSWORD'

# Main account will only be used to handle the block / unblocking functions and won't be used for scraping data.
MAIN_ACCOUNT_USERNAME = ''
MAIN_ACCOUNT_PASSWORD = ''



#--------------------------------------------------------------------------------
# PARAMS FOR FLAGGING USERS
#--------------------------------------------------------------------------------

# capitalization doesn't matter
TEXT_TO_FLAG = ['whatsapp', r'% return', 'he/him', 'they/them', 'she/her']

# see full list of emoji for python emoji library: https://carpedm20.github.io/emoji/
# capitalization matters here
EMOJI_TO_FLAG = [
    ':Ukraine:',':rainbow:',':rainbow_flag:',':pregnant_man',':transgender_'
]

# people with followers less than this amount will get flagged
# generally this is used to find people that follow only you
# set this to -1 to disable
LOW_FOLLOWER_THRESH = 3 

# followers gained per day theshold, set this to a large number to disable
FOLLOWERS_PER_DAY_THRESH = 10

# For detecting randomly generated usernames, set to False to disable
ALPHANUMERIC_CHECK_ENABLED = True
NGRAM_CHECK_ENABLED = True



#--------------------------------------------------------------------------------
# DON'T CHANGE STUFF BELOW HERE - this is just to clean up user input
#--------------------------------------------------------------------------------

TEXT_TO_FLAG = [x.lower() for x in TEXT_TO_FLAG] #make sure our text is lowercase