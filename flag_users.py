
import pandas as pd
import datetime
import re

import emoji                 #for handling emoji text
from nostril import nonsense #pip install git+https://github.com/casics/nostril.git

from build_database import load_database, DB_CSV_PATH, CSV_DELIMITER, DB_TIMESTAMP_FILE
import config

try:
    with open(DB_TIMESTAMP_FILE, 'r') as file:
        DB_TIMESTAMP = datetime.datetime.strptime(file.read(), '%Y-%m-%d %H:%M:%S.%f')
except:
    DB_TIMESTAMP = datetime.datetime.now()

def get_all_flagged_users(df):
    flag_ids = []
    flag_reasons = []

    # ADD WHICH FUNCTIONS TO USE AS FLAGS HERE
    # Flag functions must return flag (boolean), reason (string or list of string) 
    FLAGGING_FUNCTIONS = [
        flag_too_few_followers,
        flag_text_or_emoji,
        flag_randomly_generated_username,
        flag_got_followers_too_fast,
    ]

    for row in df.itertuples():
        is_flagged, reasons = False, []

        # GREEN FLAGS
        if row.verified == True:
            continue

        # RED FLAGS
        for flag_func in FLAGGING_FUNCTIONS:
            flagged, flag_reason = flag_func(row)

            if flagged:
                is_flagged = True
                if isinstance(flag_reason, str):
                    reasons.append(flag_reason)
                elif isinstance(flag_reason, list):
                    reasons.extend(flag_reason)

        if is_flagged:
            flag_ids.append(row.Index)
            flag_reasons.append(', '.join(reasons))

    return flag_ids, flag_reasons

def update_database_with_flags(df, flag_ids, reasons):
    df.loc[:,['flags']] = 'no_flag'
    df.loc[flag_ids, ['flags']] = reasons

    df.to_csv(DB_CSV_PATH, sep = CSV_DELIMITER, index = False)

#-----------------------
# Flagging functions
#-----------------------
def flag_too_few_followers(row):
    flagged, reason = False, ''

    if row.friends_count < config.LOW_FOLLOWER_THRESH:
        return True, "low_follower_count"
    else:
        return False, ''

def flag_text_or_emoji(row):
    flagged, reasons = False, []

    # clean up input, make sure it's in str format
    name, description = row.name, row.description
    if not isinstance(name, str):
        name = str(name)
    if not isinstance(description, str):
        description = str(description)

    total_text = name+description

    # check for text to flag
    total_text_lower = total_text.lower()
    for text in config.TEXT_TO_FLAG:
        if text in total_text_lower:
            flagged = True
            reasons.append(f'flagged_text --- {text}')

    # check for emojis to flag
    # would be a bit faster to use emoji.analyze(total_text)
    # a bit more complicated code though because of emoji with duplicate code (ie. :airplane::airplane:)
    total_text_demojized = emoji.demojize(total_text)
    for emo in config.EMOJI_TO_FLAG:
        if emo in total_text_demojized:
            flagged = True
            reasons.append(f'flagged_emoji --- {emo}')

    return flagged, reasons

def flag_randomly_generated_username(row):
    flagged, reason = False, ''

    if config.ALPHANUMERIC_CHECK_ENABLED:
        # my paltry attempt at randomly generated alphanumeric string detection
        all_numbers = re.findall(r'\d+', row.username)
        num_digits = sum(len(x) for x in all_numbers)
        if len(all_numbers) >= 3 or num_digits > 6 or (num_digits >= 0.6 * len(row.username) and num_digits > 4):
            flagged = True
            reason = 'randomly_generated_@username_detected - alphanumeric method'
            return flagged, reason

    if config.NGRAM_CHECK_ENABLED:
        try:
            if nonsense(row.username):
                flagged = True
                reason = 'randomly_generated_@username_detected - ngram method'
        except:
            pass

        return flagged, reason

def flag_got_followers_too_fast(row):
    flagged, reason = False, ''

    created_datetime = datetime.datetime.strptime(row.created_at[:19],'%Y-%m-%d %H:%M:%S')
    delta = DB_TIMESTAMP- created_datetime
    delta_days = delta.days + 1E-3

    followers_per_day = row.followers_count / delta_days

    if followers_per_day >= config.FOLLOWERS_PER_DAY_THRESH and 10 <= row.followers_count < 5000:
        flagged = True
        reason = f'gained_followers_too_fast: {row.followers_count} followers in {int(delta_days)} days'
        return flagged, reason

    if delta_days < 3: #TODO: check for following you right after created
        flagged = True
        reason = f'recently_created: Created {int(delta_days)} days ago.'

    return flagged, reason

if __name__ == '__main__':
    pd.options.display.width = 0 #So Pandas autodetects the size of your terminal window
    df = load_database()

    flag_ids, reasons = get_all_flagged_users(df)
    
    for flag_id, reason in zip(flag_ids, reasons):
        print(flag_id, reason)

    update_database_with_flags(df, flag_ids, reasons)
