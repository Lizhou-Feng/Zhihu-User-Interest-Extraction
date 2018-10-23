# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy import Item, Field

class AnswerItem(Item):
    origin = Field()
    type = Field()
    title = Field()
    topicList = Field()

class QuestionItem(Item):
    type = Field()
    title = Field()
    topicList = Field()
    origin = Field()
class Question_FollowingItem(Item):
    type = Field()
    title = Field()
    topicList = Field()
    origin = Field()
class Topic_FollowingItem(Item): 
    type = Field()
    topicList = Field()
    origin = Field()
