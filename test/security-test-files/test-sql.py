# SECURITY TEST FILE - HIGH-RISK VIOLATIONS
# This file contains intentional security violations for testing Security Agent detection

import sqlite3
import mysql.connector
import psycopg2
import pymongo

# High-risk violations - SQL injection patterns
def get_user_by_id(user_id):
    """SQL injection vulnerability - direct string concatenation"""
    query = "SELECT * FROM users WHERE id = " + user_id
    cursor.execute(query)
    return cursor.fetchone()

def search_users(name):
    """SQL injection vulnerability - f-string interpolation"""
    query = f"SELECT * FROM users WHERE name = '{name}'"
    cursor.execute(query)
    return cursor.fetchall()

def get_user_by_email(email):
    """SQL injection vulnerability - % formatting"""
    query = "SELECT * FROM users WHERE email = '%s'" % email
    cursor.execute(query)
    return cursor.fetchone()

def login_user(username, password):
    """SQL injection vulnerability - format method"""
    query = "SELECT * FROM users WHERE username = '{}' AND password = '{}'".format(username, password)
    cursor.execute(query)
    return cursor.fetchone()

# Dynamic query construction
def search_products(category, price_min, price_max):
    """SQL injection vulnerability - dynamic query building"""
    query = "SELECT * FROM products WHERE 1=1"
    if category:
        query += " AND category = '" + category + "'"
    if price_min:
        query += " AND price >= " + str(price_min)
    if price_max:
        query += " AND price <= " + str(price_max)
    cursor.execute(query)
    return cursor.fetchall()

# Raw SQL execution
def execute_raw_query(table, condition):
    """SQL injection vulnerability - raw query execution"""
    query = f"DELETE FROM {table} WHERE {condition}"
    cursor.execute(query)
    return cursor.rowcount

# NoSQL injection patterns
def find_user_mongo(username):
    """NoSQL injection vulnerability - MongoDB"""
    collection.find({"username": username})

def authenticate_mongo(username, password):
    """NoSQL injection vulnerability - MongoDB authentication"""
    return collection.find_one({"$where": f"this.username == '{username}' && this.password == '{password}'"})

# LDAP injection patterns
def ldap_search(username):
    """LDAP injection vulnerability"""
    filter_str = f"(uid={username})"
    return ldap_connection.search_s(base_dn, ldap.SCOPE_SUBTREE, filter_str)

# Command injection patterns
import os
import subprocess

def ping_host(hostname):
    """Command injection vulnerability - os.system"""
    command = f"ping -c 4 {hostname}"
    os.system(command)

def check_file(filename):
    """Command injection vulnerability - subprocess with shell=True"""
    command = f"ls -la {filename}"
    subprocess.run(command, shell=True)

def process_file(filename):
    """Command injection vulnerability - direct execution"""
    os.popen(f"cat {filename}").read()

# Path traversal vulnerabilities
def read_file(filename):
    """Path traversal vulnerability"""
    with open(f"/var/www/uploads/{filename}", 'r') as f:
        return f.read()

def serve_file(path):
    """Path traversal vulnerability"""
    file_path = f"/app/static/{path}"
    with open(file_path, 'rb') as f:
        return f.read()

# XML external entity (XXE) patterns
import xml.etree.ElementTree as ET

def parse_xml(xml_content):
    """XXE vulnerability - unsafe XML parsing"""
    return ET.fromstring(xml_content)

# Unsafe deserialization
import pickle
import yaml

def load_data(data):
    """Unsafe deserialization - pickle"""
    return pickle.loads(data)

def load_config(config_data):
    """Unsafe deserialization - YAML"""
    return yaml.load(config_data)

# Server-side template injection
def render_template(template_string, user_input):
    """SSTI vulnerability - Jinja2"""
    from jinja2 import Template
    template = Template(template_string)
    return template.render(user_input=user_input)

# Cross-site scripting (XSS) patterns
def render_user_content(content):
    """XSS vulnerability - unescaped content"""
    return f"<div>User says: {content}</div>"

def search_results(query):
    """XSS vulnerability - reflected XSS"""
    return f"<h1>Search results for: {query}</h1>"

# Insecure file upload patterns
def upload_file(file_content, filename):
    """Insecure file upload - no validation"""
    file_path = f"/var/www/uploads/{filename}"
    with open(file_path, 'wb') as f:
        f.write(file_content)
    return file_path

# Information disclosure
def get_database_error():
    """Information disclosure - database error exposure"""
    try:
        cursor.execute("SELECT * FROM non_existent_table")
    except Exception as e:
        return str(e)  # Exposes database structure

# Insecure direct object reference
def get_user_profile(user_id):
    """IDOR vulnerability - no authorization check"""
    query = "SELECT * FROM user_profiles WHERE user_id = %s"
    cursor.execute(query, (user_id,))
    return cursor.fetchone()

# Race condition vulnerabilities
import threading

balance = 1000
lock = threading.Lock()

def withdraw_money(amount):
    """Race condition vulnerability - no proper locking"""
    global balance
    if balance >= amount:
        # Vulnerable: balance check and update not atomic
        balance -= amount
        return True
    return False

# Time-based vulnerabilities
import time

def check_password(input_password, stored_password):
    """Timing attack vulnerability - non-constant time comparison"""
    if len(input_password) != len(stored_password):
        return False
    
    for i in range(len(input_password)):
        if input_password[i] != stored_password[i]:
            return False
        time.sleep(0.01)  # Simulates processing time
    
    return True

# Insecure cryptographic storage
def store_password(password):
    """Insecure password storage - plain text"""
    with open('passwords.txt', 'a') as f:
        f.write(f"{password}\n")

# Examples of vulnerable database connections
def connect_to_database():
    """Multiple connection vulnerabilities"""
    # Connection string with embedded credentials
    conn_string = "postgresql://admin:password123@localhost/mydb"
    
    # Insecure connection options
    conn = psycopg2.connect(
        host="localhost",
        database="mydb",
        user="admin",
        password="password123",
        sslmode="disable"  # Insecure: disables SSL
    )
    
    return conn

# Mass assignment vulnerability
def update_user_profile(user_id, form_data):
    """Mass assignment vulnerability - no field filtering"""
    fields = []
    values = []
    for key, value in form_data.items():
        fields.append(f"{key} = %s")
        values.append(value)
    
    query = f"UPDATE users SET {', '.join(fields)} WHERE id = %s"
    values.append(user_id)
    cursor.execute(query, values)

# Export vulnerable functions
__all__ = [
    'get_user_by_id',
    'search_users',
    'login_user',
    'execute_raw_query',
    'ping_host',
    'read_file',
    'parse_xml',
    'load_data',
    'render_template',
    'upload_file',
    'withdraw_money',
    'check_password',
    'store_password'
]