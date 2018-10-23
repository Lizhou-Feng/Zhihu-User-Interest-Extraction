from pymongo import MongoClient
import pymongo.errors as mongoerr

def ConnetDB():
    try:
        client = MongoClient('localhost:27017', connect=True)
        dbTopicTree = client.topicTree
        Tree = dbTopicTree.TopicTree
        dbUser = client.UserData
        UserData = dbUser.chenqin
        return Tree,UserData

    except mongoerr.ConnectionFailure as  e:
        print("Could not connect: %s" % e)
        return 1

Tree,UserData= ConnetDB()
user= 'chenqin'
userTag = user+'.Tag'
userValue = user+'.Value'
parentAlready = user + '.already'

Orinodes=[]
ns = UserData.find({'afterkEx':1})
for n in ns:
    Orinodes.append(n.get('topicName'))

def downsub(node):
        print('3',node)
        children = Tree.find({'parents': node})

        for child in children:
            if (not Tree.find_one({'topicName': child.get('topicName'),userTag:1})):  # the child-node has not been marked yet
                if (child.get('topicName') in Orinodes):
                    ori(child.get('topicName'))
                else:
                    down(child.get('topicName'))
            else:
                pass
        Children = Tree.find({'parents': node})
        childrenCount = Children.count()
        valueChildren = 0
        for child in Children:
            valueChildren += child.get(user).get('Value')
        valueChildren = valueChildren / childrenCount
        return valueChildren

def down(node):
    print('2',node)
    if (Tree.find_one({'parents': node})):  # non-leaf
        valueChildren = downsub(node)
        Tree.update({'topicName': node}, {"$set": {userValue: valueChildren, userTag: 1}})
    else:
        Tree.update({'topicName': node}, {"$set": {userValue: 0, userTag: 1}})

def ori(node):
    print('1',node)
    if (not Tree.find_one({'topicName':node,userTag:'1'})):#if node.Tag==0
      if(not Tree.find_one({'parents':node})):#leaf
          value = UserData.find_one({'topicName':node,'afterkEx':1}).get('rate')
          Tree.update({'topicName':node},{"$set":{userValue:value,userTag:1}})
      else:
          valueChildren = downsub(node)
          value_ori = UserData.find_one({'topicName':node,'afterkEx':1}).get('rate')
          if(value_ori<valueChildren):
              value = valueChildren
          else:
              value = value_ori

          Tree.update({'topicName':node},{"$set":{userValue:value,userTag:1}})


      if(Tree.find_one({'topicName':node,'parents':True})):
        parents = Tree.find_one({'topicName':node}).get('parents')
        for parent in parents:
          if(not Tree.find_one({'topicName': parent, parentAlready: '1'})):#parent node has not been found yet
              Tree.update({'topicName': parent},{"$set":{ parentAlready: '1'}})
              if parent in Orinodes:
                  ori(parent)
              else:
                  down(parent)
          else:
              pass
      else:
          pass
    else:
          pass


def main():
    # for topic_original in  Orinodes:
    #      ori(topic_original )
    topics = Tree.find({userTag:1}).sort(userValue)
    for topic in topics:
        if(topic.get(user).get('Value')!=0):
          print(topic.get('topicName'),topic.get(user).get('Value'))
        else:
            pass

if __name__ == '__main__':
    main()
    