import mysql.connector as mydb
import sys
import pandas as pd
from MyDatabase import my_query, my_open, my_close
import datetime

auth = {
    'host' : 'localhost',  
    'port' : '3306',        
    'user' : 'root',        
    'password' : '1234',    
    'database' : 'dbtest01' 
}

dbcon,cur = my_open( **auth )

my_close(dbcon,cur)
