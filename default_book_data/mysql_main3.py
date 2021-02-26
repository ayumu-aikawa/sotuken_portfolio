import mysql.connector as mydb
import json

#DBの設定
conn = mydb.connect(
  database = 'sotu_test',
  user='root',
  password = 'P@ssw0rd',
  host = 'localhost',
  port = '3306',
)


# 接続できているかどうか確認
print(conn.is_connected())

cur = conn.cursor(buffered=True)
#大分類
cat_data = json.load(open('./isbn_data/category_data/category_list2.json','r',encoding='utf-8'))
for i in range(len(cat_data)):
  cur.execute("INSERT INTO `sotuken_bigcategory` (`bigcat`, `catname`) VALUES (%(num)s, %(name)s);",{'num':cat_data[i]["大分類番号"],'name':cat_data[i]["大分類名"],},)

cur.close()
conn.commit()