# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.6.0
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %%
from github import Github
import sqlite3
import os
import pandas as pd
from tqdm import trange, tqdm
from datetime import datetime
import subprocess
import ast

from ast import (
    AsyncFunctionDef, FunctionDef, 
    ClassDef, Module
)


# %% [markdown]
# # Create the tables

# %%
def create_tables():
    from sqlalchemy import (
        Table, Column, Integer, String, MetaData, Float, 
        create_engine, ForeignKey
    )
    
    # Create a connection to our SQLite database
    sqlite_path = '///' + os.path.abspath('../data/repositories.sqlite')
    engine = create_engine(f'sqlite:{sqlite_path}', echo = True)
    meta = MetaData()
    meta.bind = engine

    repo_table = Table(
        'repositories', meta, 
        Column('id', Integer, primary_key = True, autoincrement=True), 
        Column('name', String),
        Column('url', String),
        Column('found_at', Integer),
        Column('license', String)
    )

    status_table = Table(
        'clone_status', meta,
        Column('id', Integer, primary_key = True, autoincrement=True),
        Column('repo_id', Integer, ForeignKey("repositories.id"), nullable=False),
        Column('cloned_at', Integer),
        Column('md5sum', String)
    )

    repo_table.metadata.create_all(engine)
    status_table.metadata.create_all(engine)
    
# create_tables()


# %%
con = sqlite3.connect('../data/repositories.sqlite')

# %%
# Create a Github object using an access token
with open('../_tokens/gihub_read_token') as f:
    # or using an access token
    g = Github(f.readline().strip())

# %%
license = 'apache-2.0'
search_pages = g.search_repositories(f'python language:python license:{license}', 
                                     sort='stars', order='desc')

n_repos = pd.read_sql("SELECT count(*) as count FROM repositories", con)
start_page = round(n_repos.values[0][0] / 30) 

if False:
    for i in trange(start_page, 1001):
        res = search_pages.get_page(i)
        
        timestamp_now = round(datetime.now().timestamp())

        df_repos = pd.DataFrame(
            [(repo.name, repo.clone_url, timestamp_now, license) for repo in res], 
            columns=['name', 'url', 'found_at', 'license']
        )
        df_repos.to_sql('repositories', con, if_exists='append', index=False)

# %% [markdown]
# # Shallow clone repos

# %%
df_repos = pd.read_sql("SELECT * FROM repositories", con, index_col='id')


# %%
for i, row in df_repos.iterrows():
    new_folder = '|'.join(row['url'].split('/')[-2:])[:-4]
    if not os.path.isdir(f'../data/repos/{new_folder}'):
        get_ipython().system("git clone --depth 1 {row['url']} '../data/repos/{new_folder}'")

# %% [markdown]
# # Get all .py files

# %%
# %%time
if True:
    py_files = []
    for root, dirs, files in tqdm(os.walk('../data/repos')):
        for file in files:
            if file.endswith(".py"):
                 py_files.append(os.path.join(root, file))
else:
    pass

# %%
py_files[1]

# %%
fname = py_files[1]

with open(fname, 'r') as f:
    tree = ast.parse(f.read())
ast.get_docstring(tree)


# %%
def get_functions(tree, functions):
#     print(type(tree))
    if isinstance(tree, (AsyncFunctionDef, FunctionDef, 
                         ClassDef, Module)):
        if isinstance(tree, (AsyncFunctionDef, FunctionDef)):
            if ast.get_docstring(tree) is not None:
                functions.append(tree)
        for node in tree.body:
            get_functions(node, functions)
    return functions


# %%
with open(fname, 'r') as f:
    tree = ast.parse(f.read())

# %%
functions = []
get_functions(tree, functions)

# %%
[_.name for _ in functions]

# %%
total_lines = 0
for f in tqdm(py_files):
    n_lines = !wc -l '{f}'
    total_lines += int(n_lines[0].split(' ', 1)[0])

# %%
total_lines

# %%
