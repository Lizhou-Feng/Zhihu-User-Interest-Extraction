# -*- coding: utf-8 -*-
from scrapy import Request,Spider
import json
import requests
import re
from requests.exceptions import RequestException
from GetUserData.items import AnswerItem,QuestionItem,Question_FollowingItem,Topic_FollowingItem

class ZhihuSpider(Spider):
    name = "userinfo"
    allowed_domains = ["www.zhihu.com"]
    start_urls = ['http://www.zhihu.com/']

    #start_user = 'feng-ling-zi'
    start_user = 'chenqin'

    #########url+parameters################
    #Answer list where the questions answered by current user will be listed.
    answersList_url = 'https://www.zhihu.com/api/v4/members/{user}/answers?include={include}offset={offset}&limit={limit}&sort_by={sort_by}'
    answersList_query = 'data[*].is_normal,suggest_edit,comment_count,collapsed_counts,reviewing_comments_count,can_comment,content,voteup_count,reshipment_settings,comment_permission,mark_infos,created_time,updated_time,relationship.is_authorized,voting,is_author,is_thanked,is_nothelp,upvoted_followees;data[*].author.badge[?(type=best_answerer)].topics'

    #Topic list where the topics followed by current user will be listed.
    topicList_url = 'https://www.zhihu.com/api/v4/members/{user}/following-topic-contributions?include={include}&offset={offset}&limit={limit}'
    topicList_query = 'data[*].topic.introduction'

    #Question list where the questions followed by current user will be listed.
    question_following_List_url = 'https://www.zhihu.com/api/v4/members/{user}/following-questions?include={include}&offset={offset}&limit={limit}'
    questionList_following_query = 'data[*].created,answer_count,follower_count,author'

    #Question list where the questions asked by current user will be listed.
    question_url='https://www.zhihu.com/api/v4/members/{user}/questions?include={include}&offset={offset}&limit={limit}'
    question_query ='data[*].created,answer_count,follower_count,author'
    ############url+parameters###############

    #Url for a specific question.
    urlParseTopic = 'https://www.zhihu.com/question/{questionID}'

    def start_requests(self):
        yield  Request(self.answersList_url.format(user = self.start_user,offset=0, limit = 20,sort_by = 'created',include = self.answersList_query),callback = self.parse_AnswersList)
        yield  Request(self.question_following_List_url.format(user = self.start_user,offset=0, limit = 20,include = self.questionList_following_query),callback = self.parse_Question_folloingList)
        yield  Request(self.question_url.format(user = self.start_user,offset=0, limit = 20,include = self.question_query),callback = self.parse_QuestionList)
        yield  Request(self.topicList_url.format(user = self.start_user,offset=0, limit = 20,include = self.topicList_query),callback = self.parse_Topic_folloingList)

    def parse_AnswersList(self,response):
        results = json.loads(response.text)
        item = AnswerItem()
        if 'data' in results.keys():
            for result in results.get('data'):
                topics = {}
                questionid = result.get('question').get('id')
                html = self.get_oneQtopic(self.urlParseTopic.format(questionID = questionid))
                if(html):
                    self.parse_oneQtopic(html,topics)
                    item['title'] = result.get('question').get('title')
                    item['type'] = 'Answer'
                    item['topicList'] = topics
                    item['origin'] = 1

                    yield item   
        # process the next page
        if 'paging' in results.keys() and results.get('paging').get('is_end') == False:
            next_page = results.get('paging').get('next')
            yield Request(next_page,
                              self.parse_AnswersList)

    def parse_Topic_folloingList(self, response):
        results = json.loads(response.text)
        item = Topic_FollowingItem()
        if 'data' in results.keys():
            for result in results.get('data'):
                    item['type'] = 'Topic'
                    item['topicList'] = {result.get('topic').get('name'):result.get('topic').get('id')}
                    item['origin'] = 1
                    yield item
        # process the next page
        if 'paging' in results.keys() and results.get('paging').get('is_end') == False:
            next_page = results.get('paging').get('next')
            yield Request(next_page,
                          self.parse_Topic_folloingList)

    def parse_QuestionList(self, response):
        results = json.loads(response.text)
        item = QuestionItem()
        if 'data' in results.keys():
            for result in results.get('data'):
                topics = {}
                questionid = result.get('id')
                html = self.get_oneQtopic(self.urlParseTopic.format(questionID=questionid))
                if (html):
                    self.parse_oneQtopic(html, topics)
                    item['title'] = result.get('title')
                    item['type'] = 'Question'
                    item['topicList'] = topics
                    item['origin'] = 1

                    yield item
        # process the next page
        if 'paging' in results.keys() and results.get('paging').get('is_end') == False:
            next_page = results.get('paging').get('next')
            yield Request(next_page,
                          self.parse_QuestionList)

    def parse_Question_folloingList(self, response):
        results = json.loads(response.text)
        item = Question_FollowingItem()
        if 'data' in results.keys():
            for result in results.get('data'):
                topics = {}
                questionid = result.get('id')
                html = self.get_oneQtopic(self.urlParseTopic.format(questionID=questionid))
                if (html):
                    self.parse_oneQtopic(html, topics)
                    item['title'] = result.get('title')
                    item['type'] = 'QF'
                    item['topicList'] = topics
                    item['origin'] = 1

                    yield item
        # process the next page
        if 'paging' in results.keys() and results.get('paging').get('is_end') == False:
            next_page = results.get('paging').get('next')
            yield Request(next_page,
                          self.parse_Question_folloingList)


    # Request a html page of a specific question for getting the topics of the question.
    def get_oneQtopic(self,url):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.81 Safari/537.36'}
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response.text
            return None
        except RequestException:
            return None

    # Get the topicNames and topicIDs of a specific question
    def parse_oneQtopic(self,html,topicList):
        pattern = re.compile('<a class="TopicLink".*?(\d+)">.*?<div id.*?content">(.*?)</div>',re.S)
        #pattern = re.compile('<a class="TopicLink".*?">.*?<div id.*?content">(.*?)</div>',re.S)
        topics = re.findall(pattern, html)

        for topic in topics:
            topicList.update({topic[1]:topic[0]})
            #topicName.append(topic)
        # else:
        #     self.parse_oneQtopic(html,topicList)






