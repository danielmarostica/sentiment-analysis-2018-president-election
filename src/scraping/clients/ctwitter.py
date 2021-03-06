import time
import hashlib
from selenium import webdriver
from utils import get_profile


class TwitterClient:

    def __init__(self, np_posts=5, np_comments=10):
        self.np_posts = np_posts
        self.np_comments = np_comments
        self.results = {
            'network': 'twitter',
            'data': []
        }

    def start(self, name):
        driver = webdriver.Firefox(firefox_profile=get_profile())
        driver.get(f"https://twitter.com/{name.uuid}")

        for _ in range(self.np_posts):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1)

        data = {
            'name': name.name,
            'feed': []
        }

        feeds = []
        posts = driver.find_elements_by_xpath('//*[@id="stream-items-id"]/li/div')
        for post in posts:
            link = post.get_attribute('data-permalink-path')
            if link:
                feeds.append('https://twitter.com%s' % link)

        for feed in feeds:
            feed_data = {
                'feed_views_retweets': 0,
                'feed_views_likes': 0,
                'comments': []
            }

            driver.get(feed)

            try:
                retweets = driver.find_element_by_class_name('request-retweeted-popup').text
                feed_data['feed_views_retweets'] = int(retweets.replace('Retweets', '').replace(',', '').replace('.', ''))
                likes = driver.find_element_by_class_name('request-favorited-popup').text
                feed_data['feed_views_likes'] = int(likes.replace('Likes', '').replace(',', '').replace('.', ''))
            except Exception as e:
                print(f'ERROR: likes element not found : {e}')

            i = 1
            for _ in range(self.np_comments):
                m = i * 2000
                driver.execute_script(f"document.getElementById('permalink-overlay').scrollTo(0, {m})")
                time.sleep(1)
                i += 1

            replies = driver.find_elements_by_class_name('ThreadedConversation-moreRepliesLink')
            for reply in replies:
                try:
                    reply.click()
                except Exception as e:
                    print(f'ERROR: ThreadedConversation-moreRepliesLink element not found : {e}')
                time.sleep(.5)

            replies_feed = driver.find_element_by_class_name('replies-to')
            if replies_feed:
                user_posts = replies_feed.find_elements_by_class_name('content')
                for upost in user_posts:
                    try:
                        username = upost.find_element_by_class_name('username')
                        comment = upost.find_element_by_class_name('tweet-text')
                        dt = upost.find_element_by_class_name('_timestamp')

                        if username and comment:
                            username = username.text.strip()
                            comment = comment.text.strip()
                            tm = int(dt.get_attribute('data-time'))

                            feed_data['comments'].append({
                                'hash': hashlib.sha256((username + '|' + comment).encode('ascii', 'ignore')).hexdigest(),
                                'username': username,
                                'data': time.strftime("%d/%m/%Y %H:%M", time.localtime(tm)),
                                'timestamp': tm,
                                'comment': comment
                            })
                    except Exception as e:
                        print(f'ERROR: username or comment not found : {e}')
            data['feed'].append(feed_data)

        self.results['data'].append(data)
        driver.close()