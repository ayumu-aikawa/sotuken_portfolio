import mysql.connector as mydb
import json
import datetime

#DBの設定
conn = mydb.connect(
  database = 'sotu_test',
  user='root',
  password = '',
  host = 'localhost',
  port = '3306',
)


# 接続できているかどうか確認
print(conn.is_connected())

cur = conn.cursor(buffered=True)
print("input of number")
num = input()

for i in range(num):
  dt_now = datetime.datetime.now()
  cur.execute("INSERT INTO `sotuken_lendhistory` (`id`, `accountid`, `opeaccountid`, `smallcat`, `lenddate`, `lendtype`) VALUES (NULL,%(a)s,%(b)s,%(c)s,%(d)s,%(e)s);",{'a':1,'b':1,'c':3,'d':dt_now,'e':0})

cur.close()
conn.commit()