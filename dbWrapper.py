import psycopg2
import pandas as pd

exec(open('/home/dale/local_news/db.cred').read())
                        
class dbWrapper:
    
    def __init__(self):
        self.conn = psycopg2.connect(
        "dbname='{dbname}' user='{user}' host='{host}' password='{password}'".format(
        **creds))
        self.cur = self.conn.cursor()
    
    def execute(self, query, params=None):
        
        try:
            self.cur.execute(query, params)
            self.conn.commit()
        except Exception as err:
            print("Err: %s" % str(err))
            self.conn.rollback()
            return
            
        try:
            res = self.cur.fetchall()
            colnames = [desc[0] for desc in self.cur.description]
            return pd.DataFrame(res, columns=colnames)
        except:
            return None
