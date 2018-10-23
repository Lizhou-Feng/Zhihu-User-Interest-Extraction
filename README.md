# Zhihu-User-Interest-Extraction

Project for undergraduate thesis (Communication University of China, Department of Computer Science, B.E Information Security)

# Project description
Raw data was collected from a China Q&A social networking website called "***ZHIHU***".
The raw data includes “***Answers***”, “***Questions***”, “***Following Questions***”, and “***Following Topics***” fields related to users. 
The goal of this project is to ***identify user interests*** from their raw data.

There are mainly three modules in the system: User Data Acquisition, Corpus Construction, and User Interest Extraction. 
* User Data Acquisition  \
  For collecting the ***raw data*** from server and parsing them to ***structured data***.
          
* Corpus Construction \
  For building the ***TopicTree***, which will be used in Interest-clustering in ***Interest Extraction*** module.
  
* User Interest Extraction \
  For ***clustering*** all the possible interests (topics) and ***calculating*** the possibility of each topic. The higher the possibility is, the more possible users are interested in the topic.
