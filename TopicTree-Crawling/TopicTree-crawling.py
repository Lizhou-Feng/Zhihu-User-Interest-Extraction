from selenium import webdriver
import time
import json
import os
import requests
import re
from requests.exceptions import RequestException

from pymongo.bulk import BulkOperationBuilder
from pymongo import MongoClient
import pymongo.errors as mongoerr


def ConnetDB():
    try:
        client = MongoClient('localhost:27017', connect=True)
        db = client.topicTree
        collection = db.Tree1
        return collection

    except mongoerr.ConnectionFailure as  e:
        print("Could not connect: %s" % e)
        return 1

headers = {
    'Cookie':'_zap=a113910c-f3fa-4031-b5b1-6278321aee6f; d_c0="AHBCJwuDDguPTnSS0fIbx0BB-0oNYfnMARU=|1482732437"; _xsrf=9d6c31d07a7684998746d45956c250fc; q_c1=044032362aa1407685c324e6ddb205a7|1492320457000|1492320457000; capsion_ticket="2|1:0|10:1492490097|14:capsion_ticket|44:ODg4YmVjYjEwYmQ2NGQ1NDlhOGFiM2EyOGIwYzUyOWE=|742e040301e96bf4f2c5c101189e4e8d6614b607590d6fd568ee79167f09648f"; aliyungf_tc=AQAAAFx9djV08QcAFSn3PALnNBvGx4Zd; acw_tc=AQAAAEfu3C85MQoAFSn3PPsu1k+5cNSQ; cap_id="NmQ3NzgwYmY5OTJlNDNlN2I0ZmE1OWMyYTI1ZjFhYjM=|1493632793|5c7bd30e5747dd5b070a13b42475ef15ce6aba98"; auth_type=cXFjb25u|1493632903|114a84b89d87150d942d47eb267b5b6a33c09996; atoken=30E12F9E086DAA135950FCF97254669C; atoken_expired_in=7776000; token="MzBFMTJGOUUwODZEQUExMzU5NTBGQ0Y5NzI1NDY2OUM=|1493632903|6bd50376b7cad10aca1d493b7a79e4aeceb8a10b"; client_id="NkJBQTYxNzhCNkY4MTM1REEwNTJFMzU1MjM3Mzg3N0Q=|1493632903|8aa713c05c6430bc3a1a789e9f65790eb31590c0"; s-q=%E6%A0%B9%E8%AF%9D%E9%A2%98; s-i=1; sid=ndbkh3so; s-t=autocomplete; r_cap_id="ZTZiZTc4NDVlN2YwNDYwMDk2OTUwYzdjYmY2ZjcxYWE=|1493633156|b65764f673c9ed57d9619261866533f66789257c"; l_n_c=1; __utma=51854390.1045838808.1493365582.1493611800.1493631937.5; __utmb=51854390.0.10.1493631937; __utmc=51854390; __utmz=51854390.1493381188.3.2.utmcsr=zhihu.com|utmccn=(referral)|utmcmd=referral|utmcct=/topic/20015213/hot; __utmv=51854390.100--|2=registration_date=20140821=1^3=entry_date=20140821=1; z_c0=Mi4wQUFEQTJIazFBQUFBY0VJbkM0TU9DeGNBQUFCaEFsVk5sSlV1V1FBb0l2T0pFRnJjM3dDdnNYYXRmTW83TWUtMHln|1493634270|bc70c97e4c261a1263a1da709ca592891a94a06e',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.81 Safari/537.36'
}

_session = requests.Session()
_session.headers.update(headers)


# parameters for POST request
formdata={'_xsrf':'9d6c31d07a7684998746d45956c250fc'}
urlParent = 'https://www.zhihu.com/topic/{topicID}/organize/entire'
urlLoad = 'https://www.zhihu.com/topic/19776749/organize/entire?child={thelastoneID}&parent={parentID}'
collection = ConnetDB()

def if_loadmore(response):
    pattern_if_leaf = re.compile('<h3\sclass="zm-topic-side-organize-title">(.*?)\\n</h3>', re.S)
    ifleaf = re.findall(pattern_if_leaf, response)
    # print(ifleaf)
    if '子话题' in ifleaf:
        pattern_if_loadmore = re.compile('<a\sclass="zg-link-litblue\szm-topic-side-title.*?"\shref=".*?">(.*?)</a>',
                                        re.S)
        content = re.search(pattern_if_loadmore, response)

        if ('查看完整话题结构 »' == content.group(1)):
            return 0
        else:
            return 1
    else:
        return 'leaf'

def get_parent_topic(response):
    parents=[]
    pattern_if_leaf = re.compile('<h3\sclass="zm-topic-side-organize-title">(.*?)\\n</h3>', re.S)
    ifparent = re.findall(pattern_if_leaf, response)
    #print(ifparent)
    if '父话题' not in ifparent:
        return None
    else:
         pattern1 = re.compile('<ul><li><a href=".*?">(.*?)</a>',re.S)
         pattern2 = re.compile('<a\sclass="zm-item-tag".*?"Title">\\n(.*?)\\n</a>',re.S)
         parents1 = re.findall(pattern1,response)
         parents2 = re.findall(pattern2,response)
         for p in parents1:
             if (p in parents2)&(p not in parents):
                parents.append(p)
         return parents


# get child topics
# store topics and their topic IDs in eachtopicfield
def get_childtopics(parentID, loadmore, eachtopicfield,response):
    j = response.json()  # dict type
    counter = 0  
    if (loadmore == 'leaf'):
        return
    else:
        for childtopic in j.get('msg'):  # childtopic, list type
            if counter == 1:
                for eachtopic in childtopic:
                    if (loadmore == 0):  # complete child topic
                        eachtopicfield.update({eachtopic[0][1]:  eachtopic[0][2]})
                        #eachtopicfield.append(eachtopic[0][2])
                    else:  # load child topic
                        if (eachtopic[0][1] != '加载更多'):  # the topic has already existed
                            eachtopicfield.update({eachtopic[0][1]:eachtopic[0][2]})
                             #eachtopicfield.append(eachtopic[0][2])

                        else:  # 
                            thelastoneID = eachtopic[0][2]  
                            responseLoad = _session.post(
                                urlLoad.format(parentID=parentID, thelastoneID=thelastoneID), data=formdata)
                            get_childtopics(parentID, loadmore, eachtopicfield,responseLoad)  # recursively call get_childtopics()
            counter += 1
    return

def GetAllChildTopics(parentID,loadmore):
    try:
      response = _session.post(urlParent.format(topicID=parentID), data=formdata)
      if response.status_code == 200:

          eachtopicfield={}
          get_childtopics(parentID, loadmore, eachtopicfield, response)
          return  eachtopicfield
    except RequestException:
      GetAllChildTopics(parentID,loadmore)


def parentTopic(parentID, parentName):
    try:
        response = _session.get(urlParent.format(topicID=parentID))
        if response.status_code == 200:
            print(parentName)
            loadmore = if_loadmore(response.text)
            # print(loadmore)
            Allparenttopic = GetAllChildTopics(parentID, loadmore)
            if (loadmore != 'leaf'):
                for childname in Allparenttopic.keys():
                    if(not collection.find_one({'topicID':Allparenttopic.get(childname)})):
                        parentTopic(Allparenttopic.get(childname), childname)
            node = {
                # 'layeraverage': '',
                'tag': {},
                'counter': {},
            }
            parents = get_parent_topic(response.text)
            node.update({'parents':parents,'topicID':parentID,'topicName':parentName})
            collection.update({'topicID': node.get('topicID')}, dict(node), True)
            time.sleep(7)
    except RequestException:
        parentTopic(parentID,parentName)
        #return None


def topicTree():
    rootparentID = '19776749'
    parentTopic(rootparentID, '「根话题」') ## root topic

def main():
    topicTree()
    print('the eeeeeeeeeeeeeeeend')


if __name__ == '__main__':
    main()




