from lemmy import Lemmy
from screenshotLemmy import screenshotLemmy
from createLemmyVideo import createLemmyVideo
from createTTS import createTTS
from finalCleanup import cleanup
from json import loads as json_loads
from random import choice as rchoice
from typing import Dict
from loguru import logger


with open("config.json", "r") as f:
    config = json_loads(f.read())

# configure these in the config.json file!
INSTANCE_URL = config["INSTANCE_URL"] # e.g. https://lemmy.world
LEMMY_USERNAME = config["LEMMY_USERNAME"]
LEMMY_PASSWORD = config["LEMMY_PASSWORD"]
LEMMY_TARGET_COMMUNITY = config["LEMMY_TARGET_COMMUNITY"]
COMMENT_LIMIT = config["COMMENT_LIMIT"] # max. 50
COMMENT_CHARACTER_LIMIT = config["COMMENT_CHARACTER_LIMIT"]
POST_SORT_TYPE = config["POST_SORT_TYPE"]
COMMENT_SORT_TYPE = config["COMMENT_SORT_TYPE"]
PREFERRED_BROWSER = config["PREFERRED_BROWSER"] # firefox, chrome, edge, safari

lemmy = Lemmy(INSTANCE_URL)

# login to lemmy
if lemmy.log_in(LEMMY_USERNAME, LEMMY_PASSWORD):
    logger.success(f"Successfully logged in as {LEMMY_USERNAME} to the {INSTANCE_URL} Lemmy instance.")
else:
    logger.error(f"Could not log in as {LEMMY_USERNAME} to the {INSTANCE_URL} Lemmy instance.")
    exit()
jwt = lemmy._auth.token

def getRandomPostID() -> str:
    data = lemmy.post.list(community_id=community_id, sort=POST_SORT_TYPE)
    logger.info("Getting a random post ID")
    post_ids = list()
    for post_data in data["posts"]:
        post_id = post_data["post"]["id"]
        post_ids.append(post_id)
    logger.success("Successfully got a random post ID")
    return rchoice(post_ids)

def getTopCommentData(post_id: str) -> Dict[str, str]:
    logger.info("Getting TOP comment IDs")
    comment_datas = dict()
    try:
        post_comments = lemmy.comment.list(post_id=post_id, sort="Top", limit=50 if COMMENT_LIMIT > 50 else COMMENT_LIMIT)
    except Exception as e:
        logger.error(f"An error occurred while getting the data of TOP comments\n{e.__class__.__name__}: {e}")
        exit()
    for data in post_comments["comments"]:
        if len(data["comment"]["content"]) > COMMENT_CHARACTER_LIMIT:
            continue
        else:
            comment_content = data["comment"]["content"]
        comment_id = data["comment"]["id"]
        comment_datas[comment_id] = comment_content
    if not comment_datas:
        logger.error("Could not get top comment datas; the comment_datas hashmap is empty")
        exit()
    logger.success("Successfully got TOP comment IDs")
    return comment_datas

logger.info(f"Discovering community: {LEMMY_TARGET_COMMUNITY}")
community_id = lemmy.discover_community(LEMMY_TARGET_COMMUNITY)
logger.info("Getting Lemmy posts from community")
random_post_id = getRandomPostID()
top_comment_data = getTopCommentData(random_post_id)
post_name = lemmy.post.get(id=random_post_id)["post_view"]["post"]["name"]

logger.info("Cleaning up beforehand")
cleanup()
logger.info("Preparing to take screenshots")
screenshotLemmy(INSTANCE_URL, random_post_id, top_comment_data.keys(), jwt, PREFERRED_BROWSER)
logger.info("Preparing to generate TTS files")
createTTS(top_comment_data, post_name)
logger.info("Preparing to create the video. This might take several minutes")
createLemmyVideo(random_post_id)
logger.success("All operations succeeded. Preparing to cleanup")
cleanup()
logger.success("Cleaning up done. You may now exit the program")
