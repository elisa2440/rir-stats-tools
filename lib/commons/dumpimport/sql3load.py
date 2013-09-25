'''
Created on Sep 18, 2013

@author: marcelo
'''

import sqlite3
import commons.statkeeper

class Sql3Load(object):
    '''
    This class implements a generic delimited text file importer into an sqlite3 backend. Allos for limited querying.
    '''
    
    ### begin
    def __init__(self, w_record_tpl, w_file_name = None):
        self.table_name = "imported_data"
        '''
        Default constructor
        :param w_record_tpl : record template, a dictionary with the format {'col name': 'col type'} where
                                col_type is a valid sqlite3 type.
        :param w_file_name  : file name for the database. If None the database will be created in RAM.
        '''
        #
        self.record_tpl = w_record_tpl
        #
        try:
            if w_file_name:
                self.conn = sqlite3.connect(w_file_name)
            else:
                self.conn = sqlite3.connect(':memory:')
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()
            # self.cursor.execute(''' CREATE TABLE roapfx (uri text, origin_as text, prefix text, max_len int,  ''' + 
            #                    ''' valid_from text, valid_until text, istart unsigned big int, iend unsigned big int) ''')
            self.cursor.execute(" CREATE TABLE %s (id INTEGER PRIMARY KEY)" % (self.table_name) )
            
            # loop and add columns
            for col_name in w_record_tpl.keys():
                sql = "ALTER TABLE %s ADD COLUMN %s %s" % (self.table_name, col_name, w_record_tpl[col_name])
                self.cursor.execute(sql)
            
            self.conn.commit()
        except:
            raise
    ### end
    
    ## begin
    def _insert_row(self, w_record):
        r = False
        try:
            sql = "INSERT INTO %s VALUES (1, 'marce', 10, 11.0)" % (self.table_name)
            self.cursor.execute(sql)
            self.conn.commit()
            r = True
        except:
            raise
        return r
    ## end
    
    ## begin
    def get_rowcount(self):
        sql = "SELECT count(*) AS CNT FROM %s" % (self.table_name)
        r1 = self.cursor.execute(sql)
        row = r1.fetchone()
        return dict(row)
    ## end
    
    ## begin
    def csv_read(self, w_file_name):
        pass
    ## end
    
    ## begin
    def query(self, w_query, w_parameters = {}):
        """
        Runs an arbitrary SQL query against the in-memory database.
        
        :param w_query: the query itself (what comes after the WHERE SQL keyword) using named parameters for column values, as in:
                        'origin_as=:oas'
                        
        :param w_parameters: an associative array with parameter values. Must be consistent with the names used for wquery, as in:
                            {'oas': '28000'}
        """
        sql = "SELECT * FROM %s WHERE %s" % (self.table_name, w_query)
        try:
            qr = self.cursor.execute(sql, w_parameters)
            ar = []
            for x in qr:
                ar.append(dict(x))
            return ar
        except sqlite3.Error as e:
            raise
            return None
        except:
            raise
    ## end
    
    
## end class Sql3Load

