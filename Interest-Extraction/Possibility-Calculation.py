from pymongo import MongoClient
import pymongo.errors as mongoerr
import jieba.posseg as pseg
import re
from requests.exceptions import RequestException
import requests

headers = {
'Cookie':'_zap=a113910c-f3fa-4031-b5b1-6278321aee6f; d_c0="AHBCJwuDDguPTnSS0fIbx0BB-0oNYfnMARU=|1482732437"; _xsrf=9d6c31d07a7684998746d45956c250fc; capsion_ticket="2|1:0|10:1492490097|14:capsion_ticket|44:ODg4YmVjYjEwYmQ2NGQ1NDlhOGFiM2EyOGIwYzUyOWE=|742e040301e96bf4f2c5c101189e4e8d6614b607590d6fd568ee79167f09648f"; auth_type=cXFjb25u|1493632903|114a84b89d87150d942d47eb267b5b6a33c09996; token="MzBFMTJGOUUwODZEQUExMzU5NTBGQ0Y5NzI1NDY2OUM=|1493632903|6bd50376b7cad10aca1d493b7a79e4aeceb8a10b"; client_id="NkJBQTYxNzhCNkY4MTM1REEwNTJFMzU1MjM3Mzg3N0Q=|1493632903|8aa713c05c6430bc3a1a789e9f65790eb31590c0"; aliyungf_tc=AQAAAPB+g0WpTwMAFSn3PFr22hZRyxQP; acw_tc=AQAAAOgELzZTdAUAFSn3PEyu4w6z9lX3; s-q=%E7%9F%A5%E4%B9%8E%E8%AF%9D%E9%A2%98; s-i=6; sid=thaeadsg; q_c1=6d192f99b3ca43f6bb410d9841212cd5|1493870707000|1493870707000; r_cap_id="YzY1MTQxYjY5MzZlNDdjOTg4N2M2YzI4OTk4NWJiNWU=|1493870707|9d6d80f9d017edf475547f866fe6cbfef2cdeae5"; cap_id="Nzc0NDVhNGUwYmY2NGQwZWJhYmFjMTdhODE1ZGQxY2I=|1493870707|7bebbea02a9a9d7a2fbe4a61091207eb021eb43c"; __utma=51854390.1045838808.1493365582.1493857889.1493870725.19; __utmb=51854390.0.10.1493870725; __utmc=51854390; __utmz=51854390.1493870725.19.13.utmcsr=zhihu.com|utmccn=(referral)|utmcmd=referral|utmcct=/people/zhang-zi-shi/followers; __utmv=51854390.000--|2=registration_date=20140821=1^3=entry_date=20170504=1; l_n_c=1; z_c0=Mi4wQUFEQTJIazFBQUFBY0VJbkM0TU9DeGNBQUFCaEFsVk55VFV5V1FBc0R2eEplQmZHeDRydzJoXzBmQUh0V1pOVENB|1493870793|be32926b15d625119250515218c917dbf3483427',
'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.81 Safari/537.36'
}

urlParent = 'https://www.zhihu.com/topic/{topicID}/organize/entire'

_session = requests.Session()
_session.headers.update(headers)

def ConnetDB():
    try:
        # client = MongoClient('localhost:27017', connect=True)
        # db = client.zhihu
        # collection = db.users
        client = MongoClient('localhost:27017', connect=True)
        dbTopicTree = client.topicTree
        Tree = dbTopicTree.Tree1
        test = dbTopicTree.test
        dbUser = client.UserData
        UserData = dbUser.chenqin
        #UserData 数据库的名字
        #chenqin 用户名
        # print(collection.find_one())
        return Tree,UserData,test

    except mongoerr.ConnectionFailure as  e:
        print("Could not connect: %s" % e)
        return 1

Tree,UserData ,test= ConnetDB()

##Update TopicTree
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
def update_TopicTree(TopicName,TopicID):
   if(not Tree.find_one({'topicID':TopicID})):
       try:
           response = _session.get(urlParent.format(topicID=TopicID))
           if response.status_code == 200:
               node = {
                   # 'layeraverage': '',
                   'tag': {},
                   'counter': {},
               }
               parents = get_parent_topic(response.text)
               node.update({'parents': parents, 'topicID': TopicID, 'topicName': TopicName})
               Tree.update({'topicID': node.get('topicID')}, dict(node), True)
               print('update new topic:',TopicName)
       except RequestException:
           update_TopicTree(TopicName, TopicID)

def main():

   #types = ['Answer','Question','QF','Topic']
   typs = ['Answer','Question','QF']
   # updating TopicTree
   # for type in types:
   #     xs=UserData.find({'type':type},{'title':True,'topicList':True,'_id':False})
   #     for x in xs:
   #        for topic in x.get('topicList'):
   #           update_TopicTree(topic,x.get('topicList').get(topic))
   #

   alltopics = []
   for type in typs:
       xs=UserData.find({'type':type},{'title':True,'topicList':True,'_id':True})
       afterKE = {}
       for x in xs:
        ######## Step 1 Matching possibility ############
           #### split the sentence###
           cutarray = []
           words = pseg.cut(x.get('title'))
           for word, flag in words:
           # print('%s %s' % (word,flag))
             if (flag == 'n') | (flag == 'eng') | (flag == 'nr') | (flag == 'ns') | (flag == 'nt') | (flag == 'nz') | (flag == 'vn') | (flag == 'an'):
                 cutarray.append(word)
           #### match
           for topicone in x.get('topicList').keys():
               _id = x.get('_id')
               if topicone not in afterKE.keys():
                   afterKE.update({topicone:x.get('topicList').get(topicone)})#Collect all the distinct topics from current user
               if topicone not in alltopics:
                   alltopics.append(topicone)
               topicName = 'topicList.'
               topicname = topicName+topicone
               id = x.get('topicList').get(topicone)
               field = {'topicid' :id}
               if (topicone in cutarray):
                   field.update({'rate':1})
                   UserData.update({'_id':_id},{"$set":{topicname:field}})
               else:
                   field.update({'rate':0.5})
                   UserData.update({'_id': _id}, {"$set": {topicname: field}})
        ######################################################################


       keyExtract1 = {}
       
        ###### Step 2 Average possibility #################
       print('1111',afterKE)
       for topic_in_type in afterKE.keys():
         topicName = 'topicList.'
         topicID = topicName+topic_in_type+'.topicid'
         topicrate = topicName+topic_in_type+'.rate'
         topicid = afterKE.get(topic_in_type)

         all_topic_in_type = UserData.find({'type':type,topicID:topicid},{topicrate:True})
         sum_topic_in_type =all_topic_in_type.count()
         sum = UserData.find({'type':'Answer','origin':1}).count()
         rate_count = sum_topic_in_type/sum
         rate = 0
         counter = 0
         for rateone in all_topic_in_type:
             counter +=1
             rate = rate + rateone.get('topicList').get(topic_in_type).get('rate')
         rate = rate/counter
         topicnew = {'type':type,'rate':rate*rate_count,'topicName':topic_in_type}
         UserData.insert(topicnew)
        ######################################################################



        ###### Step 3 Average possibility with weight #####
   for topicone in alltopics:
       rate_A=0
       rate_Q=0
       rate_QF =0
       a=UserData.find_one({'topicName':topicone,'type':'Answer'},{'rate':True})
       q=UserData.find_one({'topicName':topicone,'type':'Question'},{'rate':True})
       qf=UserData.find_one({'topicName':topicone,'type':'QF'},{'rate':True})
       if(a):
          rate_A =a.get('rate')
       if(q):
          rate_Q = q.get('rate')
       if(qf):
          rate_QF = qf.get('rate')
       rate = (1.5*rate_A+rate_Q+rate_QF)/4.5
       UserData.insert({'topicName':topicone,'afterkEx':1,'rate':rate})
       ######################################################################


       
       #### Step 4 Final possibility####
   alltopicsfromuser=[]
   ALLTOPICSFROMUSERS = UserData.find({'type':'Topic'})

   if(ALLTOPICSFROMUSERS):
    for each in ALLTOPICSFROMUSERS:
        for eachone in each.get('topicList').keys():
            alltopicsfromuser.append(eachone)
    for topicone in alltopics:
       rate = UserData.find_one({'topicName':topicone,'afterkEx':1},{'rate':True}).get('rate')
       if (topicone in alltopicsfromuser):
           if(rate<0.5):
               rate = (rate+0.5)/2
               UserData.update({'topicName':topicone,'afterkEx':1},{"$set":{'rate':rate}})
       else:
           if(rate>0.5):
               rate = (rate+0.5)/2
               UserData.update({'topicName':topicone,'afterkEx':1},{"$set":{'rate':rate}})
      ######################################################################


if __name__ == '__main__':
    main()
    