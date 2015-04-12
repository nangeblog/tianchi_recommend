# -*- coding: utf-8 -*- 

import mysql.connector
import datetime
from sklearn import cross_validation
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier


def computePrecisionAndRecall(fpname, frname):
	predicttionset = dict()
	referenceset = dict()
	with open(fpname, "r") as f:
		for row in f.readlines():
			row = row.strip().split(',')
			key = row[0]+"_"+row[1]
			if int(row[2]) == 1 and key not in predicttionset:
				predicttionset[key] = 1

	predinterectref = 0.0
	with open(frname, "r") as f:
		for row in f.readlines():
			row = row.strip().split(',')
			key = row[0]+"_"+row[1]
			if int(row[2]) == 1 and key not in referenceset:
				referenceset[key] = 1
				if key in predicttionset:
					predinterectref += 1

	prednum = float(len(predicttionset))
	refnum = float(len(referenceset))

	print "prediction set num: "+str(prednum)
	print "reference set num: "+str(refnum)
	print "interact num: "+str(predinterectref)
	precision = predinterectref / prednum
	recall = predinterectref / refnum
	print "precision is: " + str(precision)
	print "recall is: " + str(recall)
	f1 = (2*precision*recall) / (precision+recall)
	print "f1 is: " + str(f1)


def genFeature(user, item, end_date, timelist, cursor):
	feat = list()
	behlist = [1,2,3,4]
	#生成用户特征
	query = ("SELECT count(id),count(distinct itemid) FROM trainuser_sample "
         "WHERE userid=%s and behavior=%s and pytime between %s and %s")
	useraction = dict()
	for num, t in enumerate(timelist):
		#itemnum表示用户购买、浏览、购物车和收藏的总数
		#diifitemnum表示用户购买、浏览等不同品牌总数
		itemnum=[0,0,0,0];diffitemnum=[0,0,0,0]
		for b in behlist:
			data = (user, b, t, end_date)
			cursor.execute(query, data)
			rs = cursor.fetchall()
			itemnum[b-1] = rs[0][0]; diffitemnum[b-1] = rs[0][1]
		useraction[num] = itemnum
		feat.extend(itemnum)
		feat.extend(diffitemnum)
		#用户购买数/用户浏览数
		if itemnum[0] == 0:
			feat.append(0)
		else:
			b_c = float(itemnum[3]) / itemnum[0]
			feat.append(b_c)
		#用户购买的品牌数/用户浏览的品牌数
		if diffitemnum[0] == 0:
			feat.append(0)
		else:
			bb_cb = float(diffitemnum[3]) / diffitemnum[0]
			feat.append(bb_cb)
	
	#生成品牌特征
	itemaction = dict()
	query = ("SELECT count(id),count(distinct userid) FROM trainuser_sample "
         "WHERE itemid=%s and behavior=%s and pytime between %s and %s")
	for num, t in enumerate(timelist):
		#itemnum表示品牌购买（等）数量
		#diffitemnum表示购买（等）该品牌的人数	
		itemnum=[0,0,0,0];diffitemnum=[0,0,0,0]
		for b in behlist:
			data = (item, b, t, end_date)
			cursor.execute(query, data)
			rs = cursor.fetchall()
			itemnum[b-1] = rs[0][0]; diffitemnum[b-1] = rs[0][1]
		itemaction[num] = itemnum
		feat.extend(itemnum)
		feat.extend(diffitemnum)
		#销量（购物车、收藏）/浏览量
		if itemnum[0] == 0:
			feat.extend([0,0,0])
		else:
			for c in [1,2,3]:
				temp = float(itemnum[c]) / itemnum[0]
				feat.append(temp)
		#购买人数（购物车人数、收藏人数）/浏览人数
		if diffitemnum[0] == 0:
			feat.extend([0,0,0])
		else:
			for c in [1,2,3]:
				temp = float(diffitemnum[3]) / diffitemnum[0]
				feat.append(temp)
	
	#生成用户-品牌特征
	query = ("SELECT count(id) FROM trainuser_sample "
         "WHERE userid=%s and itemid=%s and behavior=%s and pytime between %s and %s ")
	useritemaction = dict()
	for num, t in enumerate(timelist):
		#itemnum表示用户购买（等）品牌数量
		itemnum=[0,0,0,0]
		for b in behlist:
			data = (user, item, b, t, end_date)
			cursor.execute(query, data)
			rs = cursor.fetchall()
			itemnum[b-1] = rs[0][0]
		useritemaction[num] = itemnum
	#截止到最后一天用户购买（添加购物车、浏览、收藏）该物品的数量
	templist = useritemaction[4]
	feat.extend(templist)
	for num, t in enumerate(timelist):
		#用户购买该品牌的次数/用户总购买次数
		if useraction[num][3] == 0:
			feat.append(0)
		else:
			feat.append(float(useritemaction[num][3])/useraction[num][3])
		#用户点击、购买、添加购物车、收藏该物品的次数/用户总访问次数
		if useraction[num][0] == 0:
			feat.append(0)
		else:
			feat.append(float(useritemaction[num][0])/useraction[num][0])
			feat.append(float(useritemaction[num][1])/useraction[num][0])
			feat.append(float(useritemaction[num][2])/useraction[num][0])
			feat.append(float(useritemaction[num][3])/useraction[num][0])
	
	return feat


def genFeatureFromFile(user, item, end_date, timelist, cursor):
	feat = list()
	behlist = [1,2,3,4]
	
	#生成用户-品牌特征
	query = ("SELECT count(id) FROM trainuser_sample "
         "WHERE userid=%s and itemid=%s and behavior=%s and pytime between %s and %s ")
	useritemaction = dict()
	for num, t in enumerate(timelist):
		#itemnum表示用户购买（等）品牌数量
		itemnum=[0,0,0,0]
		for b in behlist:
			data = (user, item, b, t, end_date)
			cursor.execute(query, data)
			rs = cursor.fetchall()
			itemnum[b-1] = rs[0][0]
		useritemaction[num] = itemnum
	#截止到最后一天用户购买（添加购物车、浏览、收藏）该物品的数量
	templist = useritemaction[4]
	feat.extend(templist)
	
	return feat, useritemaction

def trainModelFromFile(train=True):
	print "begin gen train data"
	end_date = datetime.date(2014, 12, 18)
	filename = ""
	if train:
		filename = "train_data.csv"
	else:
		filename = "offline_train_data.csv"
		end_date = datetime.date(2014, 12, 17)
	X_train = list()
	y_train = list()
	timelist = list()
	time_to_subtract = [1,3,7,15,30]
	for t in time_to_subtract:
		temp_date = end_date - datetime.timedelta(days=t)
		timelist.append(temp_date)
	
	cnx = mysql.connector.connect(user='root', password='1234', database='tianchi')
	cursor = cnx.cursor()

	userfeat = dict()
	print "begin user feature"
	with open("userfeature_offline.csv", "r") as f:
		for row in f.readlines():
			row = row.strip().split(',')
			userfeat[row[0]] = [float(u) for u in row[1:]]
	print "end user feature"
	itemfeat = dict()
	print "begin item feature"
	with open("itemfeature_offline.csv", "r") as f:
		for row in f.readlines():
			row = row.strip().split(',')
			itemfeat[row[0]] = [float(i) for i in row[1:]]
	print "end item feature"
	print "begin train data"
	number = 0
	with open(filename, "r") as f:
		for row in f.readlines():
			feat = list()
			if number % 1000 == 0:
				print number
			number += 1
			row = row.strip().split(',')
			user = row[0];item = row[1]
			posorneg = int(row[2])

			feat.extend(userfeat[user])
			feat.extend(itemfeat[item])
			useritemfeat, useritemaction = genFeatureFromFile(user, item, end_date, timelist, cursor)
			feat.extend(useritemfeat)
			tempaddnum = 10
			userindex_1 = -7; userindex_2 = -10
			for num, t in enumerate(timelist):
				userindex_1 = userindex_1 + tempaddnum
				#用户购买该品牌的次数/用户总购买次数
				if userfeat[user][userindex_1] == 0:
					feat.append(0)
				else:
					feat.append(float(useritemaction[num][3])/userfeat[user][userindex_1])
				userindex_2 = userindex_2 + tempaddnum
				#用户点击、购买、添加购物车、收藏该物品的次数/用户总访问次数
				tempnum = userfeat[user][userindex_2]
				if tempnum == 0:
					feat.extend([0,0,0,0])
				else:
					feat.append(float(useritemaction[num][0])/tempnum)
					feat.append(float(useritemaction[num][1])/tempnum)
					feat.append(float(useritemaction[num][2])/tempnum)
					feat.append(float(useritemaction[num][3])/tempnum)
			X_train.append(feat)
			if posorneg == 4:
				y_train.append(1)
			else:
				y_train.append(0)
	print "end gen train data"
	
	print "begin train model"
	#clf = LogisticRegression()
	clf = RandomForestClassifier(max_depth=10, n_estimators=100)
	clf = clf.fit(X_train, y_train)
	print "end train model"

	fwname = ""
	frname = ""
	if train:
		#online no need to offlien test
		fwname = "online_predict_data.txt"
		frname = "online_tobepredicted_data.csv"
	else:
		#offline test
		fwname = "offline_predict_data.txt"
		frname = "offline_test_data.csv"

	print "begin predict"
	with open(fwname, "w") as fw:
		with open(frname, "r") as f:
			number = 0
			for row in f.readlines():
				feat = list()
				if number % 1000 == 0:
					print number
				number += 1
				row = row.strip().split(',')
				user = row[0];item = row[1]

				feat.extend(userfeat[user])
				feat.extend(itemfeat[item])
				useritemfeat, useritemaction = genFeatureFromFile(row[0],row[1],end_date,timelist,cursor)
				feat.extend(useritemfeat)
				tempaddnum = 10
				userindex_1 = -7; userindex_2 = -10
				for num, t in enumerate(timelist):
					userindex_1 = userindex_1 + tempaddnum
					#用户购买该品牌的次数/用户总购买次数
					if userfeat[user][userindex_1] == 0:
						feat.append(0)
					else:
						feat.append(float(useritemaction[num][3])/userfeat[user][userindex_1])
					userindex_2 = userindex_2 + tempaddnum
					#用户点击、购买、添加购物车、收藏该物品的次数/用户总访问次数
					tempnum = userfeat[user][userindex_2]
					if tempnum == 0:
						feat.extend([0,0,0,0])
					else:
						feat.append(float(useritemaction[num][0])/tempnum)
						feat.append(float(useritemaction[num][1])/tempnum)
						feat.append(float(useritemaction[num][2])/tempnum)
						feat.append(float(useritemaction[num][3])/tempnum)				
				pred_label = clf.predict(feat)[0]
				'''
				pred_pos = clf.predict_proba(testlist)[:,1]
				pred_label = 1
				if pred_pos < 0.7:
					pred_label = 0
				'''
				fw.write(row[0]+","+row[1]+","+str(pred_label)+"\n")
	print "end predict"
	cursor.close()
	cnx.close()
	if not train:
		computePrecisionAndRecall("offline_predict_data.txt", "offline_test_data.csv")

def predictDataToSubmitData():
	with open("tianchi_mobile_recommendation_predict.csv", "w") as fw:
		fw.write("user_id,item_id\n")
		with open("online_predict_data.txt", "r") as f:
			for row in f.readlines():
				line = row.strip().split(',')
				if int(line[2]) == 1:
					fw.write(line[0]+","+line[1]+"\n")

if __name__ == "__main__":
	train = False
	trainModelFromFile(train)
	if train:
		predictDataToSubmitData()

	#computePrecisionAndRecall("offline_predict_data.txt", "offline_test_data.csv")
	#createItemFeatureToFile(False)